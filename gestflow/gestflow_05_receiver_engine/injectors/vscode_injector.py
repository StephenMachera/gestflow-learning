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


def _find_file_locally(filename, project_name=None):
    """
    Searches for a file on the local machine by name.
    Optionally narrows search to a specific project folder.

    Works cross-platform — handles Linux paths arriving on Windows
    and Windows paths arriving on Linux.

    Returns absolute local path or None if not found.
    """
    import platform
    os_name = platform.system()

    print(f"🔍 Searching locally for: {filename}")
    if project_name:
        print(f"   In project: {project_name}")

    # ── Define search roots per OS ──
    if os_name == 'Windows':
        search_roots = [
            os.path.expanduser('~\\Documents'),
            os.path.expanduser('~\\Desktop'),
            os.path.expanduser('~\\Downloads'),
            os.path.expanduser('~'),
            'C:\\Users',
        ]
    elif os_name == 'Darwin':  # Mac
        search_roots = [
            os.path.expanduser('~/Documents'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~'),
        ]
    else:  # Linux
        search_roots = [
            os.path.expanduser('~/Documents'),
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Downloads'),
            os.path.expanduser('~'),
        ]

    best_match    = None
    project_match = None

    for root in search_roots:
        if not os.path.exists(root):
            continue

        for dirpath, dirnames, filenames in os.walk(root):

            # Skip hidden folders and common noise
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith('.')
                and d not in ['node_modules', '__pycache__',
                              '.git', '.venv', 'venv', 'env',
                              'site-packages']
            ]

            if filename in filenames:
                full_path = os.path.join(dirpath, filename)

                # Best case — file is inside the correct project folder
                if project_name and project_name.lower() in dirpath.lower():
                    project_match = full_path
                    print(f"✅ Found in project: {full_path}")
                    return full_path   # perfect match — return immediately

                # Store as fallback
                if not best_match:
                    best_match = full_path
                    print(f"   Candidate: {full_path}")

    if best_match:
        print(f"✅ Best match found: {best_match}")
        return best_match

    print(f"❌ File not found locally: {filename}")
    return None


def inject_vscode_state(state):
    """
    Opens VSCode at exact position from transfer packet.
    Handles cross-OS file path translation automatically.
    """
    file_path    = state.get('filePath')
    cursor_line  = state.get('cursorLine', 1)
    git_branch   = state.get('gitBranch')
    project_name = state.get('projectName')
    filename     = os.path.basename(file_path) if file_path else None

    print(f"\n💻 VSCode State Injection:")
    print(f"   Original path : {file_path}")
    print(f"   Filename      : {filename}")
    print(f"   Line          : {cursor_line}")
    print(f"   Branch        : {git_branch}")
    print(f"   Project       : {project_name}")

    if not file_path or not filename:
        print("⚠️  No file path in state")
        return False

    # ── Step 1: Try original path first ──
    resolved = os.path.abspath(file_path)
    if os.path.exists(resolved):
        print(f"✅ File found at original path")
        return open_vscode(resolved, cursor_line)

    # ── Step 2: Cross-OS path — search locally ──
    print(f"⚠️  File not at original path — searching locally...")
    local_path = _find_file_locally(filename, project_name)

    if local_path:
        print(f"\n✅ Opening local copy:")
        print(f"   {local_path}:{cursor_line}")
        if git_branch:
            print(f"   Branch: {git_branch}")
        return open_vscode(local_path, cursor_line)

    # ── Step 3: File not found anywhere — open VSCode with info ──
    print(f"\n⚠️  File not found on this device")
    print(f"   Filename : {filename}")
    print(f"   Project  : {project_name}")
    print(f"   Line     : {cursor_line}")
    print(f"   Branch   : {git_branch}")
    print(f"   Opening VSCode — navigate to file manually")
    return open_vscode()


# ── Test block ──
if __name__ == "__main__":
    print("💻 VSCode Cross-Platform Injector Test")
    print("=" * 40)

    # Simulate receiving a Linux path on Windows
    test_state = {
        'filePath'   : '/home/stephen/gestflow/gestflow-learning/gestflow/gestflow_02_content_engine/main.py',
        'cursorLine' : 296,
        'gitBranch'  : 'main',
        'projectName': 'gestflow-learning'
    }

    inject_vscode_state(test_state)