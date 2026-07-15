# ==========================================
# GESTFLOW BROWSER ADAPTER
# ==========================================
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from permissions.permission_manager import ensure_permission
from browser_bridge_server import is_extension_connected, request_active_tab


def _parse_title_from_window(window_title):
    if not window_title:
        return None
    browser_suffixes = [
        r'\s*-\s*Google Chrome$',
        r'\s*-\s*Chromium$',
        r'\s*-\s*Brave$',
        r'\s*-\s*Microsoft Edge$',
        r'\s*-\s*Mozilla Firefox$',
    ]
    title = window_title
    for suffix in browser_suffixes:
        title = re.sub(suffix, '', title).strip()
    if not title or title.lower() in ['new tab', 'about:blank']:
        return None
    return title


def _fallback_from_title(window_title):
    return {
        'dynamicType': 'browser',
        'state': {
            'url'      : None,
            'pageTitle': _parse_title_from_window(window_title),
            'tabIndex' : 0,
            'isLoading': False,
            'note'     : 'fallback — extension not connected'
        }
    }


def _titles_match(window_title, page_title):
    """
    Checks if window title and page title are roughly the same.
    Catches cases where stale URL is returned.
    """
    if not window_title or not page_title:
        return True  # cannot check — assume ok

    # Extract page title from window title
    # "YouTube - Google Chrome" → "YouTube"
    import re
    clean_window = re.sub(
        r'\s*-\s*(Google Chrome|Brave|Chromium|Microsoft Edge)$',
        '', window_title
    ).strip().lower()

    clean_page = page_title.strip().lower()

    # Check if they overlap at all
    # Use first 20 chars of each for comparison
    window_key = clean_window[:20]
    page_key   = clean_page[:20]

    return window_key == page_key


def get_browser_state(window_title, app_name=None):
    import time

    permission_granted = ensure_permission('browser', app_name=app_name)
    if not permission_granted:
        return _fallback_from_title(window_title)

    if not is_extension_connected():
        return _fallback_from_title(window_title)

    browser_name_map = {
        'google-chrome'  : 'chrome',
        'chrome'         : 'chrome',
        'chromium'       : 'chromium',
        'brave-browser'  : 'brave',
        'brave'          : 'brave',
        'microsoft-edge' : 'edge',
    }
    browser_name = browser_name_map.get(app_name)

    # Wait for Chrome to register the active tab
    time.sleep(0.3)

    # First attempt
    tab = request_active_tab(browser_name=browser_name, timeout=3)

    if not tab or not tab.get('url'):
        return _fallback_from_title(window_title)

    # Sanity check — does URL match window title?
    if not _titles_match(window_title, tab.get('title', '')):
        print("⚠️  Title mismatch — requesting again...")
        time.sleep(0.5)
        tab = request_active_tab(browser_name=browser_name, timeout=3)
        if not tab or not tab.get('url'):
            return _fallback_from_title(window_title)

    return {
        'dynamicType': 'browser',
        'state': {
            'url'      : tab.get('url'),
            'pageTitle': tab.get('title'),
            'tabIndex' : 0,
            'isLoading': False,
            'note'     : f"v1 — URL via GestFlow extension ({browser_name})"
        }
    }