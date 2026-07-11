# ==========================================
# GESTFLOW — MAIN ENTRY POINT
# Run this ONE file to start everything
# ==========================================
import time
import json
import sys
from browser_bridge_server import (
    start_bridge_server,
    is_extension_connected,
    request_active_tab,
    get_connected_browsers
)
from content_classifier import classify_content
from screen_reader import get_active_content


def start_services():
    """
    Starts all GestFlow background services.
    Called once at startup.
    """
    print("🤚 GestFlow Starting...")
    print("=" * 40)

    # Start browser bridge
    print("Starting browser bridge server...")
    start_bridge_server()
    print("✅ Browser bridge ready\n")

"""
    Waits for Chrome extension to connect.
    Returns True if connected, False if timed out.
    """
def wait_for_extension(timeout=10):
    """
    Waits for Chrome extension to connect.
    Returns True if connected, False if timed out.
    """
    print("⏳ Waiting for browser extension...")
    for i in range(timeout * 2):
        if is_extension_connected():
            from browser_bridge_server import _connected_browsers
            print(f"🌐 Browser extension connected ✅")
            print(f"🔌 Connected browsers: {list(_connected_browsers.values())}")
            return True
        time.sleep(0.5)

    print("🌐 Extension not connected — fallback active\n")
    return False


def run_detection():
    """
    Runs one content detection cycle.
    In Phase 5 this will be triggered by gesture detection.
    """
    from browser_bridge_server import get_connected_browsers
    browsers = get_connected_browsers()
    print(f"🔌 Connected browsers: {browsers if browsers else 'none'}")
    print("You have 7 seconds to switch to VLC, Chrome, or VSCode...")
    print()
    time.sleep(7)

    raw_window = get_active_content()
    if not raw_window:
        print("❌ Could not detect active window")
        return

    print(f"🔍 App    : {raw_window.get('app')}")
    print(f"📋 Title  : {raw_window.get('windowTitle')}\n")

    final_state = classify_content(raw_window)

    print("📦 GestFlow Content State:")
    print("=" * 40)
    print(json.dumps(final_state, indent=4))


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
if __name__ == "__main__":

    # 1 — Start all services
    start_services()

    # 2 — Wait for extension
    wait_for_extension(timeout=10)

    # 3 — Run detection loop
    # For now runs once — Phase 5 will make this gesture triggered
    try:
        while True:
            run_detection()
            print("\nPress Ctrl+C to stop or wait for next detection...\n")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n👋 GestFlow stopped")