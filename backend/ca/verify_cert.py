import json, base64
from nacl.signing import VerifyKey

with open("certificates/ca_public.key", "rb") as f:
    ca_pub = VerifyKey(f.read())

with open("certificates/roby_sunjaya.cert.json") as f:
    cert = json.load(f)

sig = base64.b64decode(cert["ca_signature"])

payload = cert.copy()
del payload["ca_signature"]

payload_bytes = json.dumps(payload, sort_keys=True).encode()

ca_pub.verify(payload_bytes, sig)
print("Certificate VALID")
