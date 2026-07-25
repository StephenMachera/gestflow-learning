# ==========================================
# GESTFLOW VSCODE INJECTOR
# ==========================================
# Receives VSCode state from transfer packet
# Opens VSCode at exact file, line, column
# ==========================================
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_05_receiver_engine.app_launcher import open_vscode

def inject_vscode_state(state):
    """
    Opens VSCode at exact position from transfer packet.

    State contains:
      filePath    → absolute path to file
      cursorLine  → line number to jump to
      cursorColumn→ column number
      gitBranch   → branch (informational for now)
      projectName → project name
    """
    file_path   = state.get('filePath')
    cursor_line = state.get('cursorLine', 1)
    git_branch  = state.get('gitBranch')
    project     = state.get('projectName')

    print(f"\n💻 VSCode State Injection:")
    print(f"   File    : {file_path}")
    print(f"   Line    : {cursor_line}")
    print(f"   Branch  : {git_branch}")
    print(f"   Project : {project}")

    if not file_path:
        print("⚠️  No file path in state")
        return False

    # Resolve to absolute path in case extension returned relative path
    file_path = os.path.abspath(file_path)
    print(f"   Resolved : {file_path}")

    # Try opening directly — skip the exists check
    # VSCode handles missing files gracefully
    success = open_vscode(file_path, cursor_line)

    if success:
        print(f"✅ VSCode jumped to line {cursor_line}")
        if git_branch:
            print(f"   Branch: {git_branch}")

    return success

# ── Test block ──
if __name__ == "__main__":
    print("💻 VSCode Injector Test")
    print("=" * 40)

    test_state = {
        'filePath'    : '/home/user/gestflow/main.py',
        'cursorLine'  : 42,
        'cursorColumn': 8,
        'gitBranch'   : 'dev-branch',
        'projectName' : 'gestflow-learning'
    }

    inject_vscode_state(test_state)
