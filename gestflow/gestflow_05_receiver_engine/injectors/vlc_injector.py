# ==========================================
# GESTFLOW VLC INJECTOR
# ==========================================
# Receives video state from transfer packet
# Opens VLC and seeks to exact timestamp
# ==========================================
import os
import sys
import subprocess
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_05_receiver_engine.app_launcher import open_vlc

def inject_vlc_state(state):
    """
    Opens VLC at exact timestamp from transfer packet.

    State contains:
      filePath  → path to video file
      timestamp → seconds into the video
      volume    → volume level
    """
    file_path = state.get('filePath')
    timestamp = state.get('timestamp', 0)
    volume    = state.get('volume', 100)

    print(f"\n🎬 VLC State Injection:")
    print(f"   File      : {file_path}")
    print(f"   Timestamp : {timestamp}s")
    print(f"   Volume    : {volume}%")

    if not file_path:
        print("⚠️  No file path in state")
        return False

    # VLC supports --start-time flag for seeking
    # This is the cleanest way to open at a timestamp
    try:
        cmd = [
            'vlc',
            file_path,
            f'--start-time={timestamp}',
            f'--volume={volume}'
        ]
        subprocess.Popen(cmd)
        print(f"✅ VLC opened at {timestamp}s")
        return True

    except FileNotFoundError:
        print("⚠️  VLC not found — please install VLC")
        return False
    except Exception as e:
        print(f"⚠️  Could not open VLC: {e}")
        return False


# ── Test block ──
if __name__ == "__main__":
    print("🎬 VLC Injector Test")
    print("=" * 40)

    test_state = {
        'filePath' : '/home/user/videos/inception.mp4',
        'timestamp': 2745,
        'volume'   : 80
    }

    inject_vlc_state(test_state)