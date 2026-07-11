# ==========================================
# GESTFLOW VSCODE ADAPTER
# ==========================================
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from browser_bridge_server import is_vscode_connected, request_vscode_state


def _parse_from_title(window_title):
    """
    Fallback — extract filename and project from window title.
    Format: "● filename.py - project-name - Visual Studio Code"
    """
    if not window_title:
        return None, None

    # Remove unsaved indicator (●) and VSCode suffix
    cleaned = re.sub(r'^●\s*', '', window_title)
    cleaned = re.sub(r'\s*-\s*Visual Studio Code$', '', cleaned).strip()

    parts = [p.strip() for p in cleaned.split(' - ')]

    filename    = parts[0] if len(parts) > 0 else None
    projectname = parts[1] if len(parts) > 1 else None

    return filename, projectname


def get_vscode_state(window_title, app_name=None):
    """
    Gets full VSCode state via GestFlow VSCode extension.
    Falls back to window title parsing if extension not connected.
    """

    # Try extension first — full state
    if is_vscode_connected():
        state = request_vscode_state(timeout=3)
        if state:
            return {
                'dynamicType': 'code',
                'state': {
                    'filePath'    : state.get('filePath'),
                    'fileName'    : state.get('fileName'),
                    'language'    : state.get('language'),
                    'cursorLine'  : state.get('cursorLine'),
                    'cursorColumn': state.get('cursorColumn'),
                    'projectName' : state.get('projectName'),
                    'gitBranch'   : state.get('gitBranch'),
                    'isUnsaved'   : state.get('isUnsaved'),
                    'note'        : 'v1 — full state via GestFlow VSCode extension'
                }
            }

    # Fallback — window title only
    filename, projectname = _parse_from_title(window_title)

    return {
        'dynamicType': 'code',
        'state': {
            'filePath'    : filename,
            'fileName'    : filename,
            'language'    : None,
            'cursorLine'  : None,
            'cursorColumn': None,
            'projectName' : projectname,
            'gitBranch'   : None,
            'isUnsaved'   : None,
            'note'        : 'fallback — install GestFlow VSCode extension for full state'
        }
    }


# ── Test block ──
if __name__ == "__main__":
    import json
    import sys
    import time
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("💻 GestFlow VSCode Adapter Test")
    print("=" * 40)

    if is_vscode_connected():
        print("✅ VSCode extension connected")
        state = request_vscode_state()
        print("\n📦 VSCode State:")
        print(json.dumps(state, indent=4))
    else:
        print("⚠️  VSCode extension not connected")
        print("   Testing window title fallback...\n")
        title = "● main.py - gestflow-learning - Visual Studio Code"
        result = get_vscode_state(title)
        print("📦 Fallback State:")
        print(json.dumps(result, indent=4))