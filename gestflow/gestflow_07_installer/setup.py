#!/usr/bin/env python3
# ==========================================
# GESTFLOW INSTALLER
# ==========================================
# Cross-platform installer for GestFlow.
# Works on Linux, Windows, and Mac.
#
# Usage:
#   python setup.py
# ==========================================

import os
import sys
import json
import shutil
import platform
import subprocess
import time

# ── Configuration ──
OS_NAME      = platform.system()
HOME_DIR     = os.path.expanduser('~')
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
REPO_DIR     = os.path.dirname(BASE_DIR)

# ── GestFlow Chrome Extension ──
EXTENSION_ID = 'oniiiabboammbabpoefbbhjanedagdlf'
UPDATE_URL   = 'https://StephenMachera.github.io/gestflow-learning/extension/update.xml'

# ── Paths ──
GESTFLOW_DIR    = os.path.join(HOME_DIR, '.gestflow')
RECEIVED_DIR    = os.path.join(GESTFLOW_DIR, 'received_files')

# Fixed — Chrome extension
EXTENSION_SRC   = os.path.abspath(
    os.path.join(REPO_DIR,
                 'gestflow_03_browser_extension')
)

# Fixed — VSCode extension
VSCODE_EXT_SRC  = os.path.abspath(
    os.path.join(REPO_DIR,
                 'gestflow_03_vscode_extension')
)


# ══════════════════════════════════════════
# PRINT HELPERS
# ══════════════════════════════════════════

def print_header():
    print("\n" + "=" * 55)
    print("  🤚 GestFlow Installer v1.0")
    print("=" * 55)
    print(f"  OS      : {OS_NAME}")
    print(f"  Python  : {sys.version.split()[0]}")
    print("=" * 55)


def print_step(number, title):
    print(f"\n{'─' * 55}")
    print(f"  Step {number} — {title}")
    print(f"{'─' * 55}")


def print_ok(msg):
    print(f"  ✅ {msg}")


def print_warn(msg):
    print(f"  ⚠️  {msg}")


def print_fail(msg):
    print(f"  ❌ {msg}")


def print_info(msg):
    print(f"  ℹ️  {msg}")


# ══════════════════════════════════════════
# HELPER — RUN COMMAND
# ══════════════════════════════════════════

def run(cmd, cwd=None, shell=False):
    """
    Runs a command.
    Returns (success, output) tuple.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            shell=shell
        )
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return False, "Command not found"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════
# STEP 1 — PYTHON DEPENDENCIES
# ══════════════════════════════════════════

def install_python_dependencies():
    print_step(1, "Installing Python dependencies")

    requirements_path = os.path.join(REPO_DIR, 'requirements.txt')

    if not os.path.exists(requirements_path):
        print_fail(f"requirements.txt not found: {requirements_path}")
        return False

    print(f"  Installing from requirements.txt...")
    success, output = run([
        sys.executable, '-m', 'pip',
        'install', '-r', requirements_path,
        '--quiet'
    ])

    if success:
        print_ok("All Python dependencies installed")
        return True
    else:
        print_warn(f"Some packages failed: {output[-300:]}")
        print_info("Try manually: pip install -r requirements.txt")
        return False


# ══════════════════════════════════════════
# STEP 2 — GESTFLOW CONFIG FOLDER
# ══════════════════════════════════════════

def setup_config():
    print_step(2, "Creating GestFlow config folder")

    folders = [
        GESTFLOW_DIR,
        RECEIVED_DIR,
        os.path.join(GESTFLOW_DIR, 'logs'),
        os.path.join(GESTFLOW_DIR, 'extension'),
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print_ok(f"Created: {folder}")


# ══════════════════════════════════════════
# STEP 3 — CHROME EXTENSION
# ══════════════════════════════════════════

def install_chrome_extension():
    print_step(3, "Installing GestFlow Chrome Extension")

    policy = {
        "ExtensionInstallForcelist": [
            f"{EXTENSION_ID};{UPDATE_URL}"
        ]
    }

    if OS_NAME == 'Linux':
        _chrome_linux(policy)
    elif OS_NAME == 'Windows':
        _chrome_windows(policy)
    elif OS_NAME == 'Darwin':
        _chrome_mac(policy)

    print_ok("Chrome extension policy installed")
    print_info("Restart Chrome/Brave to activate extension")


def _chrome_linux(policy):
    """Writes Chrome policy on Linux for all browsers."""
    policy_dirs = [
        '/etc/opt/chrome/policies/managed',
        '/etc/chromium/policies/managed',
        '/etc/brave/policies/managed',
        '/etc/opt/edge/policies/managed',
    ]

    policy_json = json.dumps(policy, indent=2)

    # Write to temp file first
    tmp_file = '/tmp/gestflow_policy.json'
    with open(tmp_file, 'w') as f:
        f.write(policy_json)

    for policy_dir in policy_dirs:
        policy_file = os.path.join(policy_dir, 'gestflow.json')

        # Try without sudo
        try:
            os.makedirs(policy_dir, exist_ok=True)
            shutil.copy(tmp_file, policy_file)
            print_ok(f"Policy written: {policy_file}")
            continue
        except PermissionError:
            pass

        # Try with sudo
        ok1, _ = run(['sudo', 'mkdir', '-p', policy_dir])
        ok2, _ = run(['sudo', 'cp', tmp_file, policy_file])

        if ok1 and ok2:
            print_ok(f"Policy written (sudo): {policy_file}")
        else:
            print_warn(f"Skipped (no permission): {policy_dir}")


def _chrome_windows(policy):
    """Writes Chrome policy on Windows via Registry."""
    try:
        import winreg

        entry = policy['ExtensionInstallForcelist'][0]

        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE,
             r'SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist'),
            (winreg.HKEY_LOCAL_MACHINE,
             r'SOFTWARE\Policies\BraveSoftware\Brave\ExtensionInstallForcelist'),
            (winreg.HKEY_LOCAL_MACHINE,
             r'SOFTWARE\Policies\Microsoft\Edge\ExtensionInstallForcelist'),
            (winreg.HKEY_CURRENT_USER,
             r'SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist'),
        ]

        for hive, key_path in registry_keys:
            try:
                key = winreg.CreateKeyEx(
                    hive, key_path, 0, winreg.KEY_WRITE
                )
                winreg.SetValueEx(key, '1', 0, winreg.REG_SZ, entry)
                winreg.CloseKey(key)
                print_ok(f"Registry written: {key_path}")
            except Exception as e:
                print_warn(f"Registry skipped: {e}")

    except ImportError:
        print_warn("winreg not available")
        _manual_chrome_instructions()


def _chrome_mac(policy):
    """Writes Chrome policy on Mac."""
    import tempfile

    policy_files = [
        '/Library/Managed Preferences/com.google.Chrome.json',
        '/Library/Managed Preferences/com.brave.Browser.json',
    ]

    tmp = tempfile.mktemp(suffix='.json')
    with open(tmp, 'w') as f:
        json.dump(policy, f, indent=2)

    for policy_file in policy_files:
        policy_dir = os.path.dirname(policy_file)
        ok1, _ = run(['sudo', 'mkdir', '-p', policy_dir])
        ok2, _ = run(['sudo', 'cp', tmp, policy_file])

        if ok1 and ok2:
            print_ok(f"Mac policy written: {policy_file}")
        else:
            print_warn(f"Could not write: {policy_file}")


def _manual_chrome_instructions():
    """Prints manual install instructions as fallback."""
    print(f"\n  📋 Manual Chrome Extension Install:")
    print(f"  {'─' * 45}")
    print(f"  1. Open Chrome or Brave")
    print(f"  2. Go to: chrome://extensions/")
    print(f"  3. Enable Developer Mode (top right)")
    print(f"  4. Click Load unpacked")
    print(f"  5. Select this folder:")
    print(f"     {EXTENSION_SRC}")
    print(f"  {'─' * 45}")


# ══════════════════════════════════════════
# STEP 4 — VSCODE EXTENSION
# ══════════════════════════════════════════

def install_vscode_extension():
    print_step(4, "Installing GestFlow VSCode Extension")

    if not os.path.exists(VSCODE_EXT_SRC):
        print_warn(f"VSCode extension not found: {VSCODE_EXT_SRC}")
        return False

    # Check if bundled dist/extension.js exists
    dist_path = os.path.join(VSCODE_EXT_SRC, 'dist', 'extension.js')
    if not os.path.exists(dist_path):
        print_warn("Bundle not found — building now...")
        ok, out = run(
            ['npx', 'esbuild', 'extension.js',
             '--bundle', '--platform=node',
             '--outfile=dist/extension.js',
             '--external:vscode'],
            cwd=VSCODE_EXT_SRC
        )
        if ok:
            print_ok("Extension bundled successfully")
        else:
            print_warn(f"Bundle failed: {out[:200]}")
            return False

    # Copy to VSCode extensions folder — node_modules excluded
    ext_dir = os.path.join(HOME_DIR, '.vscode', 'extensions')

    if not os.path.exists(ext_dir):
        print_warn(f"VSCode extensions folder not found: {ext_dir}")
        _manual_vscode_instructions()
        return False

    dest = os.path.join(ext_dir, 'gestflow-vscode-1.0.0')

    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)

        shutil.copytree(
            VSCODE_EXT_SRC,
            dest,
            ignore=shutil.ignore_patterns(
                'node_modules', '.git', '*.pem', 'extension.js'
            )
        )

        print_ok(f"VSCode extension installed: {dest}")
        print_info("Restart VSCode to activate extension")
        return True

    except Exception as e:
        print_warn(f"Copy failed: {e}")
        _manual_vscode_instructions()
        return False


def _vscode_cli_install():
    """Installs VSCode extension using code CLI."""

    # Try to package as .vsix first
    vsix_path = os.path.join(BASE_DIR, 'gestflow-vscode.vsix')

    print("  Packaging VSCode extension...")
    result = subprocess.run(
        ['npx', 'vsce', 'package',
         '--out', vsix_path,
         '--no-dependencies'],
        cwd=VSCODE_EXT_SRC,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Try installing vsce first
        run(['npm', 'install', '-g', '@vscode/vsce'])
        result = subprocess.run(
            ['npx', 'vsce', 'package',
             '--out', vsix_path,
             '--no-dependencies'],
            cwd=VSCODE_EXT_SRC,
            capture_output=True,
            text=True
        )

    if not os.path.exists(vsix_path):
        print_warn("Could not package extension as .vsix")
        return False

    print_ok(f"Extension packaged: {vsix_path}")

    # Install using VSCode CLI
    vscode_cmds = ['code', 'code-insiders', 'codium']

    for cmd in vscode_cmds:
        ok, out = run([cmd, '--install-extension',
                       vsix_path, '--force'])
        if ok:
            print_ok(f"VSCode extension installed via: {cmd}")
            return True

    return False


def _vscode_copy_install():
    """Copies extension directly to VSCode extensions folder."""

    ext_dir = os.path.join(HOME_DIR, '.vscode', 'extensions')

    if not os.path.exists(ext_dir):
        print_warn(f"VSCode extensions folder not found: {ext_dir}")
        return False

    dest = os.path.join(ext_dir, 'gestflow-vscode-1.0.0')

    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(VSCODE_EXT_SRC, dest)
        print_ok(f"VSCode extension copied to: {dest}")
        print_info("Restart VSCode to activate extension")
        return True
    except Exception as e:
        print_warn(f"Copy failed: {e}")
        return False


def _manual_vscode_instructions():
    """Prints manual VSCode install instructions."""
    print(f"\n  📋 Manual VSCode Extension Install:")
    print(f"  {'─' * 45}")
    print(f"  1. Open VSCode")
    print(f"  2. Press Ctrl+Shift+P")
    print(f"  3. Type: Extensions: Install from VSIX")
    print(f"  4. Select gestflow-vscode.vsix from installer/")
    print(f"  {'─' * 45}")


# ══════════════════════════════════════════
# STEP 5 — VERIFY INSTALLATION
# ══════════════════════════════════════════

def verify_installation():
    print_step(5, "Verifying installation")

    all_good = True

    # Check Python packages
    packages = [
        'mediapipe', 'cv2', 'tensorflow',
        'numpy', 'websockets', 'zeroconf'
    ]

    for pkg in packages:
        try:
            __import__(pkg)
            print_ok(f"Package: {pkg}")
        except ImportError:
            print_fail(f"Missing: {pkg}")
            all_good = False

    # Check camera
    try:
        import cv2
        for index in [0, 1, 2]:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                print_ok(f"Camera: found at index {index}")
                cap.release()
                break
        else:
            print_warn("Camera: not detected")
    except Exception:
        print_warn("Camera: check failed")

    # Check VSCode CLI
    for cmd in ['code', 'code-insiders']:
        ok, _ = run([cmd, '--version'])
        if ok:
            print_ok(f"VSCode CLI: {cmd}")
            break
    else:
        print_warn("VSCode CLI: not in PATH")

    # Check config folder
    if os.path.exists(GESTFLOW_DIR):
        print_ok(f"Config folder: {GESTFLOW_DIR}")
    else:
        print_warn("Config folder: missing")

    return all_good


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def main():
    print_header()

    try:
        install_python_dependencies()
        setup_config()
        install_chrome_extension()
        install_vscode_extension()
        all_good = verify_installation()

        print(f"\n{'=' * 55}")
        if all_good:
            print("  ✅ GestFlow installed successfully!")
        else:
            print("  ⚠️  GestFlow installed with some warnings")
        print(f"{'=' * 55}")
        print(f"\n  To start GestFlow:")
        print(f"  cd gestflow/gestflow_02_content_engine")
        print(f"  python main.py")
        print(f"\n  First time:")
        print(f"  1. Restart Chrome or Brave")
        print(f"  2. Open VSCode")
        print(f"  3. Run python main.py")
        print(f"  4. Show your hand to the camera! 🤚")
        print(f"\n{'=' * 55}\n")

    except KeyboardInterrupt:
        print("\n\n  Installation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Installation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()