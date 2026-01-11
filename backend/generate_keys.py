from nacl.signing import SigningKey

# Generate private key (32-byte seed)
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

# Simpan private key (32 bytes)
with open("../keys/private.key", "wb") as f:
    f.write(signing_key.encode())

# Simpan public key (32 bytes)
with open("../keys/public.key", "wb") as f:
    f.write(verify_key.encode())

print("Ed25519 key pair berhasil dibuat")
