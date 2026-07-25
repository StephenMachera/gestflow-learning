# ==========================================
# GESTFLOW PACKET VALIDATOR
# ==========================================
# Single responsibility:
#   → Validate incoming packets before processing
#   → Check protocol version compatibility
#   → Ensure required fields exist
#   → Detect stale or corrupt packets
#   → Return clear validation result

import json
import sys
import os
import time

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_03_state_capture.packet_builder import (
    GESTFLOW_VERSION,
    PACKET_TYPES,
    CONTENT_TYPES,
    get_packet_age,
    is_packet_expired
)

# ══════════════════════════════════════════
# VALIDATION RESULT
# ══════════════════════════════════════════
def _pass(message = "Valid"):
    """Returns a passing validation result."""
    return {
        'valid': True,
        'message': message,
        'errors': []
    }
def _fail(errors):
    if isinstance(errors, str):
        errors = [errors]
    # Flatten if someone passed a list inside a list
    flat = []
    for e in errors:
        if isinstance(e, list):
            flat.extend(e)
        else:
            flat.append(e)
    return {
        'valid'  : False,
        'message': flat[0] if flat else 'Unknown error',
        'errors' : flat
    }

# ══════════════════════════════════════════
# FIELD VALIDATORS
# ══════════════════════════════════════════
def _validate_protocol_version(packet):
    """
    Checks gestflow protocol version.
    Ensures this device can understand the packet.
    """
    packet_version = packet.get('gestflow')

    if not packet_version:
        return _fail("Missing 'gestflow' protocol version field.")
    # Parse major version
    try:
        received_major = int(packet_version.split('.')[0])
        current_major = int(GESTFLOW_VERSION.split('.')[0])
    except ValueError:
        return _fail(f"Invalid protocol version format: {packet_version}")
    # Major version must match
    # Minor version differences are acceptable
    if received_major != current_major:
        return _fail(
            f"Version mismatch: received v{packet_version} "
            f"but this device runs v{GESTFLOW_VERSION}. "
            f"Please update GestFlow."
        )
    return _pass(f"Version {packet_version} ✅")

def _validate_required_fields(packet, required_fields):
    """
    Checks that all required fields exist in packet.
    required_fields is a list of field names.
    """
    errors=[]
    for field in required_fields:
        if field not in packet or packet[field] is None:
            errors.append(f"Missing required field: '{field}'")
    if errors:
        return _fail(errors)
    return _pass("All required fields present ✅")

def _validate_packet_type(packet):
    """
    Checks packet type is a known GestFlow type.
    """
    packet_type = packet.get('type')

    if not packet_type:
        return _fail("Missing 'type' field")
    if packet_type not in PACKET_TYPES.values():
        return _fail(
            f"Unknown packet type: '{packet_type}'. "
            f"Expected one of: {list(PACKET_TYPES.values())}"
        )
    return _pass(f"Type '{packet_type}' ✅")

def _validate_source_peer(packet):
    """
    Validates the sourcePeer field.
    Must have ip and port at minimum.
    """
    source_peer = packet.get('sourcePeer')
    if not source_peer:
        return _fail("Missing 'sourcePeer' field")
    if not isinstance(source_peer, dict):
        return _fail("'sourcePeer' must be an object")
    errors = []

    if not source_peer.get('ip'):
        errors.append("sourcePeer missing 'ip' address")

    if not source_peer.get('port'):
        errors.append("sourcePeer missing 'port'")

    if not source_peer.get('name'):
        errors.append("sourcePeer missing 'name'")

    if errors:
        return _fail(errors)
    return _pass(f"sourcePeer valid: {source_peer.get('name')} ({source_peer.get('ip')}) ✅")

def _validate_content(packet):
    """
    Validates the content field for CONTENT_TRANSFER packets.
    Checks content type is known and state exists.
    """
    content = packet.get('content')
    if not content:
        return _fail("Missing 'content' field")
    if not isinstance(content, dict):
        return _fail("'content' must be an object")
    
    content_type = content.get('contentType')
    if not content_type:
        return _fail("content missing 'contentType'")
    if content_type not in CONTENT_TYPES.values():
        return _fail(
            f"Unknown contentType: '{content_type}'. "
            f"Expected one of: {list(CONTENT_TYPES.values())}"
        )
    state = content.get('state')
    if state is None:
        return _fail("content missing 'state'")
    if not isinstance(state, dict):
        return _fail("content 'state' must be an object")

    return _pass(f"Content valid: {content_type} ✅")

def _validate_timestamp(packet):
    """
    Checks packet timestamp is valid and not in the future.
    Future timestamps indicate clock skew or corrupted packet.
    """
    timestamp = packet.get('timestamp')
    if not timestamp:
        return _fail("Missing 'timestamp' field")
    try:
        timestamp = int(timestamp)
    except (ValueError, TypeError):
        return _fail("Missing 'timestamp' field")
    
    now = int(time.time())
    # Timestamp should not be more than 60 seconds in the future
    # Small allowance for clock differences between devices
    if timestamp > now + 60:
        return _fail(
            f"Packet timestamp is in the future "
            f"({timestamp - now}s ahead). "
            f"Check device clock settings."
        )

    return _pass("Timestamp valid ✅")

def _validate_expiry(packet):
    """
    Checks packet has not expired.
    Prevents stale transfers from executing.
    """
    if is_packet_expired(packet):
        age = get_packet_age(packet)
        expires_in = packet.get('transfer',{}).get('expiresIn', 30)
        return _fail(
            f"Packet expired: {age}s old "
            f"(expires after {expires_in}s). "
            f"Transfer was too slow."
        )
    return _pass(f"Packet fresh: {get_packet_age(packet)}s old ✅")

def _validate_packet_id(packet):
    """
    Checks packetId exists and has correct format.
    """
    packet_id = packet.get('packetId')
    if not packet_id:
        return _fail("Missing 'packetId' field")
    if not isinstance(packet_id, str):
        return _fail("'packetId' must be a string")
    if len(packet_id) < 4:
        return _fail(f"'packetId' too short: '{packet_id}'")

    return _pass(f"PacketId valid: {packet_id} ✅")

# ══════════════════════════════════════════
# CONTENT TYPE SPECIFIC VALIDATORS
# ══════════════════════════════════════════

def _validate_video_state(state):
    """Validates video content state has required fields."""
    errors = []
    if not state.get('filePath'):
        errors.append("Video state missing 'filePath'")
    return _fail(errors) if errors else _pass("Video state valid ✅")


def _validate_browser_state(state):
    """Validates browser content state."""
    # URL can be null in v1 fallback — so we just warn
    if not state.get('url') and not state.get('pageTitle'):
        return _fail("Browser state missing both 'url' and 'pageTitle'")
    return _pass("Browser state valid ✅")


def _validate_code_state(state):
    """Validates code content state."""
    errors = []
    if not state.get('filePath') and not state.get('fileName'):
        errors.append("Code state missing both 'filePath' and 'fileName'")
    return _fail(errors) if errors else _pass("Code state valid ✅")


def _validate_audio_state(state):
    """Validates audio content state."""
    errors = []
    if not state.get('filePath') and not state.get('trackName'):
        errors.append("Audio state missing both 'filePath' and 'trackName'")
    return _fail(errors) if errors else _pass("Audio state valid ✅")


# Map content types to their validators
CONTENT_VALIDATORS = {
    'video'  : _validate_video_state,
    'browser': _validate_browser_state,
    'code'   : _validate_code_state,
    'audio'  : _validate_audio_state,
}

# ══════════════════════════════════════════
# MAIN VALIDATORS
# One function per packet type
# ══════════════════════════════════════════

def validate_transfer_packet(packet):
    """
    Full validation for CONTENT_TRANSFER packets.
    Runs all checks and collects all errors.

    Returns:
    {
        'valid'  : True/False,
        'message': 'summary',
        'errors' : ['error1', 'error2', ...]
    }
    """
    all_errors = []

    checks = [
        _validate_protocol_version(packet),
        _validate_packet_id(packet),
        _validate_packet_type(packet),
        _validate_timestamp(packet),
        _validate_expiry(packet),
        _validate_source_peer(packet),
        _validate_required_fields(packet, ['gestflow', 'packetId',
                                           'type', 'timestamp',
                                           'sourcePeer', 'content',
                                           'gesture']),
        _validate_content(packet),
    ]
    # Collect all errors
    for check in checks:
        if not check['valid']:
            all_errors.extend(check['errors'])
        
    if all_errors:
        return _fail(all_errors)
    
    # Content type specific validation
    content = packet.get('content',{})
    content_type = content.get('contentType')
    state = content.get('state',{})
    content_validator = CONTENT_VALIDATORS.get(content_type)
    if content_validator:
        result = content_validator(state)
        if not result['valid']:
            all_errors.extend(result['errors'])
    if all_errors:
        return _fail(all_errors)

    return _pass(
        f"✅ Valid CONTENT_TRANSFER packet "
        f"[{packet.get('packetId')}] "
        f"from {packet.get('sourcePeer', {}).get('name')}"
    )

def validate_ack_packet(packet):
    """Validates ACK packets."""
    all_errors = []

    checks = [
        _validate_protocol_version(packet),
        _validate_packet_id(packet),
        _validate_packet_type(packet),
        _validate_timestamp(packet),
        _validate_source_peer(packet),
        _validate_required_fields(packet, ['ackFor', 'success']),
    ]

    for check in checks:
        if not check['valid']:
            all_errors.extend(check['errors'])

    if all_errors:
        return _fail(all_errors)

    return _pass(
        f"✅ Valid ACK packet for "
        f"[{packet.get('ackFor')}] — "
        f"{'success' if packet.get('success') else 'failed'}"
    )

def validate_ping_packet(packet):
    """Validates PING packets."""
    checks = [
        _validate_protocol_version(packet),
        _validate_packet_id(packet),
        _validate_source_peer(packet),
    ]
    errors = [e for c in checks for e in c['errors']]
    return _fail(errors) if errors else _pass("✅ Valid PING packet")


def validate_peer_announce_packet(packet):
    """Validates PEER_ANNOUNCE packets."""
    checks = [
        _validate_protocol_version(packet),
        _validate_packet_id(packet),
        _validate_source_peer(packet),
        _validate_required_fields(packet, ['capabilities']),
    ]
    errors = [e for c in checks for e in c['errors']]
    return _fail(errors) if errors else _pass("✅ Valid PEER_ANNOUNCE packet")


# ══════════════════════════════════════════
# MASTER VALIDATOR
# Single entry point — routes to correct validator
# ══════════════════════════════════════════

def validate_packet(packet):
    """
    Master validator — single entry point for Phase 5.
    Automatically routes to the correct validator
    based on packet type.

    Usage in Phase 5:
        result = validate_packet(received_packet)
        if not result['valid']:
            print(f"Invalid packet: {result['message']}")
            return
        # process packet...

    Returns:
    {
        'valid'  : True/False,
        'message': 'summary',
        'errors' : ['error1', ...]
    }
    """
    # Basic check — is it even a dict?
    if not packet or not isinstance(packet, dict):
        return _fail("Packet is empty or not a valid object")

    # Route to correct validator based on type
    packet_type = packet.get('type')

    validators = {
        'CONTENT_TRANSFER': validate_transfer_packet,
        'ACK'             : validate_ack_packet,
        'PING'            : validate_ping_packet,
        'PONG'            : validate_ping_packet,   # same rules as ping
        'PEER_ANNOUNCE'   : validate_peer_announce_packet,
        'CANCEL'          : validate_ping_packet,   # same minimal rules
    }

    validator = validators.get(packet_type)

    if not validator:
        return _fail(f"No validator found for packet type: '{packet_type}'")

    return validator(packet)


# ══════════════════════════════════════════
# TEST BLOCK
# ══════════════════════════════════════════

if __name__ == "__main__":
    import json
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from gestflow_03_state_capture.packet_builder import (
        build_transfer_packet,
        build_ack_packet,
        build_ping_packet,
        build_peer_announce_packet
    )

    print("🔍 GestFlow Packet Validator Test")
    print("=" * 40)

    # ── Mock Phase 2 content ──
    mock_content = {
        "app"        : "code",
        "contentType": "code",
        "windowTitle": "main.py - gestflow-learning - Visual Studio Code",
        "adapter"    : "vscode_adapter",
        "state": {
            "filePath"  : "/home/user/gestflow/main.py",
            "fileName"  : "main.py",
            "language"  : "python",
            "cursorLine": 42,
            "gitBranch" : "dev-branch",
        }
    }

    # ── Test 1 — Valid transfer packet ──
    print("\n✅ Test 1 — Valid transfer packet:")
    packet = build_transfer_packet(mock_content, "FIST_THROW_RIGHT")
    result = validate_packet(packet)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 2 — Missing required field ──
    print("\n❌ Test 2 — Missing gesture field:")
    bad_packet = build_transfer_packet(mock_content, "FIST_THROW_RIGHT")
    del bad_packet['gesture']
    result = validate_packet(bad_packet)
    print(f"   Valid  : {result['valid']}")
    print(f"   Errors : {result['errors']}")

    # ── Test 3 — Wrong version ──
    print("\n❌ Test 3 — Wrong protocol version:")
    wrong_version = build_transfer_packet(mock_content, "FIST_THROW_RIGHT")
    wrong_version['gestflow'] = '99.0'
    result = validate_packet(wrong_version)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 4 — Expired packet ──
    print("\n❌ Test 4 — Expired packet:")
    expired = build_transfer_packet(mock_content, "FIST_THROW_RIGHT")
    expired['timestamp'] = int(time.time()) - 60  # 60 seconds ago
    result = validate_packet(expired)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 5 — Valid ACK packet ──
    print("\n✅ Test 5 — Valid ACK packet:")
    original = build_transfer_packet(mock_content, "FIST_THROW_RIGHT")
    ack      = build_ack_packet(original, success=True)
    result   = validate_packet(ack)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 6 — Valid PING ──
    print("\n✅ Test 6 — Valid PING packet:")
    ping   = build_ping_packet()
    result = validate_packet(ping)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 7 — Valid peer announce ──
    print("\n✅ Test 7 — Valid PEER_ANNOUNCE:")
    announce = build_peer_announce_packet()
    result   = validate_packet(announce)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 8 — Corrupt packet ──
    print("\n❌ Test 8 — Completely corrupt packet:")
    result = validate_packet({"random": "garbage"})
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    # ── Test 9 — None packet ──
    print("\n❌ Test 9 — None packet:")
    result = validate_packet(None)
    print(f"   Valid  : {result['valid']}")
    print(f"   Message: {result['message']}")

    print("\n" + "=" * 40)
    print("✅ All validator tests complete!")



