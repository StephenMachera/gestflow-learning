import subprocess
import sys
import psutil
import os

# ==========================================================
# LINUX / UBUNTU ACTIVE WINDOW HOOKS
# ==========================================================
def get_active_window_linux():
    """
    Queries the Linux X11 window manager via xdotool 
    to fetch window properties and process name.
    """
    try:
        # Get the raw active window hex/decimal Id
        window_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode('utf-8').strip()

        # Get the Window Title Name
        windowTitle = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode('utf-8').strip()

        # Get the process ID(PID) owning this window
        pid = subprocess.check_output(['xdotool',"getwindowpid",window_id]).decode('utf-8').strip()
        pid = int(pid)

        # Use psutilto get the underlying binary system name
        process = psutil.Process(pid)
        app_name = process.name().lower()

        return{
            'app':app_name,
            'windowTitle':windowTitle,
            'pid':pid
        }
    except subprocess.CalledProcessError:
        return None
    except Exception as e:
        print(f"Error reading screen:{e}")
        return None
    
# ==========================================================
# WINDOWS OS ACTIVE WINDOW HOOKS
# ==========================================================
def get_active_window_windows():
    import win32gui
    import win32process
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        window_title = win32gui.GetWindowText(hwnd)
        _,pid = win32process.GetWindowThreadProcessId(hwnd)

        process = psutil.Process(pid)
        app_name = process.name().lower()
        # Strip .exe extension if present on Windows
        if app_name.endswith('.exe'):
            app_name = app_name[:-4]
                
        return {
            "app": app_name,
            "windowTitle": window_title,
            "pid": pid
            }
    except Exception as e:
        print(f"⚠️ Windows Screen Reader Error: {e}")
        return None

# ==========================================================
# MACOS ACTIVE WINDOW HOOKS
# ==========================================================
def get_active_window_mac():
    try:
        from AppKit import NSWorkspace
        # Query Apple Cocoa API for active frontmost application details
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not active_app:
            return None
            
        app_name = active_app.localizedName().lower()
        pid = active_app.processIdentifier()
        
        # macOS doesn't easily expose the precise focused window title without accessibility permissions,
        # so we fall back to using the App Name as a filler title if unavailable.
        window_title = app_name 
        
        return {
            "app": app_name,
            "windowTitle": window_title,
            "pid": int(pid)
        }
    except Exception as e:
        print(f"⚠️ macOS Screen Reader Error: {e}")
        return None

# ==========================================================
# THE UNIVERSAL CROSS-PLATFORM SYSTEM ENTRANCE HOOK
# ==========================================================
def get_active_content():
    """
    Detects the current host OS platform and automatically 
    routes data extraction loops to native API hooks.
    """
    if sys.platform.startswith('linux'):
        return get_active_window_linux()
    elif sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
        return get_active_window_windows()
    elif sys.platform.startswith('darwin'): # darwin is the core platform name for macOS
        return get_active_window_mac()
    else:
        print(f"❌ Host Platform system '{sys.platform}' is currently unsupported by GestFlow.")
        return None
if __name__ == "__main__":
    import time
    print("👀 Screen Reader Tester Active! Switch to VLC or Chrome now...")
    time.sleep(10) # Gives you time to click on another window to test it
    
    result = get_active_window_linux()
    print("\n📦 Captured Window Data:")
    print(result)