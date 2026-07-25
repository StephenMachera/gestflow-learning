import json
import os
import platform
import socket
import uuid
import time


#__Storage__

GESTFLOW_DIR = os.path.join(os.path.expanduser("~/.gestflow"))
DEVICE_FILE = os.path.join(GESTFLOW_DIR, "device.json")

#__P2P port
"""
Each node in gestflow will listen from this port
"""
GESTFLOW_P2P_PORT = 9001

# ══════════════════════════════════════════
# DEVICE DETECTION
# ══════════════════════════════════════════

def _get_hostname():
    """
    This functio uses the socket library to get the hostname of the device.
    """
    try:
        return socket.gethostname()
    except Exception as e:
        print(f"Error getting hostname: {e}")
        return "Unknown-host"
def _get_local_ip():
    """
    Gets the device's local IP address on the network.
    Uses a UDP trick — connects to external IP without
    sending data, just to find which interface is used.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.connect(("8.8.8.8", 80)) # Google's public DNS server
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"
    
def _get_os_name():
    """
    Gets the opereting system name using the platform library.
    """
    try: 
        system = platform.system()
        os_map = {
            "Windows": "Windows",
            "Darwin": "macOS",
            "Linux": "Linux",
            "Java": "Java",
            "AIX": "AIX",
            "FreeBSD": "FreeBSD",
            "SunOS": "Solaris",
        }
        return os_map.get(system, system)
    except Exception as e:
        print(f"Error getting OS name: {e}")
        return "Unknown-OS"
    
def _get_device_name():
    """
    Returns a human readable device name.
    Uses hostname — same name user sees in network settings.
    """
    try:
        hostname = _get_hostname()
        parts = hostname.split("-")
        if len(parts)>1:
            return '-'.join(parts[1:])
        return hostname
    except Exception as e:
        print(f"Error getting device name: {e}")
        return "Unknown-Device"
    
def _generate_device_id():
    """
    Generates a unique device ID.
    Based on MAC address so it stays the same
    across GestFlow restarts.
    """
    try:
        # Use MAC address as base — unique per device
        mac = uuid.getnode()
        device_id = str(uuid.uuid5(
            uuid.NAMESPACE_DNS, str(mac)
        ))
        return device_id
    except Exception as e:
        print(f"Error generating device ID: {e}")
        return str(uuid.uuid4())  # fallback to random UUID
    
# ══════════════════════════════════════════
# DEVICE INFO MANAGEMENT
# ══════════════════════════════════════════

def _load_device_info():
    """
    Loads saved device info from disk.
    Returns None if not saved yet.
    """
    try:
        if os.path.exists(DEVICE_FILE):
            with open(DEVICE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading device info: {e}")
        return None

def _save_device_info(info):
    """Saves device info to ~/.gestflow/device.json"""
    try:
        os.makedirs(GESTFLOW_DIR, exist_ok=True)
        with open(DEVICE_FILE, "w") as f:
            json.dump(info, f, indent=4)
    except Exception as e:
        print(f"Error saving device info: {e}")

def get_device_info():
    """
    Returns current device identity.
    Loads from disk if saved — generates fresh if not.

    This is what gets embedded in every transfer packet
    as 'sourcePeer' to identify who sent it.

    Returns:
    {
        "id"      : "a3f9b2c1-...",   unique device ID
        "name"    : "ThinkPad-X280",  human readable name
        "hostname": "stephen-ThinkPad-X280",
        "os"      : "Linux",
        "ip"      : "192.168.1.5",    current IP
        "port"    : 9001,             P2P listening port
        "version" : "1"             GestFlow version
    }
    """
    saved = _load_device_info()

    # IP can always change, so we always refresh it
    current_ip = _get_local_ip()

    if saved:
        saved["ip"] = current_ip
        return saved
    # First time — generate and save
    info = {
        'id'      : _generate_device_id(),
        'name'    : _get_device_name(),
        'hostname': _get_hostname(),
        'os'      : _get_os_name(),
        'ip'      : current_ip,
        'port'    : GESTFLOW_P2P_PORT,
        'version' : '1',
        'created' : time.strftime('%Y-%m-%d %H:%M:%S')
    }

    _save_device_info(info)
    return info

def update_device_name(new_name):
    """
    Allows user to set a custom device name.
    e.g. "Living Room TV", "Work Laptop"
    """
    info = get_device_info()
    info['name'] = new_name
    _save_device_info(info)
    print(f"✅ Device name updated to: {new_name}")
    return info

def get_peer_info(ip, port=GESTFLOW_P2P_PORT, name=None):
    """
    Builds a peer info dict for a remote device.
    Used to fill 'targetPeer' in transfer packets.
    Called by Phase 4 after discovering a device.
    """
    return {
        'ip'  : ip,
        'port': port,
        'name': name or ip,
    }

# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    print("🖥️  GestFlow Device Info")
    print("=" * 40)

    info = get_device_info()

    print(f"\n📋 Device Identity:")
    print(f"   ID       : {info['id']}")
    print(f"   Name     : {info['name']}")
    print(f"   Hostname : {info['hostname']}")
    print(f"   OS       : {info['os']}")
    print(f"   IP       : {info['ip']}")
    print(f"   Port     : {info['port']}")
    print(f"   Version  : {info['version']}")

    print(f"\n📁 Saved to: {DEVICE_FILE}")

    # Test peer info
    print(f"\n🔗 Example peer info:")
    peer = get_peer_info('192.168.1.8', name='Desktop-PC')
    print(json.dumps(peer, indent=4))
    

   
