import psutil
import re

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac')
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm')


def is_vlc_running():
    """
    Checks if VLC process is currently running.
    Uses psutil — works on all platforms.
    """
    for process in psutil.process_iter(['name']):
        try:
            if 'vlc' in process.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def parse_filename_from_title(title):
    """
    Extracts filename from VLC window title.

    VLC title formats:
      "inception.mp4 - VLC media player"
      "My Movie.mkv - VLC media player"
      "VLC media player"  ← no file open

    window title comes from screen_reader.py
    this function only handles VLC specific parsing
    """
    if not title:
        return None

    # Remove " - VLC media player" suffix
    cleaned = re.sub(r'\s*-\s*VLC media player.*$', '', title).strip()

    # VLC open but no file loaded
    if not cleaned or cleaned.lower() == 'vlc media player':
        return None

    return cleaned


def detect_content_type(filename):
    """
    Determines video or audio from file extension.
    """
    if not filename:
        return 'video'

    lower = filename.lower()

    if lower.endswith(AUDIO_EXTENSIONS):
        return 'audio'
    return 'video'


def get_vlc_state(window_title,app_name):
    """
    Builds GestFlow state from VLC window title.

    window_title comes from screen_reader.get_active_content()
    This function never calls xdotool or any OS API directly.

    Returns state dict or None if VLC not running or no file loaded.
    """

    # Step 1 — confirm VLC is actually running
    if not is_vlc_running():
        return None

    # Step 2 — parse filename from title screen_reader already fetched
    filename = parse_filename_from_title(window_title)
    if not filename:
        return {
            "dynamicType": "video",
            "state": {
                "filePath": "Unknown",
                "timestamp": 0,
                "volume": 100,
                "isPlaying": False,
                "note": "VLC open but no file loaded"
            }
        }

    # Step 3 — detect content type
    content_type = detect_content_type(filename)

    # Step 4 — return clean state object
    return {
        "dynamicType": content_type,
        "state": {
            "filePath": filename,
            "timestamp": 0,
            "volume": 100,
            "isPlaying": True,
            "note": "v1 — exact timestamp coming in v2"
        }
    }


# ── Test block ──
if __name__ == "__main__":
    import json
    import sys
    import os

    # Add parent folder to path so we can import screen_reader
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from screen_reader import get_active_content

    print("🎬 GestFlow VLC Adapter v1")
    print("=" * 40)

    # Get active content from screen_reader — single source of truth
    content = get_active_content()

    if not content:
        print("❌ Could not read active window")
        exit()

    if content['app'] != 'vlc':
        print(f"❌ Active app is '{content['app']}' not VLC")
        print("   Click on VLC window first then run again")
        exit()

    print(f"✅ VLC detected via screen_reader")
    print(f"📺 Window title : {content['windowTitle']}")

    # Pass window title to adapter
    state = get_vlc_state(content['windowTitle'])
    print(f"\n📦 GestFlow State Packet:")
    print(json.dumps(state, indent=4))