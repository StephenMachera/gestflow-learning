# ==========================================
# GESTFLOW TRANSFER SERVER
# ==========================================
# Single responsibility:
#   → Listen for incoming P2P packets
#   → Validate every packet before processing
#   → Send ACK back to sender
#   → Hand packet to Phase 5 for resuming
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
    build_ack_packet,
    build_pong_packet,
    serialize_packet,
    deserialize_packet
)
from gestflow_03_state_capture.packet_validator import validate_packet
from gestflow_03_state_capture.device_info import get_device_info, GESTFLOW_P2P_PORT
from gestflow_04_transfer_protocal.peer_manager import (
    add_peer,
    update_peer_last_seen
)

import logging
logging.getLogger('websockets').setLevel(logging.CRITICAL)

# ── Server state ──
_server_loop    = None
_server_running = False

# ── Packet handler ──
# Phase 5 registers a callback here
# Server calls it when a valid packet arrives
_packet_handler = None


# ══════════════════════════════════════════
# PACKET HANDLER REGISTRATION
# ══════════════════════════════════════════

def register_packet_handler(handler_fn):
    """
    Registers a callback for incoming packets.
    Phase 5 calls this to receive content transfers.

    handler_fn receives one argument: the packet dict
    Example:
        def my_handler(packet):
            content_type = packet['content']['contentType']
            print(f"Received {content_type} transfer!")

        register_packet_handler(my_handler)
    """
    global _packet_handler
    _packet_handler = handler_fn
    print("✅ Packet handler registered")


# ══════════════════════════════════════════
# CONNECTION HANDLER
# ══════════════════════════════════════════

async def _handle_incoming(websocket):
    """
    Handles every incoming P2P connection.
    Each connection is a packet from another GestFlow device.
    """
    sender_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'

    try:
        async for raw_message in websocket:
            try:
                # Deserialize packet
                packet = deserialize_packet(raw_message)
                if not packet:
                    print(f"⚠️  Invalid JSON from {sender_ip}")
                    continue

                packet_type = packet.get('type')
                packet_id   = packet.get('packetId', 'unknown')
                source_peer = packet.get('sourcePeer', {})
                source_name = source_peer.get('name', sender_ip)

                print(f"\n📥 Incoming packet from {source_name}")
                print(f"   Type     : {packet_type}")
                print(f"   Packet ID: {packet_id}")

                # Update peer last seen
                peer_id = source_peer.get('id')
                if peer_id:
                    update_peer_last_seen(peer_id)

                # Route by packet type
                await _route_packet(websocket, packet)

            except Exception as e:
                print(f"⚠️  Error processing packet: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass


async def _route_packet(websocket, packet):
    """
    Routes packet to correct handler based on type.
    """
    packet_type = packet.get('type')

    if packet_type == 'CONTENT_TRANSFER':
        await _handle_content_transfer(websocket, packet)

    elif packet_type == 'PING':
        await _handle_ping(websocket, packet)

    elif packet_type == 'PEER_ANNOUNCE':
        await _handle_peer_announce(websocket, packet)

    elif packet_type == 'CANCEL':
        await _handle_cancel(websocket, packet)

    else:
        print(f"⚠️  Unknown packet type: {packet_type}")


async def _handle_content_transfer(websocket, packet):
    """
    Handles incoming content transfer packet.
    Validates → ACK → hand to Phase 5 handler.
    """
    packet_id   = packet.get('packetId')
    source_name = packet.get('sourcePeer', {}).get('name', 'Unknown')
    content     = packet.get('content', {})
    content_type = content.get('contentType', 'unknown')

    print(f"   Content  : {content_type}")

    # Validate packet
    validation = validate_packet(packet)
    if not validation['valid']:
        print(f"   ❌ Invalid: {validation['message']}")

        # Send failure ACK
        ack = build_ack_packet(packet, success=False,
                               error=validation['message'])
        await websocket.send(serialize_packet(ack))
        return

    print(f"   ✅ Valid packet from {source_name}")

    # Send success ACK immediately
    ack = build_ack_packet(packet, success=True)
    await websocket.send(serialize_packet(ack))
    print(f"   📤 ACK sent")

    # Hand to Phase 5 handler
    if _packet_handler:
        try:
            _packet_handler(packet)
        except Exception as e:
            print(f"   ⚠️  Handler error: {e}")
    else:
        # No Phase 5 handler yet — just print
        print(f"\n🎉 CONTENT RECEIVED!")
        print(f"   From    : {source_name}")
        print(f"   Type    : {content_type}")
        print(f"   State   : {json.dumps(content.get('state', {}), indent=6)}")


async def _handle_ping(websocket, packet):
    """Responds to ping with pong."""
    pong = build_pong_packet(packet)
    await websocket.send(serialize_packet(pong))
    source = packet.get('sourcePeer', {}).get('name', 'Unknown')
    print(f"   🏓 Pong sent to {source}")


async def _handle_peer_announce(websocket, packet):
    """Adds announcing peer to peer list."""
    source_peer = packet.get('sourcePeer', {})
    if source_peer:
        add_peer(source_peer)
        print(f"   👥 Peer announced: {source_peer.get('name')}")


async def _handle_cancel(websocket, packet):
    """Handles transfer cancellation."""
    cancelled_id = packet.get('cancelledId')
    source       = packet.get('sourcePeer', {}).get('name', 'Unknown')
    print(f"   ❌ Transfer {cancelled_id} cancelled by {source}")


# ══════════════════════════════════════════
# SERVER STARTUP
# ══════════════════════════════════════════

async def _run_server():
    """Runs the P2P WebSocket server."""
    global _server_loop, _server_running

    _server_loop    = asyncio.get_running_loop()
    _server_running = True

    device = get_device_info()

    async with websockets.serve(
        _handle_incoming,
        '0.0.0.0',          # listen on ALL interfaces
        device['port']      # port 9000
    ):
        print(f"🖧  P2P server listening on port {device['port']}")
        print(f"   Any GestFlow device can now send to this machine")
        await asyncio.Future()  # run forever


def start_transfer_server():
    """
    Starts P2P transfer server in background thread.
    Call once when GestFlow starts.
    """
    def run():
        asyncio.run(_run_server())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1)
    print("✅ Transfer server started")


def is_server_running():
    """Returns True if transfer server is running."""
    return _server_running


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    print("🖧  GestFlow Transfer Server Test")
    print("=" * 40)
    print("Starting server — waiting for incoming packets...")
    print("Run transfer_client.py to send a test packet\n")

    # Register a test handler
    def test_handler(packet):
        content = packet.get('content', {})
        print(f"\n🎉 Phase 5 would now resume:")
        print(f"   App     : {content.get('app')}")
        print(f"   Type    : {content.get('contentType')}")
        print(f"   State   : {json.dumps(content.get('state', {}), indent=6)}")

    register_packet_handler(test_handler)

    # Start server
    start_transfer_server()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

