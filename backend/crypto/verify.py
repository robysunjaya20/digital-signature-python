from nacl.signing import VerifyKey
import hashlib, json, base64

def verify_document(file_path, signature_json, public_key_path):
    # baca dokumen
    with open(file_path, "rb") as f:
        data = f.read()

    # hash ulang dokumen
    current_hash = hashlib.sha256(data).digest()
    current_hash_b64 = base64.b64encode(current_hash).decode()

    # bandingkan hash
    if current_hash_b64 != signature_json["document_hash"]:
        return False, "Dokumen telah diubah"

    # reconstruct payload
    payload = json.dumps({
        "document_hash": signature_json["document_hash"],
        "timestamp": signature_json["timestamp"],
        "signer": signature_json["signer"]["name"]
    }, sort_keys=True).encode()

    # verify signature
    with open(public_key_path, "rb") as f:
        verify_key = VerifyKey(f.read())

    try:
        verify_key.verify(
            payload,
            base64.b64decode(signature_json["signature"])
        )
        return True, "Signature VALID"
    except:
        return False, "Signature TIDAK VALID"
