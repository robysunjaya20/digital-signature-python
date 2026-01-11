import json, base64
from nacl.signing import SigningKey
from datetime import datetime, timezone

# load CA private key
with open("certificates/ca_private.key", "rb") as f:
    ca_key = SigningKey(f.read())

# load signer public key
with open("../keys/public.key", "rb") as f:
    signer_pub = f.read()

cert = {
    "version": "Mini X.509 v1",
    "serial_number": "RS-2026-0001",
    "subject": {
        "name": "Roby Sunjaya",
        "email": "robysunjaya9@gmail.com",
        "organization": "Universitas Pelita Bangsa"
    },
    "issuer": {
        "name": "Digital Signature CA",
        "country": "ID"
    },
    "validity": {
        "not_before": datetime.now(timezone.utc).isoformat(),
        "not_after": "2028-01-01T00:00:00Z"
    },
    "public_key": base64.b64encode(signer_pub).decode(),
    "signature_algorithm": "Ed25519"
}

# sign certificate
payload = json.dumps(cert, sort_keys=True).encode()
cert_signature = ca_key.sign(payload).signature

cert["ca_signature"] = base64.b64encode(cert_signature).decode()

with open("certificates/roby_sunjaya.cert.json", "w") as f:
    json.dump(cert, f, indent=2)

print("Certificate issued")
