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
    Cross-platform — handles Windows PATH issues.
    """
    import platform
    os_name = platform.system()

    # ── Find VSCode executable ──
    vscode_commands = ['code']

    if os_name == 'Windows':
        # Common Windows VSCode locations
        import os
        possible_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''),
                        'Programs', 'Microsoft VS Code', 'bin', 'code.cmd'),
            os.path.join(os.environ.get('PROGRAMFILES', ''),
                        'Microsoft VS Code', 'bin', 'code.cmd'),
            'code.cmd',
            'code',
        ]
        vscode_commands = possible_paths

    # Try each command until one works
    for cmd in vscode_commands:
        try:
            args = [cmd, '--reuse-window']

            if file_path and line:
                args += ['--goto', f"{file_path}:{line}"]
            elif file_path:
                args += [file_path]

            subprocess.Popen(args)
            print(f"✅ VSCode opened via: {cmd}")
            return True

        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️  {cmd} failed: {e}")
            continue

    print("⚠️  VSCode not found — trying to open via system default...")

    # Last resort — open with system default
    try:
        if os_name == 'Windows':
            os.startfile(file_path or '.')
        elif os_name == 'Darwin':
            subprocess.Popen(['open', '-a', 'Visual Studio Code',
                             file_path or '.'])
        else:
            subprocess.Popen(['xdg-open', file_path or '.'])
        return True
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
    
def open_vlc(file_path=None, timestamp=0):
    """Opens VLC — cross platform."""
    from gestflow_05_receiver_engine.injectors.vlc_injector import (
        _find_vlc_executable,
        _open_vlc
    )

    vlc_exe = _find_vlc_executable()
    if not vlc_exe:
        print("❌ VLC not found")
        return False

    if file_path:
        return _open_vlc(vlc_exe, file_path, timestamp, 100)

    try:
        subprocess.Popen([vlc_exe])
        return True
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