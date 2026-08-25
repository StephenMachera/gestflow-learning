# save as get_ext_id.py
import hashlib
import base64
import sys

def get_extension_id(pem_path):
    with open(pem_path, 'rb') as f:
        pem_data = f.read()

    # Remove header and footer lines
    lines   = pem_data.decode().strip().split('\n')
    key_b64 = ''.join(lines[1:-1])

    # Decode base64 to get raw key bytes
    key_bytes = base64.b64decode(key_b64)

    # SHA256 hash of key bytes
    key_hash = hashlib.sha256(key_bytes).hexdigest()[:32]

    # Convert to Chrome's a-p encoding
    ext_id = ''
    for char in key_hash:
        ext_id += chr(int(char, 16) + ord('a'))

    return ext_id

pem_path = './gestflow_03_browser_extension.pem'
ext_id   = get_extension_id(pem_path)

print(f"\n✅ Your Extension ID:")
print(f"   {ext_id}")
print(f"\nCopy this ID — you will need it for:")
print(f"  → update.xml")
print(f"  → Chrome policy file")
print(f"  → setup.py")