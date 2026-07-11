# ==========================================
# GESTFLOW BROWSER BRIDGE SERVER
# ==========================================
import asyncio
import json
import websockets
import threading
import time
import uuid
import socket as socket_lib

PORT = 8765

# ── Per-browser connection tracking ──
_connected_browsers = {}   # websocket → browser_name

# ── Per-request response tracking ──
_pending_requests = {}     # requestId → {event, data}

_current_tab_cache = {} 

_loop           = None
_server_running = False

VSCODE_PORT = 8766

# ── VSCode connection tracking ──
_connected_vscode    = None
_vscode_state_cache  = None
_vscode_requests     = {}   # requestId → {event, data}


# ══════════════════════════════════════════
# CONNECTION HANDLER
# ══════════════════════════════════════════

async def _handle_connection(websocket):
    global _connected_browsers

    browser_name = 'unknown'

    try:
        async for message in websocket:
            try:
                data     = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'BROWSER_CONNECTED':
                    browser_name = data.get('browser', 'unknown')

                    # Remove existing connection for same browser
                    existing = {
                        ws: name for ws, name
                        in _connected_browsers.items()
                        if name == browser_name
                    }
                    for ws in existing:
                        _connected_browsers.pop(ws, None)

                    _connected_browsers[websocket] = browser_name
                    print(f"🌐 Browser connected: {browser_name}")
                    print(f"   Total browsers: {len(_connected_browsers)}")

                elif msg_type == 'ACTIVE_TAB_RESPONSE':
                    request_id = data.get('requestId')
                    if request_id and request_id in _pending_requests:
                        _pending_requests[request_id]['data'] = data
                        _pending_requests[request_id]['event'].set()
                    # Ignore unsolicited responses
                elif msg_type == 'TAB_SWITCHED':
                    # Cache the latest active tab for each browser
                    _current_tab_cache[browser_name] = {
                        'type' : 'ACTIVE_TAB_RESPONSE',
                        'url'  : data.get('url'),
                        'title': data.get('title'),
    }
                elif msg_type == 'PING':
                    await websocket.send(json.dumps({'type': 'PONG'}))

            except json.JSONDecodeError:
                pass

    except websockets.exceptions.ConnectionClosed:
        if websocket in _connected_browsers:
            name = _connected_browsers.pop(websocket)
            print(f"🌐 Browser disconnected: {name}")
            print(f"   Remaining: {len(_connected_browsers)}")


# ══════════════════════════════════════════
# SERVER STARTUP
# ══════════════════════════════════════════

def _is_port_open(port, host='localhost'):
    try:
        sock = socket_lib.socket(socket_lib.AF_INET, socket_lib.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_bridge_server():
    """Starts all bridges — browser and VSCode."""
    def run():
        asyncio.run(_run_all_servers())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    print(f"⏳ Waiting for server to bind to port {PORT}...")
    for i in range(20):
        if _is_port_open(PORT):
            print(f"🌐 Browser bridge running on port {PORT}")
            print(f"💻 VSCode bridge running on port {VSCODE_PORT}")
            return True
        time.sleep(0.5)

    print(f"❌ Server failed to start")
    return False


async def _run_all_servers():
    """Runs both browser and VSCode servers simultaneously."""
    global _loop, _server_running
    _loop           = asyncio.get_running_loop()
    _server_running = True

    import logging
    logging.getLogger('websockets').setLevel(logging.CRITICAL)

    browser_server = websockets.serve(
        _handle_connection, 'localhost', PORT
    )
    vscode_server = websockets.serve(
        _handle_vscode_connection, 'localhost', VSCODE_PORT
    )

    async with browser_server, vscode_server:
        await asyncio.Future()


# ══════════════════════════════════════════
# BROWSER MANAGEMENT
# ══════════════════════════════════════════

def is_extension_connected():
    return len(_connected_browsers) > 0


def get_connected_browsers():
    return list(_connected_browsers.values())


def get_browser_socket(browser_name):
    """Returns socket for specific browser name."""
    for socket, name in _connected_browsers.items():
        if name == browser_name:
            return socket
    return None


def get_any_browser_socket():
    """Returns first available browser socket."""
    if _connected_browsers:
        return next(iter(_connected_browsers))
    return None


# ══════════════════════════════════════════
# TAB REQUESTS
# ══════════════════════════════════════════

async def _send_to_browser(websocket, message):
    try:
        await websocket.send(json.dumps(message))
        return True
    except Exception as e:
        print(f"⚠️  Send failed: {e}")
        return False


def request_active_tab(browser_name=None, timeout=3):
    """
    Requests active tab from specific browser.
    Each request has its own event and ID.
    No cross-contamination between browsers.
    """
    global _pending_requests, _loop, _current_tab_cache

    # Check cache first — most recent tab switch
    if browser_name and browser_name in _current_tab_cache:
        cached = _current_tab_cache.pop(browser_name)
        if cached.get('url'):
            print(f"📋 Using cached tab for {browser_name}")
            return cached

    if not _loop:
        return None

    # Find correct socket
    if browser_name:
        target_socket = get_browser_socket(browser_name)
        if not target_socket:
            print(f"⚠️  {browser_name} not connected — trying any")
            target_socket = get_any_browser_socket()
    else:
        target_socket = get_any_browser_socket()

    if not target_socket:
        print("⚠️  No browsers connected")
        return None

    # Create unique request slot
    request_id    = str(uuid.uuid4())[:8]
    request_event = threading.Event()
    _pending_requests[request_id] = {
        'event': request_event,
        'data' : None
    }

    # Send to specific browser with request ID
    future = asyncio.run_coroutine_threadsafe(
        _send_to_browser(target_socket, {
            'type'      : 'GET_ACTIVE_TAB',
            'requestId' : request_id
        }),
        _loop
    )

    try:
        future.result(timeout=2)
    except Exception as e:
        print(f"⚠️  Request failed: {e}")
        _pending_requests.pop(request_id, None)
        return None

    # Wait for THIS request's response only
    received = request_event.wait(timeout=timeout)
    response = _pending_requests.pop(request_id, {}).get('data')

    if not received or not response:
        print("⚠️  No response received")
        return None

    return response

# ══════════════════════════════════════════
# VS CODE INTEGRATION
# ══════════════════════════════════════════
async def _handle_vscode_connection(websocket):
    """Handles VSCode extension connection."""
    global _connected_vscode, _vscode_state_cache

    _connected_vscode = websocket
    print("💻 VSCode extension connected!")

    try:
        async for message in websocket:
            try:
                data     = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'VSCODE_CONNECTED':
                    print(f"   VSCode version: {data.get('version')}")

                elif msg_type == 'VSCODE_STATE_RESPONSE':
                    request_id = data.get('requestId')
                    state      = data.get('state', {})

                    # Cache latest state
                    _vscode_state_cache = state

                    # Resolve pending request if any
                    if request_id and request_id in _vscode_requests:
                        _vscode_requests[request_id]['data'] = state
                        _vscode_requests[request_id]['event'].set()

                elif msg_type == 'PONG':
                    pass

            except json.JSONDecodeError:
                pass

    except websockets.exceptions.ConnectionClosed:
        print("💻 VSCode extension disconnected")
        _connected_vscode   = None
        _vscode_state_cache = None


async def _run_vscode_server():
    """Runs VSCode WebSocket server on port 8766."""
    import logging
    logging.getLogger('websockets').setLevel(logging.CRITICAL)

    async with websockets.serve(
        _handle_vscode_connection, 'localhost', VSCODE_PORT
    ):
        await asyncio.Future()


def start_vscode_bridge():
    """Starts VSCode bridge in background thread."""
    def run():
        asyncio.run(_run_vscode_server())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(0.5)
    print(f"💻 VSCode bridge running on port {VSCODE_PORT}")


def is_vscode_connected():
    return _connected_vscode is not None


def request_vscode_state(timeout=3):
    """
    Requests current VSCode state.
    Returns cached state if available — instant response.
    """
    global _vscode_requests, _loop

    # Return cache immediately if fresh
    if _vscode_state_cache:
        return _vscode_state_cache

    if not _connected_vscode or not _loop:
        return None

    request_id    = str(uuid.uuid4())[:8]
    request_event = threading.Event()
    _vscode_requests[request_id] = {
        'event': request_event,
        'data' : None
    }

    future = asyncio.run_coroutine_threadsafe(
        _send_to_browser(_connected_vscode, {
            'type'      : 'GET_VSCODE_STATE',
            'requestId' : request_id
        }),
        _loop
    )

    try:
        future.result(timeout=2)
    except Exception as e:
        _vscode_requests.pop(request_id, None)
        return None

    received = request_event.wait(timeout=timeout)
    response = _vscode_requests.pop(request_id, {}).get('data')

    return response if received else None
