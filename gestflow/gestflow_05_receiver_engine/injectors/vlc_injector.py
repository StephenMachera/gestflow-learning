import base64
import os
import subprocess
import platform
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def _find_vlc_executable():
    """Finds VLC on any OS."""
    os_name = platform.system()

    if os_name == 'Windows':
        paths = [
            r'C:\Program Files\VideoLAN\VLC\vlc.exe',
            r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
            os.path.join(os.environ.get('PROGRAMFILES', ''),
                        'VideoLAN', 'VLC', 'vlc.exe'),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    elif os_name == 'Darwin':
        mac_path = '/Applications/VLC.app/Contents/MacOS/VLC'
        return mac_path if os.path.exists(mac_path) else None

    else:
        return 'vlc'


def _save_received_file(file_data_b64, filename):
    """
    Decodes base64 file data and saves to local machine.
    Saves to ~/.gestflow/received_files/
    Returns the saved file path.
    """
    try:
        # Create received files directory
        receive_dir = os.path.join(
            os.path.expanduser('~'),
            '.gestflow',
            'received_files'
        )
        os.makedirs(receive_dir, exist_ok=True)

        # Save file
        save_path = os.path.join(receive_dir, filename)

        print(f"💾 Saving received file...")
        raw_bytes = base64.b64decode(file_data_b64)

        with open(save_path, 'wb') as f:
            f.write(raw_bytes)

        size_mb = len(raw_bytes) / 1024 / 1024
        print(f"✅ File saved: {save_path}")
        print(f"   Size: {size_mb:.1f}MB")

        return save_path

    except Exception as e:
        print(f"❌ Could not save file: {e}")
        return None


def _find_video_locally(filename):
    """Searches for video file on local machine."""
    os_name = platform.system()

    if os_name == 'Windows':
        roots = [
            os.path.expanduser('~\\Videos'),
            os.path.expanduser('~\\Desktop'),
            os.path.expanduser('~\\Downloads'),
        ]
    else:
        roots = [
            os.path.expanduser('~/Videos'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Downloads'),
        ]

    for root in roots:
        if not os.path.exists(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            if filename in filenames:
                return os.path.join(dirpath, filename)
    return None


def _open_vlc(vlc_exe, file_path, timestamp, volume):
    """Opens VLC at file and timestamp."""
    try:
        cmd = [
            vlc_exe,
            file_path,
            f'--start-time={timestamp}',
            f'--volume={volume}'
        ]
        subprocess.Popen(cmd)
        print(f"✅ VLC opened at {timestamp}s")
        return True
    except Exception as e:
        print(f"⚠️  Could not open VLC: {e}")
        return False


def inject_vlc_state(state):
    """
    Opens VLC at exact timestamp.
    Handles four scenarios:

    1. File at original path → open directly
    2. File found locally by search → open at timestamp
    3. File embedded in packet → save then open
    4. Nothing works → open VLC empty with instructions
    """
    file_path  = state.get('filePath')
    timestamp  = state.get('timestamp', 0)
    volume     = state.get('volume', 100)
    filename   = state.get('fileName') or (
        os.path.basename(file_path) if file_path else None
    )
    file_data  = state.get('fileData')    # base64 content from sender
    embedded   = state.get('embedded', False)

    print(f"\n🎬 VLC State Injection:")
    print(f"   File      : {filename}")
    print(f"   Timestamp : {timestamp}s")
    print(f"   Volume    : {volume}%")
    print(f"   Embedded  : {embedded}")

    # Find VLC
    vlc_exe = _find_vlc_executable()
    if not vlc_exe:
        print("❌ VLC not installed")
        print("   Download from: https://www.videolan.org/vlc/")
        return False

    # ── Scenario 1: File at original path ──
    if file_path and os.path.exists(file_path):
        print(f"✅ Scenario 1: File at original path")
        return _open_vlc(vlc_exe, file_path, timestamp, volume)

    # ── Scenario 2: Search locally ──
    if filename:
        print(f"🔍 Scenario 2: Searching locally...")
        local_path = _find_video_locally(filename)
        if local_path:
            print(f"✅ Scenario 2: Found locally")
            return _open_vlc(vlc_exe, local_path, timestamp, volume)

    # ── Scenario 3: Use embedded file data ──
    if file_data and filename:
        print(f"📥 Scenario 3: Using embedded file from sender")
        saved_path = _save_received_file(file_data, filename)
        if saved_path:
            print(f"✅ Scenario 3: File saved — opening VLC")
            return _open_vlc(vlc_exe, saved_path, timestamp, volume)

    # ── Scenario 4: Open VLC empty ──
    print(f"\n⚠️  Scenario 4: Video not available")
    print(f"   File: {filename}")
    print(f"   Please open the file manually")
    print(f"   Then seek to: {timestamp}s ({timestamp // 60}m {timestamp % 60}s)")
    try:
        subprocess.Popen([vlc_exe])
        return True
    except Exception as e:
        print(f"❌ Could not open VLC: {e}")
        return False