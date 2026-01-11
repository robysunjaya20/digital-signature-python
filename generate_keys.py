from nacl.signing import SigningKey
import os

KEY_DIR = "keys"

# Buat folder keys jika belum ada
os.makedirs(KEY_DIR, exist_ok=True)

# Generate key pair Ed25519
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

# Simpan private key
with open(f"{KEY_DIR}/private.key", "wb") as f:
    f.write(signing_key.encode())

# Simpan public key
with open(f"{KEY_DIR}/public.key", "wb") as f:
    f.write(verify_key.encode())

print("✅ Key pair berhasil dibuat")
print("🔒 private.key (RAHASIA)")
print("🔓 public.key (UNTUK VERIFIKASI)")
