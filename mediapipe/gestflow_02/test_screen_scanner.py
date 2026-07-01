import time
from content_classifier import classify_content
from screen_reader import get_active_content

print("🚀 INTEGRATION TEST ACTIVE")
print("You have 5 seconds to switch focus to VLC, Chrome, or VSCode...")
time.sleep(5)

raw_window = get_active_content()

# pass the raw window to gestflow content_classifier
final_state = classify_content(raw_window)
print('the final content state')
import json
print(json.dumps(final_state,indent=4))