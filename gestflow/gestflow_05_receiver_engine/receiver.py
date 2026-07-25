# ==========================================
# GESTFLOW RECEIVER ENGINE
# ==========================================
# Single responsibility:
#   → Receive validated packet from Phase 4
#   → Route to correct injector
#   → Resume content on this device
# ==========================================
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestflow_05_receiver_engine.injectors.vscode_injector  import inject_vscode_state
from gestflow_05_receiver_engine.injectors.browser_injector import inject_browser_state
from gestflow_05_receiver_engine.injectors.vlc_injector     import inject_vlc_state

# ── Injector registry ──
# Maps content type to injector function
# Adding new content type = one line here
INJECTOR_REGISTRY = {
    'code'   : inject_vscode_state,
    'browser': inject_browser_state,
    'video'  : inject_vlc_state,
    'audio'  : inject_vlc_state,   # VLC handles audio too
}

def handle_received_packet(packet):
    """
    Master handler — called by Phase 4 transfer_server
    when a valid packet arrives.

    Routes to correct injector based on content type.
    This replaces the placeholder in main.py.

    Usage in main.py:
        from phase_5_receiver_engine.receiver import handle_received_packet
        register_packet_handler(handle_received_packet)
    """
    content = packet.get('content')
    content_type = content.get('contentType')
    state        = content.get('state', {})
    source       = packet.get('sourcePeer', {}).get('name', 'Unknown')
    packet_id    = packet.get('packetId')

    print(f"\n{'=' * 40}")
    print(f"📥 CONTENT TRANSFER RECEIVED")
    print(f"{'=' * 40}")
    print(f"   From      : {source}")
    print(f"   Type      : {content_type}")
    print(f"   Packet ID : {packet_id}")

    # Find correct injector
    injector = INJECTOR_REGISTRY.get(content_type)
    
    if not injector:
        print(f"⚠️  No injector for content type: '{content_type}'")
        print(f"   Raw state: {json.dumps(state, indent=6)}")
        return False
    # Run injector
    print(f"\n🚀 Resuming {content_type} on this device...")
    success = injector(state)

    if success:
        print(f"\n✅ Content resumed successfully!")
        print(f"   {content_type} from {source} is now live on this device")
    else:
        print(f"\n⚠️  Could not resume {content_type}")
        print(f"   Check that the required app is installed")

    print(f"{'=' * 40}\n")
    return success



# ── Test block ──
if __name__ == "__main__":
    print("📥 GestFlow Receiver Engine Test")
    print("=" * 40)

    # Test 1 — VSCode packet
    print("\n💻 Test 1 — VSCode transfer:")
    vscode_packet = {
        "packetId"  : "TEST001",
        "sourcePeer": {"name": "Desktop-PC"},
        "content"   : {
            "contentType": "code",
            "state": {
                "filePath"  : os.path.abspath(__file__),
                "cursorLine": 10,
                "gitBranch" : "dev-branch",
                "projectName": "gestflow-learning"
            }
        }
    }
    handle_received_packet(vscode_packet)

    # Test 2 — Browser packet
    print("\n🌐 Test 2 — Browser transfer:")
    browser_packet = {
        "packetId"  : "TEST002",
        "sourcePeer": {"name": "ThinkPad-X280"},
        "content"   : {
            "contentType": "browser",
            "state": {
                "url"      : "https://github.com/StephenMachera/gestflow",
                "pageTitle": "StephenMachera/gestflow"
            }
        }
    }
    handle_received_packet(browser_packet)

    # Test 3 — Unknown content type
    print("\n❓ Test 3 — Unknown content type:")
    unknown_packet = {
        "packetId"  : "TEST003",
        "sourcePeer": {"name": "Android-Phone"},
        "content"   : {
            "contentType": "spotify",
            "state"      : {"trackName": "Kama ni dini"}
        }
    }
    handle_received_packet(unknown_packet)