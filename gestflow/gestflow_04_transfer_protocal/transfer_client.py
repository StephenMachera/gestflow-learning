# ==========================================
# GESTFLOW TRANSFER CLIENT
# ==========================================
# Single responsibility:
#   → Connect to target peer
#   → Send transfer packet
#   → Wait for ACK
# ==========================================

import asyncio
import json
import websockets
import threading
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_03_state_capture.packet_builder import (
    build_ping_packet,
    serialize_packet,
    deserialize_packet,
    update_packet_status,
    set_target_peer
)
from gestflow_03_state_capture.device_info import GESTFLOW_P2P_PORT

import logging
logging.getLogger('websockets').setLevel(logging.CRITICAL)

# ── Transfer settings ──
CONNECT_TIMEOUT = 5     # seconds to wait for connection
ACK_TIMEOUT     = 10    # seconds to wait for ACK
MAX_RETRIES     = 3     # max send attempts


# ══════════════════════════════════════════
# CORE SEND FUNCTION
# ══════════════════════════════════════════

async def _send_packet_async(target_ip, target_port, packet):
    """
    Async function — connects to target and sends packet.
    Waits for ACK response.

    Returns:
      { success: True, ack: {...} }   on success
      { success: False, error: '...' } on failure
    """
    url = f"ws://{target_ip}:{target_port}"

    try:
        async with websockets.connect(
            url,
            open_timeout = CONNECT_TIMEOUT,
            max_size     = 500 * 1024 * 1024
        ) as websocket:

            # Send packet
            await websocket.send(serialize_packet(packet))
            print(f"   📤 Packet sent to {target_ip}:{target_port}")

            # Wait for ACK
            try:
                raw_ack = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=ACK_TIMEOUT
                )
                ack = deserialize_packet(raw_ack)

                if ack and ack.get('type') == 'ACK':
                    if ack.get('success'):
                        return {'success': True, 'ack': ack}
                    else:
                        return {
                            'success': False,
                            'error'  : ack.get('error', 'Target rejected packet')
                        }
                else:
                    return {
                        'success': False,
                        'error'  : 'Invalid ACK received'
                    }

            except asyncio.TimeoutError:
                return {
                    'success': False,
                    'error'  : f'No ACK received within {ACK_TIMEOUT}s'
                }

    except ConnectionRefusedError:
        return {
            'success': False,
            'error'  : f'Target {target_ip}:{target_port} refused connection — GestFlow running?'
        }
    except OSError as e:
        return {
            'success': False,
            'error'  : f'Network error: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'error'  : str(e)
        }


def send_packet(packet, target_peer):
    """
    Sends a packet to a target peer with retry logic.
    This is the main function transfer protocol uses.

    Arguments:
      packet      → built by packet_builder
      target_peer → peer dict from peer_manager

    Returns updated packet with final status.
    """
    target_ip   = target_peer.get('ip')
    target_port = target_peer.get('port', GESTFLOW_P2P_PORT)
    target_name = target_peer.get('name', target_ip)

    if not target_ip:
        print(f"❌ No IP address for target peer")
        return update_packet_status(packet, 'FAILED')

    # Set target peer in packet
    packet = set_target_peer(packet, target_peer)
    packet = update_packet_status(packet, 'SENDING')

    print(f"\n📡 Sending to {target_name} ({target_ip}:{target_port})")
    print(f"   Packet ID : {packet.get('packetId')}")
    print(f"   Content   : {packet.get('content', {}).get('contentType')}")

    # Retry loop
    max_retries = packet.get('transfer', {}).get('maxRetries', MAX_RETRIES)

    for attempt in range(1, max_retries + 1):
        print(f"   Attempt   : {attempt}/{max_retries}")

        # Run async send in sync context
        result = asyncio.run(
            _send_packet_async(target_ip, target_port, packet)
        )

        if result['success']:
            packet = update_packet_status(packet, 'DELIVERED')
            print(f"   ✅ Delivered to {target_name}")
            return packet

        else:
            error = result.get('error', 'Unknown error')
            print(f"   ⚠️  Attempt {attempt} failed: {error}")

            # Update retry count
            if 'transfer' in packet:
                packet['transfer']['retryCount'] = attempt

            # Wait before retry (except last attempt)
            if attempt < max_retries:
                wait = attempt * 2  # 2s, 4s, 6s
                print(f"   ⏳ Retrying in {wait}s...")
                time.sleep(wait)

    # All retries exhausted
    packet = update_packet_status(packet, 'FAILED')
    print(f"   ❌ Failed after {max_retries} attempts")
    return packet


def send_to_all_peers(packet, peers):
    """
    Sends packet to ALL peers simultaneously.
    Used for the "point up" gesture — broadcast to everyone.

    Returns list of results per peer.
    """
    if not peers:
        print("⚠️  No peers to broadcast to")
        return []

    print(f"\n📢 Broadcasting to {len(peers)} peers...")

    results = []
    threads = []

    def send_to_one(peer):
        import copy
        peer_packet = copy.deepcopy(packet)
        result      = send_packet(peer_packet, peer)
        results.append({
            'peer'  : peer.get('name'),
            'status': result.get('status')
        })

    # Send to all peers simultaneously using threads
    for peer in peers:
        thread = threading.Thread(
            target=send_to_one,
            args=(peer,),
            daemon=True
        )
        threads.append(thread)
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join(timeout=30)

    return results


def ping_peer(peer):
    """
    Sends a ping to check if peer is reachable.
    Returns True if peer responds with pong.
    """
    ping_packet = build_ping_packet()

    target_ip   = peer.get('ip')
    target_port = peer.get('port', GESTFLOW_P2P_PORT)

    result = asyncio.run(
        _send_packet_async(target_ip, target_port, ping_packet)
    )

    return result.get('success', False)


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from gestflow_03_state_capture.packet_builder import build_transfer_packet
    from gestflow_03_state_capture.device_info import get_device_info

    print("📡 GestFlow Transfer Client Test")
    print("=" * 40)
    print("This sends a test packet to localhost:9000")
    print("Make sure transfer_server.py is running first!\n")

    # Mock content from Phase 2
    mock_content = {
        "app"        : "code",
        "contentType": "code",
        "windowTitle": "main.py - gestflow-learning - Visual Studio Code",
        "adapter"    : "vscode_adapter",
        "state": {
            "filePath"  : "/home/user/gestflow/main.py",
            "fileName"  : "main.py",
            "language"  : "python",
            "cursorLine": 42,
            "gitBranch" : "dev-branch",
        }
    }

    # Build packet
    packet = build_transfer_packet(
        classified_content = mock_content,
        gesture            = "FIST_THROW_RIGHT"
    )

    # Send to localhost for testing
    # In production this comes from peer_manager.get_target_peer()
    device      = get_device_info()
    target_peer = {
        'id'  : 'test-target',
        'name': 'localhost (self test)',
        'ip'  : '127.0.0.1',
        'port': device['port']
    }

    print(f"📤 Sending test packet...")
    result = send_packet(packet, target_peer)

    print(f"\n📊 Final packet status: {result.get('status')}")