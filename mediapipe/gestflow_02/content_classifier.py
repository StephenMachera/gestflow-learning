# ==========================================
# GESTFLOW CONTENT CLASSIFIER
# ==========================================
import json
import os
import sys

# Add parent folder to path for adapter imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from adapters.vlc_adapter     import get_vlc_state
from adapters.browser_adapter import get_browser_state
from adapters.vscode_adapter import get_vscode_state

# ── Adapter registry ──
# Every adapter signature must be: fn(window_title, app_name=None)
# Adding a new app = one line here + one entry in app_mapping.json
ADAPTER_REGISTRY = {
    'vlc'            : get_vlc_state,
    'chrome'         : get_browser_state,
    'google-chrome'  : get_browser_state,
    'chromium'       : get_browser_state,
    'brave-browser'  : get_browser_state,
    'brave'          : get_browser_state,
    'microsoft-edge' : get_browser_state,
    'code'    : get_vscode_state,
    # 'spotify' : get_spotify_state,   ← uncomment when built
}

# ── Load app mappings once at startup ──
MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'app_mapping.json')

def load_app_mappings():
    try:
        if os.path.exists(MAPPING_FILE):
            with open(MAPPING_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"Warning: {MAPPING_FILE} not found. Using empty mapping.")
            return {}
    except Exception as e:
        print(f"Error loading app mappings: {e}")
        return {}

# Load once when module is imported — not on every call
APP_MAPPINGS = load_app_mappings()


def classify_content(window_data):
    """
    Takes window data from screen_reader.get_active_content()
    and returns a standardized GestFlow content object.

    This is the single entry point for Phase 3 and Phase 4.
    """
    if not window_data:
        return None

    app_name     = window_data.get('app')
    window_title = window_data.get('windowTitle', '')
    pid          = window_data.get('pid')

    # ── Known app ──
    if app_name in APP_MAPPINGS:
        mapping      = APP_MAPPINGS[app_name]
        content_type = mapping['contentType']
        adapter_name = mapping['adapter']
        adapter_state = {}

        # Call correct adapter
        # Pass BOTH window_title AND app_name
        # Every adapter: fn(window_title, app_name=None)
        adapter_fn = ADAPTER_REGISTRY.get(app_name)
        if adapter_fn:
            payload = adapter_fn(window_title, app_name)  # ← fixed
            if payload:
                content_type  = payload.get('dynamicType', content_type)
                adapter_state = payload.get('state', {})

        return {
            'app'         : app_name,
            'contentType' : content_type,
            'windowTitle' : window_title,
            'pid'         : pid,
            'adapter'     : adapter_name,
            'state'       : adapter_state
        }

    # ── Unknown app — graceful fallback ──
    print(f"⚠️  App '{app_name}' is untracked — add it to app_mapping.json")
    return {
        'app'         : app_name,
        'contentType' : 'unknown',
        'windowTitle' : window_title,
        'pid'         : pid,
        'adapter'     : None,
        'state'       : {}
    }


# ── Test block ──
if __name__ == "__main__":
    import json as json_lib
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from screen_reader import get_active_content

    print("🔍 GestFlow Content Classifier")
    print("=" * 40)
    print("Click on any app then run this script\n")

    window_data = get_active_content()

    if not window_data:
        print("❌ Could not detect active window")
        exit()

    print(f"Active app   : {window_data['app']}")
    print(f"Window title : {window_data['windowTitle']}")

    result = classify_content(window_data)

    print(f"\n📦 Classified Content:")
    print(json_lib.dumps(result, indent=4))