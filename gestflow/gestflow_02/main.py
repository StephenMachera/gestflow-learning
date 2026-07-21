# ==========================================
# GESTFLOW — MAIN ENTRY POINT
# Full pipeline: Phase 1 → 2 → 3 → 4
# ==========================================
import time
import json
import sys
import os
import threading

# ── Path setup ──
# ── Path setup ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(PARENT_DIR)

for path in (BASE_DIR, PARENT_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.append(path)


def ensure_project_python():
    """Use the project's virtual environment when available."""
    venv_python = os.path.join(PROJECT_ROOT, "gestflow-env", "bin", "python")
    if not os.path.exists(venv_python) or sys.executable == venv_python:
        return

    try:
        import websockets  # noqa: F401
    except ModuleNotFoundError:
        print(f"🔧 Switching to project Python: {venv_python}")
        os.execv(venv_python, [venv_python, __file__, *sys.argv[1:]])


ensure_project_python()

# ── Phase 2 imports ──
from browser_bridge_server import (
    start_bridge_server,
    is_extension_connected,
    get_connected_browsers
)
from content_classifier import classify_content
from screen_reader import get_active_content

# ── Phase 3 imports ──
from gestflow_03_state_capture.packet_builder import (
    build_transfer_packet,
    serialize_packet
)
from gestflow_03_state_capture.packet_validator import validate_packet
from gestflow_03_state_capture.device_info import get_device_info

# ── Phase 4 imports ──
from gestflow_04_transfer_protocal.peer_manager import (
    start_peer_cleanup,
    get_target_peer,
    get_online_peer_count,
    print_peer_list
)
from gestflow_04_transfer_protocal.discovery import (
    start_discovery,
    stop_discovery,
    is_discovery_active
)
from gestflow_04_transfer_protocal.transfer_server import (
    start_transfer_server,
    register_packet_handler
)
from gestflow_04_transfer_protocal.transfer_client import (
    send_packet,
    ping_peer
)

from gestflow_05_receiver_engine.receiver import handle_received_packet


# ══════════════════════════════════════════
# PHASE 5 HANDLER (placeholder)
# Phase 5 will replace this with real
# content resumption logic
# ══════════════════════════════════════════

def on_packet_received(packet):
    """
    Called when this device receives a content transfer.
    Phase 5 will open the correct app and resume content.
    For now — just print what was received.
    """
    content      = packet.get('content', {})
    content_type = content.get('contentType')
    state        = content.get('state', {})
    source       = packet.get('sourcePeer', {}).get('name', 'Unknown')

    print(f"\n🎉 CONTENT RECEIVED FROM {source}!")
    print(f"=" * 40)
    print(f"   Type    : {content_type}")

    if content_type == 'code':
        print(f"   File    : {state.get('filePath')}")
        print(f"   Line    : {state.get('cursorLine')}")
        print(f"   Branch  : {state.get('gitBranch')}")
        print(f"\n   Phase 5 would open VSCode at this file and line")

    elif content_type == 'video':
        print(f"   File    : {state.get('filePath')}")
        print(f"   At      : {state.get('timestamp')}s")
        print(f"\n   Phase 5 would open VLC and seek to timestamp")

    elif content_type == 'browser':
        print(f"   URL     : {state.get('url')}")
        print(f"   Title   : {state.get('pageTitle')}")
        print(f"\n   Phase 5 would open this URL in the browser")

    print(f"=" * 40)


# ══════════════════════════════════════════
# SERVICE STARTUP
# ══════════════════════════════════════════

def start_services():
    """Starts ALL GestFlow background services."""
    print("🤚 GestFlow Starting...")
    print("=" * 40)

    # ── Device identity ──
    device = get_device_info()
    print(f"\n🖥️  This device  : {device['name']}")
    print(f"   IP address  : {device['ip']}")
    print(f"   OS          : {device['os']}")
    print(f"   Device ID   : {device['id'][:8]}...")
    print(f"   P2P port    : {device['port']}")

    # ── Phase 2 — browser bridge ──
    print(f"\n📡 Starting browser bridge...")
    start_bridge_server()
    print(f"✅ Browser bridge ready (port 8765)")

    # ── Phase 4 — peer cleanup ──
    print(f"\n🧹 Starting peer cleanup...")
    start_peer_cleanup()
    print(f"✅ Peer cleanup ready")

    # ── Phase 4 — transfer server ──
    print(f"\n🖧  Starting transfer server...")
    register_packet_handler(handle_received_packet)
    start_transfer_server()
    print(f"✅ Transfer server ready (port {device['port']})")

    # ── Phase 4 — discovery ──
    print(f"\n📡 Starting discovery service...")
    start_discovery()
    print(f"✅ Discovery ready")

    print(f"\n{'=' * 40}")
    print(f"✅ All services running")
    print(f"{'=' * 40}\n")


def wait_for_extension(timeout=10):
    """Waits for browser extension to connect."""
    print("⏳ Waiting for browser extension...")
    for i in range(timeout * 2):
        if is_extension_connected():
            browsers = get_connected_browsers()
            print(f"🌐 Browser extension connected ✅ {browsers}\n")
            return True
        time.sleep(0.5)
    print("🌐 Extension not connected — browser fallback active\n")
    return False


def keep_extension_alive():
    """Keeps browser extension service worker alive."""
    from browser_bridge_server import _loop
    import asyncio

    async def ping_all():
        from browser_bridge_server import _connected_browsers
        for ws in list(_connected_browsers.keys()):
            try:
                await ws.send(json.dumps({'type': 'PING'}))
            except Exception:
                pass

    def run():
        while True:
            time.sleep(20)
            if _loop and is_extension_connected():
                asyncio.run_coroutine_threadsafe(ping_all(), _loop)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


# ══════════════════════════════════════════
# MAIN DETECTION + TRANSFER LOOP
# Combines Phase 2 + Phase 3 + Phase 4
# ══════════════════════════════════════════

def run_detection_and_transfer():
    """
    One full GestFlow cycle:
      Phase 2 → detect what is on screen
      Phase 3 → build and validate packet
      Phase 4 → discover target + send packet
    """

    # Show peer status
    peer_count = get_online_peer_count()
    browsers   = get_connected_browsers()

    print(f"🔌 Browser extensions : {browsers if browsers else 'none'}")
    print(f"👥 Online peers       : {peer_count}")

    if peer_count > 0:
        print_peer_list()

    print("You have 7 seconds to switch to VLC, Chrome, VSCode, or Brave...")
    print()
    time.sleep(7)

    # ── Phase 2 — detect active content ──
    raw_window = get_active_content()
    if not raw_window:
        print("❌ Could not detect active window")
        return

    print(f"🔍 Detected app   : {raw_window.get('app')}")
    print(f"📋 Window title   : {raw_window.get('windowTitle')}\n")

    classified = classify_content(raw_window)
    if not classified:
        print("❌ Could not classify content")
        return

    # ── Phase 3 — build transfer packet ──
    packet = build_transfer_packet(
        classified_content = classified,
        gesture            = "FIST_THROW_RIGHT",
        target_peer        = None
    )

    if not packet:
        print("❌ Could not build packet")
        return

    # Validate
    validation = validate_packet(packet)
    if not validation['valid']:
        print(f"❌ Invalid packet: {validation['message']}")
        return

    print(f"✅ Packet built: {packet.get('packetId')}")
    print(f"   Content type: {classified.get('contentType')}")

    # ── Phase 4 — find target and send ──
    target = get_target_peer()

    # Test by itself as transfer server
    # target = {
    # 'id'  : 'self-test',
    # 'name': 'localhost (self)',
    # 'ip'  : '127.0.0.1',
    # 'port': 9001
    # }

    if not target:
        print("\n⚠️  No peers online yet")
        print("   Run GestFlow on another device on the same WiFi")
        print("   Packet is ready — will send when a peer is found")
        print(f"\n📦 Packet preview:")
        print(json.dumps(packet, indent=4))
        return

    print(f"\n🎯 Target peer: {target['name']} ({target['ip']})")

    # Send packet
    result = send_packet(packet, target)

    # Show final status
    status = result.get('status')
    if status == 'DELIVERED':
        print(f"\n✅ Transfer complete!")
        print(f"   {classified.get('contentType')} sent to {target['name']}")
    else:
        print(f"\n❌ Transfer failed")
        print(f"   Status: {status}")


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

if __name__ == "__main__":

    # 1 — Start all services
    start_services()

    # 2 — Wait for browser extension
    wait_for_extension(timeout=10)

    # 3 — Keep extension alive
    keep_extension_alive()

    # 4 — Main loop
    try:
        while True:
            run_detection_and_transfer()
            print("\n" + "-" * 40)
            print("Waiting for next detection...")
            print("-" * 40 + "\n")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nShutting down GestFlow...")
        stop_discovery()
        print("👋 GestFlow stopped")