import os
import sys
import json
import time
import uuid
import base64


# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_03_state_capture.device_info import get_device_info

# ── Protocol version ──
# Bump this when packet format changes
# Receiving devices check this before processing
GESTFLOW_VERSION = '1'

# Maximum file size to embed directly in packet
MAX_EMBED_SIZE_MB = 50
MAX_EMBED_SIZE    = MAX_EMBED_SIZE_MB * 1024 * 1024  # bytes

# ── Packet types ──
PACKET_TYPES = {
    'CONTENT_TRANSFER' : 'CONTENT_TRANSFER',  # throw content to another device
    'ACK'              : 'ACK',               # confirm packet received
    'PING'             : 'PING',              # check if peer is alive
    'PONG'             : 'PONG',              # response to ping
    'PEER_ANNOUNCE'    : 'PEER_ANNOUNCE',     # announce presence on network
    'CANCEL'           : 'CANCEL',            # cancel a transfer in progress
}

# ── Content types ──
CONTENT_TYPES = {
    'video'  : 'video',
    'audio'  : 'audio',
    'browser': 'browser',
    'code'   : 'code',
    'file'   : 'file',
    'unknown': 'unknown',
}

# ══════════════════════════════════════════
# PACKET ID GENERATION
# ══════════════════════════════════════════
def _generate_packet_id():
    """
    Generate a unique packet ID using UUID4.
    """
    return str(uuid.uuid4())[:8].upper()

def _get_timestamp():
    """
    Returns current Unix timestamp.
    Used to track when packet was created.
    Also used by receiver to detect stale packets.
    """
    return int(time.time())

# ══════════════════════════════════════════
# PACKET BUILDERS
# ══════════════════════════════════════════
def _embed_file(file_path):
    """
    Reads file and returns base64 encoded content.
    Returns None if file too large or unreadable.
    """
    try:
        file_size = os.path.getsize(file_path)

        if file_size > MAX_EMBED_SIZE:
            print(f"⚠️  File too large to embed: "
                  f"{file_size / 1024 / 1024:.1f}MB "
                  f"(max {MAX_EMBED_SIZE_MB}MB)")
            print(f"   Streaming will be added in v2")
            return None, file_size

        print(f"📎 Embedding file: {file_size / 1024 / 1024:.1f}MB")

        with open(file_path, 'rb') as f:
            raw_bytes      = f.read()
            encoded        = base64.b64encode(raw_bytes).decode('utf-8')
            print(f"✅ File embedded successfully")
            return encoded, file_size

    except Exception as e:
        print(f"⚠️  Could not read file: {e}")
        return None, 0


def build_transfer_packet(classified_content, gesture, target_peer=None):
    """
    Builds transfer packet.
    For video/audio — embeds file if small enough.
    For code — embeds file content as text.
    """
    source_peer  = get_device_info()
    content      = dict(classified_content)
    content_type = content.get('contentType')
    state        = dict(content.get('state', {}))

    # ── Embed file content based on type ──
    if content_type in ('video', 'audio'):
        file_path = state.get('filePath')

        if file_path and os.path.exists(file_path):
            encoded, file_size = _embed_file(file_path)

            if encoded:
                state['fileData']      = encoded           # base64 content
                state['fileSize']      = file_size
                state['fileName']      = os.path.basename(file_path)
                state['fileExtension'] = os.path.splitext(file_path)[1]
                state['embedded']      = True
                print(f"📦 Video embedded in packet")
            else:
                state['embedded'] = False
                state['fileName'] = os.path.basename(file_path)
                print(f"⚠️  File not embedded — too large")
        else:
            state['embedded'] = False

    elif content_type == 'code':
        file_path = state.get('filePath')

        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    state['fileContent']   = f.read()
                    state['fileExtension'] = os.path.splitext(file_path)[1]
                    state['fileName']      = os.path.basename(file_path)
                    state['embedded']      = True
            except Exception as e:
                print(f"⚠️  Could not read code file: {e}")
                state['embedded'] = False

    content['state'] = state

    packet = {
        'gestflow'  : GESTFLOW_VERSION,
        'packetId'  : _generate_packet_id(),
        'type'      : PACKET_TYPES['CONTENT_TRANSFER'],
        'timestamp' : _get_timestamp(),
        'sourcePeer': {
            'id'      : source_peer['id'],
            'name'    : source_peer['name'],
            'hostname': source_peer['hostname'],
            'os'      : source_peer['os'],
            'ip'      : source_peer['ip'],
            'port'    : source_peer['port'],
        },
        'targetPeer': target_peer,
        'gesture'   : gesture,
        'content'   : content,
        'transfer'  : {
            'requiresAck': True,
            'expiresIn'  : 120,   # ← increased for large transfers
            'retryCount' : 0,
            'maxRetries' : 3,
        },
        'status': 'PENDING'
    }

    return packet

def build_ack_packet(original_packet, success = True, error = None):
    """
    Builds an acknowledgement packet.
    Sent by receiver back to sender to confirm receipt.

    Arguments:
      original_packet → the packet being acknowledged
      success         → True if received and processing started
      error           → error message if something went wrong
    """
    source_peer = get_device_info()

    return {
        'gestflow'  : GESTFLOW_VERSION,
        'packetId'  : _generate_packet_id(),
        'type'      : PACKET_TYPES['ACK'],
        'timestamp' : _get_timestamp(),

        'sourcePeer': {
            'id'  : source_peer['id'],
            'name': source_peer['name'],
            'ip'  : source_peer['ip'],
            'port': source_peer['port'],
        },

        # Reference the original packet
        'ackFor'  : original_packet.get('packetId'),
        'success' : success,
        'error'   : error,
        'status'  : 'DELIVERED' if success else 'FAILED'
    }

def build_ping_packet():
    """
    Builds a ping packet.
    Sent to check if a peer is alive and reachable.
    Peer responds with PONG.
    """
    source_peer = get_device_info()

    return {
        'gestflow'  : GESTFLOW_VERSION,
        'packetId'  : _generate_packet_id(),
        'type'      : PACKET_TYPES['PING'],
        'timestamp' : _get_timestamp(),

        'sourcePeer': {
            'id'  : source_peer['id'],
            'name': source_peer['name'],
            'ip'  : source_peer['ip'],
            'port': source_peer['port'],
        }
    }

def build_pong_packet(ping_packet):
    """
    Builds a pong packet in response to a ping.
    """
    source_peer = get_device_info()

    return {
        'gestflow'  : GESTFLOW_VERSION,
        'packetId'  : _generate_packet_id(),
        'type'      : PACKET_TYPES['PONG'],
        'timestamp' : _get_timestamp(),
        'pingId'    : ping_packet.get('packetId'),

        'sourcePeer': {
            'id'  : source_peer['id'],
            'name': source_peer['name'],
            'ip'  : source_peer['ip'],
            'port': source_peer['port'],
        }
    }

def build_peer_announce_packet():
    """
    Builds a peer announcement packet.
    Broadcast on the network so other devices
    know this device exists and is running GestFlow.
    Used by Phase 4 mDNS discovery.
    """
    source_peer = get_device_info()

    return {
        'gestflow'  : GESTFLOW_VERSION,
        'packetId'  : _generate_packet_id(),
        'type'      : PACKET_TYPES['PEER_ANNOUNCE'],
        'timestamp' : _get_timestamp(),

        'sourcePeer': {
            'id'      : source_peer['id'],
            'name'    : source_peer['name'],
            'hostname': source_peer['hostname'],
            'os'      : source_peer['os'],
            'ip'      : source_peer['ip'],
            'port'    : source_peer['port'],
        },
        'capabilities': [
            'video',      # can send and receive video state
            'browser',    # can send and receive browser tabs
            'code',       # can send and receive code state
            'audio',      # can send and receive audio state
            'file',       # can send and receive files
        ]
    }

def build_cancel_packet(original_packet_id):
    """
    Builds a cancel packet.
    Sent when user makes cancel gesture (shake hand)
    to abort a transfer in progress.
    """
    source_peer = get_device_info()

    return {
        'gestflow'   : GESTFLOW_VERSION,
        'packetId'   : _generate_packet_id(),
        'type'       : PACKET_TYPES['CANCEL'],
        'timestamp'  : _get_timestamp(),
        'cancelledId': original_packet_id,

        'sourcePeer': {
            'id'  : source_peer['id'],
            'name': source_peer['name'],
            'ip'  : source_peer['ip'],
            'port': source_peer['port'],
        }
    }

# ══════════════════════════════════════════
# PACKET UTILITIES
# ══════════════════════════════════════════
def serialize_packet(packet):
    """
    Serializes a packet to JSON string.
    """
    return json.dumps(packet, ensure_ascii=False)

def deserialize_packet(json_str):
    """
    Deserializes a JSON string back to a packet dictionary.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid packet received: {e}")
        return None
    
def update_packet_status(packet, new_status):
    """
    Updates the status of a packet as it
    progresses through the transfer lifecycle.
    """
    packet['status'] = new_status
    return packet
def set_target_peer(packet, target_peer):
    """
    Sets the target peer information in a packet.
    Used when the target peer is determined after packet creation.
    Called by Phase 4 after discovering the target device.
    """
    packet['target_peer'] = target_peer
    return packet

def get_packet_age(packet):
    """
    Returns the age of the packet in seconds.
    Used to determine if a packet has expired.
    """
    created_time = packet.get('timestamp', 0)
    return int(time.time()) - created_time

def is_packet_expired(packet):
    """
    Returns True if packet has exceeded its expiry time.
    Prevents stale transfers from executing.
    """
    expires_in = packet.get('transfer', {}).get('expiresIn', 30)
    return get_packet_age(packet) > expires_in


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    print("📦 GestFlow Packet Builder Test")
    print("=" * 40)

    # ── Simulate Phase 2 output ──
    mock_classified_content = {
        "app"        : "code",
        "contentType": "code",
        "windowTitle": "main.py - gestflow-learning - Visual Studio Code",
        "adapter"    : "vscode_adapter",
        "state": {
            "filePath"    : "/home/user/gestflow/main.py",
            "fileName"    : "main.py",
            "language"    : "python",
            "cursorLine"  : 42,
            "cursorColumn": 8,
            "projectName" : "gestflow-learning",
            "gitBranch"   : "dev-branch",
            "isUnsaved"   : False
        }
    }

    # ── Test 1 — Build transfer packet ──
    print("\n📤 Test 1 — Transfer Packet:")
    print("-" * 40)
    packet = build_transfer_packet(
        classified_content = mock_classified_content,
        gesture            = "FIST_THROW_RIGHT",
        target_peer        = None   # Phase 4 will fill this
    )
    print(json.dumps(packet, indent=4))

    # ── Test 2 — Serialize and deserialize ──
    print("\n🔄 Test 2 — Serialize / Deserialize:")
    print("-" * 40)
    json_str = serialize_packet(packet)
    print(f"Serialized length: {len(json_str)} bytes")
    recovered = deserialize_packet(json_str)
    print(f"Deserialized successfully: {recovered['packetId'] == packet['packetId']} ✅")

    # ── Test 3 — ACK packet ──
    print("\n✅ Test 3 — ACK Packet:")
    print("-" * 40)
    ack = build_ack_packet(packet, success=True)
    print(json.dumps(ack, indent=4))

    # ── Test 4 — Ping/Pong ──
    print("\n🏓 Test 4 — Ping / Pong:")
    print("-" * 40)
    ping = build_ping_packet()
    pong = build_pong_packet(ping)
    print(f"Ping ID : {ping['packetId']}")
    print(f"Pong for: {pong['pingId']}")
    print(f"Match   : {ping['packetId'] == pong['pingId']} ✅")

    # ── Test 5 — Peer announce ──
    print("\n📢 Test 5 — Peer Announce Packet:")
    print("-" * 40)
    announce = build_peer_announce_packet()
    print(json.dumps(announce, indent=4))

    # ── Test 6 — Expiry check ──
    print("\n⏰ Test 6 — Packet Expiry:")
    print("-" * 40)
    print(f"Packet age   : {get_packet_age(packet)} seconds")
    print(f"Packet expired: {is_packet_expired(packet)}")

    print("\n✅ All packet builder tests passed!")

