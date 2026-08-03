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

# ── Phase 1 import ──
from gestflow_06_integration.gesture_engine import (
    start_gesture_engine,
    register_action
)

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
# GESTURE ACTION HANDLERS
# These replace the 7-second timer
# ══════════════════════════════════════════

# Shared state between gesture handlers
_grabbed_content = None
_grabbed_packet  = None


def on_grab_gesture(gesture_info):
    """FIST gesture — grab content and hold it."""
    # Import shared state from gesture engine
    import gestflow_06_integration.gesture_engine as ge

    print("\n✊ GRAB gesture — detecting content...")

    raw_window = get_active_content()
    if not raw_window:
        print("❌ Could not detect active window")
        ge._grab_status = "❌ Could not detect content"
        return

    classified = classify_content(raw_window)
    if not classified:
        print("❌ Could not classify content")
        ge._grab_status = "❌ Could not classify content"
        return

    packet = build_transfer_packet(
        classified_content = classified,
        gesture            = 'GRAB_CONTENT'
    )

    if not packet:
        ge._grab_status = "❌ Could not build packet"
        return

    validation = validate_packet(packet)
    if not validation['valid']:
        print(f"❌ Invalid packet: {validation['message']}")
        ge._grab_status = "❌ Invalid packet"
        return

    # Store grabbed content
    ge._grabbed_content = classified
    ge._grabbed_packet  = packet

    content_type = classified.get('contentType', 'unknown')
    app          = classified.get('app', 'unknown')

    print(f"\n✅ Content grabbed!")
    print(f"   App     : {app}")
    print(f"   Type    : {content_type}")
    print(f"   Now make THROW RIGHT gesture to send")

    # ← This appears on camera overlay
    ge._grab_status = f"✊ {content_type} grabbed — throw it! 👉"


def on_throw_right(gesture_info):
    """THROW RIGHT — send grabbed content to peer."""
    import gestflow_06_integration.gesture_engine as ge
    from gestflow_04_transfer_protocal.peer_manager import get_all_peers, get_online_peers

    # ── DEBUG ──
    all_peers    = get_all_peers()
    online_peers = get_online_peers()
    print(f"\n🔍 DEBUG:")
    print(f"   All peers    : {len(all_peers)}")
    print(f"   Online peers : {len(online_peers)}")
    for p in all_peers:
        print(f"   → {p.get('name')} ({p.get('ip')}) online={p.get('online')}")

    if not ge._grabbed_packet:
        print("⚠️  Nothing grabbed — make FIST gesture first")
        return

    print("\n👉 THROW RIGHT — sending to target device...")
    target = get_target_peer()

    if not target:
        print("⚠️  No peers online")
        return

    result = send_packet(ge._grabbed_packet, target)

    if not ge._grabbed_packet:
        print("⚠️  Nothing grabbed — make FIST gesture first")
        ge._grab_status = "⚠️  Nothing grabbed — make FIST first ✊"
        return

    print("\n👉 THROW RIGHT — sending to target device...")

    target = get_target_peer()
    if not target:
        print("⚠️  No peers online")
        ge._grab_status = "⚠️  No peers found on network"
        return

    # Show throwing status on overlay
    ge._grab_status = f"👉 Throwing to {target['name']}..."

    result = send_packet(ge._grabbed_packet, target)

    if result.get('status') == 'DELIVERED':
        print(f"✅ Delivered to {target['name']}")

        # Clear grab state after successful delivery
        ge._grabbed_packet  = None
        ge._grabbed_content = None
        ge._grab_status     = f"✅ Delivered to {target['name']}!"

    else:
        print(f"❌ Transfer failed")
        ge._grab_status = f"❌ Transfer failed — try again"


def on_throw_left(gesture_info):
    """
    THROW LEFT gesture — same as throw right for v1.
    Future: pick peer on the left side.
    """
    on_throw_right(gesture_info)


def on_pinch_gesture(gesture_info):
    """
    PINCH gesture — grab small item (text, link).
    Same as grab for v1.
    """
    on_grab_gesture(gesture_info)


def on_cancel_gesture(gesture_info):
    """CANCEL — drop grabbed content."""
    import gestflow_06_integration.gesture_engine as ge

    print("\n🤙 CANCEL — clearing grabbed content")
    ge._grabbed_content = None
    ge._grabbed_packet  = None
    ge._grab_status     = None  # ← clears the blue bar
    print("✅ Transfer cancelled")


def on_expand_gesture(gesture_info):
    """
    EXPAND gesture — future feature.
    """
    print("\n🖖 EXPAND gesture detected — coming in v2")


def on_select_multiple(gesture_info):
    """
    SELECT MULTIPLE gesture — future feature.
    """
    print("\n✌️  SELECT MULTIPLE detected — coming in v2")


# ══════════════════════════════════════════
# SERVICES STARTUP
# ══════════════════════════════════════════
def keep_peers_alive():
    """
    Pings all known peers every 15 seconds.
    Prevents peers from being marked stale.
    """
    from gestflow_04_transfer_protocal.peer_manager import (
        get_all_peers, update_peer_last_seen
    )
    from gestflow_04_transfer_protocal.transfer_client import ping_peer

    def run():
        while True:
            time.sleep(15)
            peers = get_all_peers()
            for peer in peers:
                try:
                    alive = ping_peer(peer)
                    if alive:
                        update_peer_last_seen(peer['id'])
                        print(f"🏓 Peer alive: {peer['name']}")
                    else:
                        print(f"⚠️  Peer not responding: {peer['name']}")
                except Exception:
                    pass

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print("🏓 Peer keep-alive started")

def start_services():
    """Starts ALL GestFlow background services."""
    print("🤚 GestFlow Starting...")
    print("=" * 40)

    device = get_device_info()
    print(f"\n🖥️  This device  : {device['name']}")
    print(f"   IP address  : {device['ip']}")
    print(f"   OS          : {device['os']}")
    print(f"   P2P port    : {device['port']}")

    # Phase 2 — browser bridge
    print(f"\n📡 Starting browser bridge...")
    start_bridge_server()
    print(f"✅ Browser bridge ready")

    # Phase 4 — peer cleanup
    print(f"\n🧹 Starting peer cleanup...")
    start_peer_cleanup()
    print(f"✅ Peer cleanup ready")

    # Phase 4 — transfer server
    print(f"\n🖧  Starting transfer server...")
    register_packet_handler(handle_received_packet)
    start_transfer_server()
    print(f"✅ Transfer server ready")

    # Phase 4 — discovery
    print(f"\n📡 Starting discovery...")
    start_discovery()
    print(f"✅ Discovery ready")

    keep_peers_alive()
    # Phase 6 — register gesture actions
    print(f"\n✋ Registering gesture actions...")
    register_action('GRAB_CONTENT'   , on_grab_gesture)
    register_action('THROW_RIGHT'    , on_throw_right)
    register_action('THROW_LEFT'     , on_throw_left)
    register_action('GRAB_SMALL'     , on_pinch_gesture)
    register_action('CANCEL_TRANSFER', on_cancel_gesture)
    register_action('EXPAND_CONTENT' , on_expand_gesture)
    register_action('SELECT_MULTIPLE', on_select_multiple)
    print(f"✅ Gesture actions registered")

    print(f"\n{'=' * 40}")
    print(f"✅ All services running")
    print(f"{'=' * 40}\n")


def wait_for_extension(timeout=10):
    """Waits for browser extension."""
    print("⏳ Waiting for browser extension...")
    for i in range(timeout * 2):
        if is_extension_connected():
            browsers = get_connected_browsers()
            print(f"🌐 Browser extension connected ✅ {browsers}\n")
            return True
        time.sleep(0.5)
    print("🌐 Extension not connected — fallback active\n")
    return False


def keep_extension_alive():
    """Keeps browser extension alive."""
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
# MAIN
# ══════════════════════════════════════════

if __name__ == "__main__":

    # 1 — Start all services
    start_services()

    # 2 — Wait for browser extension
    wait_for_extension(timeout=10)

    # 3 — Keep extension alive
    keep_extension_alive()

    # 4 — Show peer status
    print(f"👥 Online peers: {get_online_peer_count()}")
    if get_online_peer_count() > 0:
        print_peer_list()

    # 5 — Start gesture engine (replaces 7-second timer)
    # This blocks until user presses Q
    print("\n✋ GestFlow ready — show your hand to the camera!\n")
    print("Gestures:")
    print("  ✊ FIST        → grab content on screen")
    print("  👉 THROW RIGHT → send to target device")
    print("  👈 THROW LEFT  → send to target device")
    print("  🤏 PINCH       → grab small item")
    print("  🤙 CANCEL      → cancel transfer")
    print("  Press Q to quit\n")

    try:
        start_gesture_engine()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down GestFlow...")
        stop_discovery()
        print("👋 GestFlow stopped")