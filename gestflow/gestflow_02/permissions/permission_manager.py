# ==========================================
# GESTFLOW PERMISSION MANAGER
# ==========================================
# Single responsibility:
#   → Ask user once per app permission
#   → Save the answer
#   → Never ask again
#
# What this file does NOT do:
#   ❌ Detect which app is running (screen_reader)
#   ❌ Route to adapters (content_classifier)
#   ❌ Read app state (adapters)
# ==========================================

import json
import os
import subprocess
import time

# ── Storage ──
GESTFLOW_DIR     = os.path.expanduser('~/.gestflow')
PERMISSIONS_FILE = os.path.join(GESTFLOW_DIR, 'permissions.json')

# ── Browser executables to try on relaunch ──
# Ordered by most common first
BROWSER_EXECUTABLES = [
    'google-chrome',
    'google-chrome-stable',
    'brave-browser',
    'chromium',
    'chromium-browser',
    'microsoft-edge',
    'microsoft-edge-stable',
]

# ── Permission definitions ──
# title   → what user sees in popup title bar
# message → friendly explanation — no technical words
# setup_fn → function called silently after user clicks Allow
PERMISSION_DEFINITIONS = {
    'browser': {
        'title': 'GestFlow — Browser Access',
        'message': (
            "GestFlow needs access to your browser tabs.\n\n"
            "This lets you throw any browser tab to another "
            "device with a single hand gesture.\n\n"
            "Your browser will restart briefly and all your "
            "tabs will be restored automatically.\n\n"
            "Allow browser access?"
        ),
        'setup_fn': '_setup_browser_permission'
    },
    'spotify': {
        'title': 'GestFlow — Music Access',
        'message': (
            "GestFlow needs access to Spotify.\n\n"
            "This lets you throw your current song to another "
            "device and it continues from the same position.\n\n"
            "You will be asked to log in to Spotify once.\n\n"
            "Allow music access?"
        ),
        'setup_fn': '_setup_spotify_permission'
    },
    'vscode': {
        'title': 'GestFlow — Code Editor Access',
        'message': (
            "GestFlow needs access to your code editor.\n\n"
            "This lets you throw your current file to another "
            "device and it opens at the exact same line.\n\n"
            "Allow code editor access?"
        ),
        'setup_fn': '_setup_vscode_permission'
    }
}


# ══════════════════════════════════════════
# PERMISSIONS FILE MANAGEMENT
# ══════════════════════════════════════════

def _load_permissions():
    """
    Reads saved permissions from disk.
    Returns empty dict if file does not exist yet.
    Never crashes — returns {} on any error.
    """
    try:
        if os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load permissions: {e}")
    return {}


def _save_permission(permission_name):
    """
    Saves a granted permission to disk.
    Creates ~/.gestflow/ automatically if it does not exist.
    Called once after user clicks Allow — never again.
    """
    try:
        os.makedirs(GESTFLOW_DIR, exist_ok=True)

        permissions = _load_permissions()
        permissions[permission_name] = {
            'granted'   : True,
            'granted_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        with open(PERMISSIONS_FILE, 'w') as f:
            json.dump(permissions, f, indent=2)

    except Exception as e:
        print(f"Warning: Could not save permission: {e}")


def has_permission(permission_name):
    """
    Checks if user already granted a specific permission.

    Returns True  → already granted, skip popup entirely
    Returns False → first time, show popup
    """
    permissions = _load_permissions()
    entry = permissions.get(permission_name, {})
    return entry.get('granted', False)


def revoke_permission(permission_name):
    """
    Removes a saved permission.
    Used for testing or if user wants to reset GestFlow.
    After revoke, next access will show popup again.
    """
    try:
        permissions = _load_permissions()
        if permission_name in permissions:
            del permissions[permission_name]
            with open(PERMISSIONS_FILE, 'w') as f:
                json.dump(permissions, f, indent=2)
            print(f"✅ Permission '{permission_name}' revoked")
        else:
            print(f"⚠️  Permission '{permission_name}' was not set")
    except Exception as e:
        print(f"Warning: Could not revoke permission: {e}")


def revoke_all_permissions():
    """
    Clears all saved permissions.
    Used for full GestFlow reset.
    """
    try:
        if os.path.exists(PERMISSIONS_FILE):
            os.remove(PERMISSIONS_FILE)
            print("✅ All permissions revoked")
        else:
            print("ℹ️  No permissions file found")
    except Exception as e:
        print(f"Warning: Could not clear permissions: {e}")


# ══════════════════════════════════════════
# POPUP DIALOG
# ══════════════════════════════════════════

def _show_permission_dialog(title, message):
    """
    Shows a friendly permission popup to the user.
    Uses tkinter for now — Phase 6 Electron UI replaces this.

    Returns True  → user clicked Allow
    Returns False → user clicked Deny or closed dialog
    """
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()                    # hide empty tkinter window
        root.lift()                        # bring dialog to front
        root.attributes('-topmost', True)  # stay on top of other windows

        result = messagebox.askyesno(
            title,
            message,
            icon='question'
        )

        root.destroy()
        return result

    except ImportError:
        # tkinter not available
        # Auto-grant for headless/server environments
        print(f"⚠️  tkinter not available — auto-granting: {title}")
        return True

    except Exception as e:
        print(f"Warning: Dialog error: {e}")
        return False


# ══════════════════════════════════════════
# SETUP FUNCTIONS
# Called silently after user clicks Allow
# Each function handles one app's setup
# ══════════════════════════════════════════

def _get_browser_executable(browser_name=None):
    """
    Finds the browser executable path.

    If browser_name passed from content_classifier — try that first.
    Falls back to checking all known browser executables.
    Never scans processes — that is screen_reader's job.
    """
    # Try the specific browser name first if provided
    candidates = []
    if browser_name:
        candidates.append(browser_name)
    candidates.extend(BROWSER_EXECUTABLES)

    for exe in candidates:
        try:
            result = subprocess.run(
                ['which', exe],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return exe
        except Exception:
            continue

    return None


def _setup_browser_permission(browser_name=None):
    """
    Silently relaunches the browser with remote debugging enabled.
    Receives browser_name from content_classifier via ensure_permission.
    Never detects which browser is running — that is screen_reader's job.

    Steps:
      1. Find browser executable
      2. Close browser using pkill (by name passed in)
      3. Wait for full close
      4. Relaunch with --remote-debugging-port=9222
      5. Wait for browser to start
    """
    print("🔄 Setting up browser access...")

    # Find executable — use passed name first, then scan known executables
    browser_exe = _get_browser_executable(browser_name)
    if not browser_exe:
        print("⚠️  Could not find browser executable to relaunch")
        return False

    # Close browser by executable name
    # pkill is safer than psutil here — no process scanning needed
    try:
        subprocess.run(
            ['pkill', '-f', browser_exe],
            capture_output=True
        )
    except Exception as e:
        print(f"Warning: Could not close browser: {e}")

    # Wait for browser to fully close
    time.sleep(2)

    # Relaunch with remote debugging port
    # --restore-last-session brings back all user tabs automatically
    try:
        subprocess.Popen([
            browser_exe,
            '--remote-debugging-port=9222',
            '--restore-last-session'
        ])
    except Exception as e:
        print(f"⚠️  Could not relaunch browser: {e}")
        return False

    # Wait for browser to fully start before adapter tries to connect
    time.sleep(3)

    print("✅ Browser relaunched with GestFlow access")
    return True


def _setup_spotify_permission(app_name=None):
    """
    Placeholder for Spotify OAuth setup.
    Will open Spotify login page once during setup.
    Implemented when building spotify_adapter.
    """
    print("🎵 Spotify permission setup — coming in v2")
    return True


def _setup_vscode_permission(app_name=None):
    """
    VSCode CLI is always available — no special setup needed.
    Permission is saved as a formality so user is informed.
    """
    print("💻 VSCode access enabled")
    return True


# ══════════════════════════════════════════
# MAIN ENTRY POINT
# This is the ONLY function adapters call
# ══════════════════════════════════════════

def ensure_permission(permission_name, app_name=None):
    """
    The single function every adapter calls.

    Arguments:
      permission_name → 'browser', 'spotify', 'vscode'
      app_name        → passed from content_classifier
                        e.g. 'google-chrome', 'brave-browser'
                        permission_manager never detects this itself

    Flow:
      1. Already granted → return True immediately, no popup
      2. Not granted     → show friendly popup
      3. User clicks Allow → run silent setup → save → return True
      4. User clicks Deny  → return False → adapter uses title fallback

    Usage in any adapter:
      from permissions.permission_manager import ensure_permission

      def get_browser_state(window_title, app_name=None):
          if not ensure_permission('browser', app_name=app_name):
              return fallback_from_title(window_title)
          return get_state_via_cdp()
    """

    # Already granted — skip everything, return immediately
    if has_permission(permission_name):
        return True

    # Unknown permission type
    definition = PERMISSION_DEFINITIONS.get(permission_name)
    if not definition:
        print(f"⚠️  Unknown permission: '{permission_name}'")
        return False

    # Show friendly popup — user sees this exactly once
    granted = _show_permission_dialog(
        definition['title'],
        definition['message']
    )

    if not granted:
        print(f"ℹ️  User declined '{permission_name}' permission")
        return False

    # Run silent setup function for this permission type
    setup_fn_name = definition['setup_fn']
    setup_fn = globals().get(setup_fn_name)

    if setup_fn:
        try:
            # Pass app_name if setup function accepts it
            success = setup_fn(app_name)
        except TypeError:
            # Setup function takes no arguments
            success = setup_fn()

        if not success:
            print(f"⚠️  Setup failed for '{permission_name}'")
            return False

    # Save to disk — never ask again
    _save_permission(permission_name)
    print(f"✅ Permission '{permission_name}' granted and saved")
    return True


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("🔐 GestFlow Permission Manager")
    print("=" * 40)

    # Show current saved permissions
    print("\n📋 Current saved permissions:")
    permissions = _load_permissions()
    if permissions:
        for name, data in permissions.items():
            granted_at = data.get('granted_at', 'unknown')
            print(f"   {name}: granted at {granted_at}")
    else:
        print("   None saved yet")

    # Reset flag for testing
    if '--reset' in sys.argv:
        print("\n🔄 Resetting all permissions...")
        revoke_all_permissions()
        print("Done — run again without --reset to test fresh flow")
        sys.exit(0)

    # Test ensure_permission flow
    print("\n🧪 Test 1 — first time browser permission:")
    result = ensure_permission('browser', app_name='google-chrome')
    print(f"Result: {'✅ Granted' if result else '❌ Denied'}")

    # Second call should skip popup entirely
    print("\n🧪 Test 2 — second call (should skip popup):")
    result2 = ensure_permission('browser', app_name='google-chrome')
    print(f"Result: {'✅ Skipped popup — already granted' if result2 else '❌ Denied'}")

    # Show updated permissions
    print("\n📋 Updated permissions file:")
    permissions = _load_permissions()
    print(json.dumps(permissions, indent=2))