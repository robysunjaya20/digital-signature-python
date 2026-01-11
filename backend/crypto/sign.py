from nacl.signing import SigningKey
import hashlib, json, base64
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
def sign_document(file_path, private_key_path, signer_name="Unknown"):
    # baca dokumen
    with open(file_path, "rb") as f:
        data = f.read()

    # hash dokumen
    doc_hash = hashlib.sha256(data).digest()
    doc_hash_b64 = base64.b64encode(doc_hash).decode()

    # timestamp UTC
    timestamp = datetime.now(WIB).isoformat()

    # payload yang akan ditandatangani
    payload = json.dumps({
        "document_hash": doc_hash_b64,
        "timestamp": timestamp,
        "signer": signer_name
    }, sort_keys=True).encode()

    # sign
    with open(private_key_path, "rb") as f:
        signing_key = SigningKey(f.read())

    signature = signing_key.sign(payload).signature

    return {
        "algorithm": "Ed25519",
        "hash_algorithm": "SHA-256",
        "document_hash": doc_hash_b64,
        "timestamp": timestamp,
        "signature": base64.b64encode(signature).decode(),
        "signer": {
            "name": signer_name,
            "system": "Digital Signature System v1"
        }
    }
