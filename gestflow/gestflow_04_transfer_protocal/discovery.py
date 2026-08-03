# ==========================================
# GESTFLOW DISCOVERY SERVICE
# ==========================================
# Single responsibility:
#   → Broadcast this device on the network
#   → Listen for other GestFlow devices
#   → Add/remove peers from peer_manager
# ==========================================

import socket
import threading
import time
import json
import sys
import os
import asyncio
import websockets

from zeroconf import (
    Zeroconf,
    ServiceInfo,
    ServiceBrowser,
    ServiceListener
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_03_state_capture.device_info import get_device_info, GESTFLOW_P2P_PORT
from gestflow_04_transfer_protocal.peer_manager import add_peer, remove_peer
from gestflow_02_content_engine.browser_bridge_server import _handle_connection, PORT

# ── Service type ──
# Only GestFlow devices respond to this
SERVICE_TYPE = "_gestflow._tcp.local."


# ══════════════════════════════════════════
# SERVICE LISTENER
# Handles devices joining and leaving
# ══════════════════════════════════════════

class GestFlowListener(ServiceListener):
    """
    Listens for GestFlow devices on the network.
    Called automatically by zeroconf when:
      → A new GestFlow device appears
      → A GestFlow device disappears
      → A GestFlow device updates its info
    """

    def add_service(self, zeroconf, service_type, name):
        """Called when a new GestFlow device is found."""
        try:
            info = zeroconf.get_service_info(service_type, name)
            if not info:
                return

            # Extract peer info from service record
            peer = _parse_service_info(info)
            if peer:
                add_peer(peer)

        except Exception as e:
            print(f"⚠️  Discovery error (add): {e}")

    def remove_service(self, zeroconf, service_type, name):
        """Called when a GestFlow device leaves the network."""
        try:
            # Extract peer ID from service name
            peer_id = _extract_peer_id(name)
            if peer_id:
                remove_peer(peer_id)

        except Exception as e:
            print(f"⚠️  Discovery error (remove): {e}")

    def update_service(self, zeroconf, service_type, name):
        """Called when a GestFlow device updates its info."""
        # Re-add with updated info
        self.add_service(zeroconf, service_type, name)


# ══════════════════════════════════════════
# SERVICE INFO PARSING
# ══════════════════════════════════════════

def _parse_service_info(info):
    """
    Extracts peer info from a zeroconf ServiceInfo object.
    Returns peer dict or None if parsing fails.
    """
    try:
        # Get IP address
        addresses = info.parsed_addresses()
        if not addresses:
            return None

        ip = addresses[0]

        # Get port
        port = info.port or GESTFLOW_P2P_PORT

        # Get properties from TXT record
        properties = {}
        if info.properties:
            for key, value in info.properties.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                properties[key] = value

        peer_id   = properties.get('id', ip)
        peer_name = properties.get('name', f"GestFlow-{ip}")
        peer_os   = properties.get('os', 'Unknown')
        version   = properties.get('version', '1.0')

        return {
            'id'     : peer_id,
            'name'   : peer_name,
            'ip'     : ip,
            'port'   : port,
            'os'     : peer_os,
            'version': version
        }

    except Exception as e:
        print(f"⚠️  Could not parse service info: {e}")
        return None


def _extract_peer_id(service_name):
    """
    Extracts peer ID from service name.
    Service name format:
    gestflow-{peer_id}._gestflow._tcp.local.
    """
    try:
        # Remove service type suffix
        name = service_name.replace(f".{SERVICE_TYPE}", "")
        # Remove gestflow- prefix
        if name.startswith("gestflow-"):
            return name[len("gestflow-"):]
        return name
    except Exception:
        return None


# ══════════════════════════════════════════
# SERVICE REGISTRATION
# Announces this device on the network
# ══════════════════════════════════════════

def _build_service_info():
    """
    Builds a ServiceInfo object for this device.
    This is what gets broadcast on the network.
    """
    device = get_device_info()

    # Service name — unique per device
    service_name = f"gestflow-{device['id']}.{SERVICE_TYPE}"

    # Properties broadcast in TXT record
    # Other devices read these to identify us
    properties = {
        'id'     : device['id'],
        'name'   : device['name'],
        'os'     : device['os'],
        'version': device['version'],
    }

    # Encode properties as bytes for zeroconf
    encoded_properties = {
        k.encode('utf-8'): v.encode('utf-8')
        for k, v in properties.items()
    }

    # Get local IP as bytes
    ip = device['ip']

    return ServiceInfo(
        type_        = SERVICE_TYPE,
        name         = service_name,
        port         = device['port'],
        properties   = encoded_properties,
        addresses    = [socket.inet_aton(ip)],
        server       = f"{device['hostname']}.local."
    )


# ══════════════════════════════════════════
# DISCOVERY SERVICE
# ══════════════════════════════════════════

# Module level state
_zeroconf        = None
_service_info    = None
_browser         = None
_discovery_active = False

async def _run_server():
    """Runs discovery and re-announces every 20 seconds."""
    global _loop, _server_running
    _loop           = asyncio.get_running_loop()
    _server_running = True

    async with websockets.serve(_handle_connection, 'localhost', PORT):
        await asyncio.Future()

def start_discovery():
    """
    Starts the GestFlow discovery service.

    Does two things simultaneously:
      1. Registers this device so others can find us
      2. Listens for other GestFlow devices

    Call once when GestFlow starts.
    Runs in background — non-blocking.
    """
    global _zeroconf, _service_info, _browser, _discovery_active

    if _discovery_active:
        return

    def run():
        global _zeroconf, _service_info, _browser, _discovery_active

        try:
            device = get_device_info()
            print(f"📡 Starting discovery service...")
            print(f"   Broadcasting: {device['name']} on {device['ip']}:{device['port']}")

            _zeroconf     = Zeroconf()
            _service_info = _build_service_info()
            _zeroconf.register_service(_service_info)
            print(f"✅ Device registered on network")

            listener = GestFlowListener()
            _browser  = ServiceBrowser(_zeroconf, SERVICE_TYPE, listener)
            print(f"👂 Listening for nearby GestFlow devices...")

            _discovery_active = True

            # ── Re-announce every 20 seconds ──
            # Keeps this device visible to peers
            # Prevents peers from marking us as stale
            while _discovery_active:
                time.sleep(20)
                if _discovery_active and _zeroconf and _service_info:
                    try:
                        _zeroconf.update_service(_service_info)
                    except Exception:
                        pass

        except Exception as e:
            print(f"❌ Discovery error: {e}")
            _discovery_active = False

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(2)


def stop_discovery():
    """
    Stops the discovery service cleanly.
    Unregisters this device from the network.
    Other devices will know we left.
    """
    global _zeroconf, _service_info, _discovery_active

    _discovery_active = False

    if _zeroconf and _service_info:
        try:
            _zeroconf.unregister_service(_service_info)
            _zeroconf.close()
            print("📡 Discovery service stopped")
        except Exception as e:
            print(f"⚠️  Error stopping discovery: {e}")

    _zeroconf     = None
    _service_info = None


def is_discovery_active():
    """Returns True if discovery service is running."""
    return _discovery_active


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from gestflow_04_transfer_protocal.peer_manager import (
        print_peer_list,
        get_online_peer_count,
        start_peer_cleanup
    )

    print("📡 GestFlow Discovery Service Test")
    print("=" * 40)

    # Start peer cleanup
    start_peer_cleanup()

    # Start discovery
    start_discovery()

    print("\n⏳ Waiting for nearby GestFlow devices...")
    print("   Run this script on another device to test discovery")
    print("   Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(5)
            count = get_online_peer_count()
            if count > 0:
                print_peer_list()
            else:
                print(f"   No peers found yet — waiting...")

    except KeyboardInterrupt:
        print("\n\nStopping discovery...")
        stop_discovery()
        print("👋 Done")

