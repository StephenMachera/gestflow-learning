# ==========================================
# GESTFLOW PEER MANAGER
# ==========================================
# Single responsibility:
#   → Keep a live list of all GestFlow peers
#   → Add peers when discovered
#   → Remove peers when they go offline
#   → Provide peer selection for transfers

# ==========================================

import time
import json
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_03_state_capture.device_info import get_device_info

# ── How long before a peer is considered offline ──
PEER_TIMEOUT_SECONDS = 30


# ══════════════════════════════════════════
# PEER STORAGE
# ══════════════════════════════════════════

# Thread-safe peer storage
# Key: peer ID
# Value: peer info dict
_peers      = {}
_peers_lock = threading.Lock()


# ══════════════════════════════════════════
# PEER MANAGEMENT
# ══════════════════════════════════════════

def add_peer(peer_info):
    """
    Adds or updates a peer in the list.
    Called by discovery.py when a new device is found.

    peer_info must contain at minimum:
      id, name, ip, port
    """
    if not peer_info:
        return

    peer_id = peer_info.get('id')
    if not peer_id:
        return

    # Never add ourselves to the peer list
    my_info = get_device_info()
    if peer_id == my_info.get('id'):
        return

    with _peers_lock:
        _peers[peer_id] = {
            'id'      : peer_id,
            'name'    : peer_info.get('name', 'Unknown Device'),
            'ip'      : peer_info.get('ip'),
            'port'    : peer_info.get('port', 9000),
            'os'      : peer_info.get('os', 'Unknown'),
            'version' : peer_info.get('version', '1.0'),
            'lastSeen': time.time(),
            'online'  : True
        }

    print(f"👥 Peer discovered: {peer_info.get('name')} "
          f"({peer_info.get('ip')})")
    print(f"   Total peers: {get_peer_count()}")


def remove_peer(peer_id):
    """
    Removes a peer from the list.
    Called by discovery.py when a device goes offline.
    """
    with _peers_lock:
        peer = _peers.pop(peer_id, None)

    if peer:
        print(f"👥 Peer left: {peer.get('name')} ({peer.get('ip')})")
        print(f"   Remaining peers: {get_peer_count()}")


def update_peer_last_seen(peer_id):
    """
    Updates the last seen timestamp for a peer.
    Called when we receive any message from a peer.
    Keeps peer marked as online.
    """
    with _peers_lock:
        if peer_id in _peers:
            _peers[peer_id]['lastSeen'] = time.time()
            _peers[peer_id]['online']   = True


def mark_peer_offline(peer_id):
    """
    Marks a peer as offline without removing it.
    Used when ping fails but we are not sure they left.
    """
    with _peers_lock:
        if peer_id in _peers:
            _peers[peer_id]['online'] = False
            print(f"⚠️  Peer offline: {_peers[peer_id].get('name')}")


# ══════════════════════════════════════════
# PEER QUERIES
# ══════════════════════════════════════════

def get_all_peers():
    """
    Returns all known peers regardless of online status.
    """
    with _peers_lock:
        return list(_peers.values())


def get_online_peers():
    """
    Returns only peers that are currently online.
    These are valid targets for content transfer.
    """
    with _peers_lock:
        return [
            peer for peer in _peers.values()
            if peer.get('online', False)
        ]


def get_peer_by_id(peer_id):
    """Returns a specific peer by their device ID."""
    with _peers_lock:
        return _peers.get(peer_id)


def get_peer_by_ip(ip):
    """Returns a peer by their IP address."""
    with _peers_lock:
        for peer in _peers.values():
            if peer.get('ip') == ip:
                return peer
    return None


def get_peer_count():
    """Returns total number of known peers."""
    with _peers_lock:
        return len(_peers)


def get_online_peer_count():
    """Returns number of online peers."""
    with _peers_lock:
        return sum(
            1 for p in _peers.values()
            if p.get('online', False)
        )


def has_peers():
    """Returns True if at least one peer is online."""
    return get_online_peer_count() > 0


# ══════════════════════════════════════════
# PEER SELECTION
# Used when gesture is detected to pick target
# ══════════════════════════════════════════

def get_target_peer(direction=None):
    """
    Selects the best target peer for a transfer.

    direction: gesture direction hint
      'right' → prefer peer to the right (future feature)
      'left'  → prefer peer to the left (future feature)
      None    → pick first available peer

    For v1 — returns first online peer.
    Future versions will use gesture direction
    and peer physical location.
    """
    online = get_online_peers()

    if not online:
        return None

    # v1 — return first available online peer
    # v2 — use direction to pick closest peer
    return online[0]


def get_all_peers_as_targets():
    """
    Returns all online peers formatted as
    targetPeer for packet_builder.
    Used when broadcasting to ALL devices (point up gesture).
    """
    return [
        {
            'id'  : peer['id'],
            'name': peer['name'],
            'ip'  : peer['ip'],
            'port': peer['port'],
        }
        for peer in get_online_peers()
    ]


# ══════════════════════════════════════════
# STALE PEER CLEANUP
# ══════════════════════════════════════════

def _cleanup_stale_peers():
    """
    Background thread — removes peers we haven't
    heard from in PEER_TIMEOUT_SECONDS.
    Prevents ghost devices staying in the list.
    """
    while True:
        time.sleep(10)  # check every 10 seconds
        now = time.time()

        with _peers_lock:
            stale = [
                peer_id for peer_id, peer in _peers.items()
                if now - peer.get('lastSeen', 0) > PEER_TIMEOUT_SECONDS
            ]

        for peer_id in stale:
            with _peers_lock:
                peer = _peers.get(peer_id)
            if peer:
                print(f"🧹 Removing stale peer: {peer.get('name')}")
                remove_peer(peer_id)


def start_peer_cleanup():
    """
    Starts background cleanup thread.
    Call once when GestFlow starts.
    """
    thread = threading.Thread(
        target=_cleanup_stale_peers,
        daemon=True
    )
    thread.start()
    print("🧹 Peer cleanup service started")


# ══════════════════════════════════════════
# DEBUG HELPERS
# ══════════════════════════════════════════

def print_peer_list():
    """Prints all known peers in a readable format."""
    peers = get_all_peers()

    if not peers:
        print("👥 No peers discovered yet")
        return

    print(f"\n👥 Known Peers ({len(peers)}):")
    print("-" * 40)
    for peer in peers:
        status = "🟢 online" if peer.get('online') else "🔴 offline"
        age    = int(time.time() - peer.get('lastSeen', 0))
        print(f"   {peer.get('name')}")
        print(f"   {peer.get('ip')}:{peer.get('port')}")
        print(f"   OS: {peer.get('os')}  |  {status}  |  seen {age}s ago")
        print()


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    print("👥 GestFlow Peer Manager Test")
    print("=" * 40)

    # Start cleanup
    start_peer_cleanup()

    # Test 1 — Add peers
    print("\n📥 Test 1 — Adding peers:")
    add_peer({
        'id'     : 'peer-001',
        'name'   : 'Desktop-PC',
        'ip'     : '192.168.1.8',
        'port'   : 9000,
        'os'     : 'Windows',
        'version': '1.0'
    })

    add_peer({
        'id'     : 'peer-002',
        'name'   : 'MacBook-Pro',
        'ip'     : '192.168.1.9',
        'port'   : 9000,
        'os'     : 'Mac',
        'version': '1.0'
    })

    add_peer({
        'id'     : 'peer-003',
        'name'   : 'Android-Phone',
        'ip'     : '192.168.1.10',
        'port'   : 9000,
        'os'     : 'Android',
        'version': '1.0'
    })

    # Test 2 — Print peer list
    print("\n📋 Test 2 — Peer list:")
    print_peer_list()

    # Test 3 — Get target peer
    print("🎯 Test 3 — Get target peer:")
    target = get_target_peer()
    if target:
        print(f"   Selected: {target['name']} ({target['ip']})")

    # Test 4 — Get all as targets
    print("\n📢 Test 4 — All peers as targets:")
    targets = get_all_peers_as_targets()
    print(json.dumps(targets, indent=4))

    # Test 5 — Mark peer offline
    print("\n🔴 Test 5 — Mark peer offline:")
    mark_peer_offline('peer-001')
    print(f"   Online peers: {get_online_peer_count()}")
    print(f"   Total peers:  {get_peer_count()}")

    # Test 6 — Remove peer
    print("\n🗑️  Test 6 — Remove peer:")
    remove_peer('peer-002')
    print(f"   Remaining peers: {get_peer_count()}")
    print_peer_list()

    # Test 7 — Find peer by IP
    print("🔍 Test 7 — Find peer by IP:")
    peer = get_peer_by_ip('192.168.1.10')
    if peer:
        print(f"   Found: {peer['name']}")

    print("\n✅ All peer manager tests passed!")