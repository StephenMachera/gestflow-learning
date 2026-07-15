# ==========================================
# GESTFLOW — MAIN ENTRY POINT
# ==========================================
import time
import json
import sys
import os
import threading

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
from gestflow_state_capture.packet_builder import (
    build_transfer_packet,
    serialize_packet
)
from gestflow_state_capture.packet_validator import validate_packet
from gestflow_state_capture.device_info import get_device_info


# ══════════════════════════════════════════
# SERVICES
# ══════════════════════════════════════════

def start_services():
    """Starts all GestFlow background services."""
    print("🤚 GestFlow Starting...")
    print("=" * 40)

    # Start browser bridge
    print("Starting browser bridge server...")
    start_bridge_server()

    # Show this device's identity
    device = get_device_info()
    print(f"\n🖥️  This device  : {device['name']}")
    print(f"   IP address  : {device['ip']}")
    print(f"   OS          : {device['os']}")
    print(f"   Device ID   : {device['id'][:8]}...")
    print(f"   P2P port    : {device['port']}")
    print(f"\n✅ Services ready\n")


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
    """
    Pings all connected browser extensions every 20 seconds.
    Prevents Chrome service worker from sleeping.
    """
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
# DETECTION + PACKET BUILDING
# Combines Phase 2 + Phase 3
# ══════════════════════════════════════════

def run_detection():
    """
    One full GestFlow cycle:
      Phase 2 → detect what is on screen
      Phase 3 → build transfer packet
      Phase 3 → validate packet
      Phase 4 → (coming next) send to target device
    """
    browsers = get_connected_browsers()
    print(f"🔌 Connected browsers : {browsers if browsers else 'none'}")
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
        gesture            = "FIST_THROW_RIGHT",  # Phase 1 will set this
        target_peer        = None                  # Phase 4 will set this
    )

    if not packet:
        print("❌ Could not build packet")
        return

    # ── Phase 3 — validate packet ──
    validation = validate_packet(packet)
    if not validation['valid']:
        print(f"❌ Invalid packet: {validation['message']}")
        for error in validation['errors']:
            print(f"   → {error}")
        return

    # ── Display results ──
    print("📦 GestFlow Transfer Packet:")
    print("=" * 40)
    print(json.dumps(packet, indent=4))

    serialized = serialize_packet(packet)
    print(f"\n📡 Packet size    : {len(serialized)} bytes")
    print(f"✅ Packet status  : {validation['message']}")
    print(f"⏳ Packet status  : {packet['status']}")
    print(f"\n🚀 Ready for Phase 4 — transfer to target device\n")


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

if __name__ == "__main__":

    # 1 — Start all services
    start_services()

    # 2 — Wait for browser extension
    wait_for_extension(timeout=10)

    # 3 — Keep extension alive permanently
    keep_extension_alive()

    # 4 — Run detection loop
    try:
        while True:
            run_detection()
            print("-" * 40)
            print("Waiting for next detection...")
            print("-" * 40 + "\n")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n👋 GestFlow stopped")