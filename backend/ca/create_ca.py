from nacl.signing import SigningKey
import base64, os

os.makedirs("certificates", exist_ok=True)

ca_key = SigningKey.generate()
ca_pub = ca_key.verify_key

with open("certificates/ca_private.key", "wb") as f:
    f.write(ca_key.encode())

with open("certificates/ca_public.key", "wb") as f:
    f.write(ca_pub.encode())

print("CA keys generated")
