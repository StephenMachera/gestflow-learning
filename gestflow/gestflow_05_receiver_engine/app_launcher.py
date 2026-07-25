# ==========================================
# GESTFLOW APP LAUNCHER
# ==========================================
# Single responsibility:
#   → Open the correct app for each content type
#   → Cross platform (Linux, Windows, Mac)
# ==========================================

import platform
import subprocess
import os
import sys

def get_os():
    """Returns current OS name."""
    system = platform.system()
    return{
        'Linux':'linux',
        'Windows':'windows',
        'Darwin':'darwin'
    }.get(system, 'linux')

OS = get_os()

# ══════════════════════════════════════════
# APP LAUNCHERS
# ══════════════════════════════════════════

def open_vscode(file_path=None, line=None):
    """
    Opens VSCode at specific file and line.
    Uses --reuse-window to open in existing VSCode instance.
    """
    try:
        cmd = ['code', '--reuse-window']  # ← add this flag

        if file_path and line:
            cmd += ['--goto', f"{file_path}:{line}"]
        elif file_path:
            cmd += [file_path]

        subprocess.Popen(cmd)
        print(f"✅ VSCode opened: {file_path}:{line}")
        return True

    except FileNotFoundError:
        print("⚠️  VSCode CLI not found")
        return False
    except Exception as e:
        print(f"⚠️  Could not open VSCode: {e}")
        return False

def open_browser(url):
    """
    Opens URL in default browser.
    Works on all platforms.
    """
    if not url:
        print("⚠️  No URL provided")
        return False
    
    try:
        import webbrowser
        webbrowser.open(url)
        print(f"✅ Browser opened: {url}")
        return True

    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")
        return False
    
def open_vlc(file_path = None, timestamp = 0):
    """
    Opens VLC with a file at a specific timestamp.
    """
    if not file_path:
        print("⚠️  No file path provided")
        return False
    try:
        if OS == 'linux':
            cmd = ['vlc', file_path]
        elif OS == 'windows':
            cmd = ['vlc', file_path]
        elif OS == 'mac':
            cmd = ['open', '-a', 'VLC', file_path]
        else:
            cmd = ['vlc', file_path]
        
        subprocess.Popen(cmd)
        print(f"✅ VLC opened: {file_path}")
        return True

    except FileNotFoundError:
        print("⚠️  VLC not found — please install VLC")
        return False
    except Exception as e:
        print(f"⚠️  Could not open VLC: {e}")
        return False
    
def open_file_manager(path=None):
    """
    Opens file manager at a specific path.
    """
    try:
        if OS == 'linux':
            cmd = ['xdg-open', path or os.path.expanduser('~')]
        elif OS == 'windows':
            cmd = ['explorer', path or os.path.expanduser('~')]
        elif OS == 'mac':
            cmd = ['open', path or os.path.expanduser('~')]
        subprocess.Popen(cmd)
        print(f"✅ File manager opened: {path}")
        return True

    except Exception as e:
        print(f"⚠️  Could not open file manager: {e}")
        return False

def get_launcher(content_type):
    """
    Returns the correct launcher function for a content type.
    Used by receiver.py to open the right app.
    """
    launchers = {
        'code'   : open_vscode,
        'browser': open_browser,
        'video'  : open_vlc,
        'audio'  : open_vlc,
        'file'   : open_file_manager,
    }
    return launchers.get(content_type)

# ── Test block ──
if __name__ == "__main__":
    print("🚀 GestFlow App Launcher Test")
    print("=" * 40)
    print(f"OS: {OS}\n")

    print("Testing browser launcher...")
    open_browser("https://github.com/StephenMachera/gestflow")

    print("\nTesting VSCode launcher...")
    open_vscode("/home/user/test.py", line=42)