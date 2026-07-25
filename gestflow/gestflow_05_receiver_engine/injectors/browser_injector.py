# ==========================================
# GESTFLOW BROWSER INJECTOR
# ==========================================
# Receives browser state from transfer packet
# Opens exact URL in default browser
# ==========================================
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gestflow_05_receiver_engine.app_launcher import open_browser

def inject_browser_state(state):
    """
    Opens browser at exact URL from transfer packet.

    State contains:
      url       → exact URL to open
      pageTitle → page title (fallback if no URL)
    """
    url        = state.get('url')
    page_title = state.get('pageTitle')

    print(f"\n🌐 Browser State Injection:")
    print(f"   URL   : {url}")
    print(f"   Title : {page_title}")
    if url:
        success = open_browser(url)
        if success:
            print(f"✅ Browser opened at: {url}")
        return success
    # Fallback — no URL, search by title
    if page_title:
        search_url = f"https://www.google.com/search?q={page_title}"
        print(f"⚠️  No URL — searching for: {page_title}")
        success = open_browser(search_url)
        return success

    print("⚠️  No URL or title in state")
    return False


# ── Test block ──
if __name__ == "__main__":
    print("🌐 Browser Injector Test")
    print("=" * 40)

    test_state = {
        'url'      : 'https://github.com/StephenMachera/gestflow',
        'pageTitle': 'StephenMachera/gestflow'
    }

    inject_browser_state(test_state)