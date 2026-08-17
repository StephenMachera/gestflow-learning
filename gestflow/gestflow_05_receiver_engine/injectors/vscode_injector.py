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
    Opens VSCode at exact position.
    Handles three scenarios:
      1. File exists locally at original path
      2. File found locally by search
      3. File not found — use embedded content from sender
    """
    file_path      = state.get('filePath')
    cursor_line    = state.get('cursorLine', 1)
    git_branch     = state.get('gitBranch')
    project_name   = state.get('projectName')
    file_content   = state.get('fileContent')      # ← embedded content
    file_extension = state.get('fileExtension', '.py')
    filename       = os.path.basename(file_path) if file_path else 'received_file.py'

    print(f"\n💻 VSCode State Injection:")
    print(f"   File    : {filename}")
    print(f"   Line    : {cursor_line}")
    print(f"   Branch  : {git_branch}")
    print(f"   Project : {project_name}")
    print(f"   Has embedded content: {'Yes' if file_content else 'No'}")

    if not file_path and not file_content:
        print("⚠️  No file path or content in state")
        return False

    # ── Scenario 1: File exists at original path ──
    if file_path:
        resolved = os.path.abspath(file_path)
        if os.path.exists(resolved):
            print(f"✅ Scenario 1: File found at original path")
            return open_vscode(resolved, cursor_line)

    # ── Scenario 2: Search locally by filename ──
    print(f"🔍 Scenario 2: Searching locally...")
    local_path = _find_file_locally(filename, project_name)
    if local_path:
        print(f"✅ Scenario 2: Found locally at {local_path}")
        return open_vscode(local_path, cursor_line)

    # ── Scenario 3: Use embedded file content ──
    if file_content:
        print(f"📥 Scenario 3: Using embedded file content from sender")

        # Save to a GestFlow temp folder
        temp_dir = os.path.join(
            os.path.expanduser('~'),
            '.gestflow',
            'received_files'
        )
        os.makedirs(temp_dir, exist_ok=True)

        # Save with original filename
        temp_path = os.path.join(temp_dir, filename)

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

            print(f"✅ File saved to: {temp_path}")
            print(f"   Opening VSCode at line {cursor_line}")

            success = open_vscode(temp_path, cursor_line)

            if success:
                print(f"\n💡 Note: This is a copy of the file from the sender.")
                print(f"   Original location: {file_path}")
                if git_branch:
                    print(f"   From branch: {git_branch}")

            return success

        except Exception as e:
            print(f"⚠️  Could not save temp file: {e}")

    # ── Scenario 4: Nothing worked — open VSCode empty ──
    print(f"\n⚠️  Could not find or receive file")
    print(f"   Opening VSCode without file")
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