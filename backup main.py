from fastapi import FastAPI, UploadFile, File
import shutil
import json
import os

from crypto.sign import sign_document
from crypto.verify import verify_document
from crypto.qr import generate_qr
from crypto.pdf_signature import create_signature_page
from crypto.merge_pdf import merge_pdf

from utils.verification_id import generate_verification_id

from fastapi.responses import HTMLResponse


app = FastAPI()

UPLOAD_DIR = "../uploads/"
PRIVATE_KEY = "../keys/private.key"
PUBLIC_KEY = "../keys/public.key"

@app.post("/sign")
async def sign(file: UploadFile = File(...)):
    # =============================
    # 1. Simpan file PDF
    # =============================
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # =============================
    # 2. Buat digital signature + metadata
    # =============================
    signature_data = sign_document(
        file_path,
        PRIVATE_KEY,
        signer_name="Roby Sunjaya"
    )

    verification_id = generate_verification_id()

    registry_path = "../backend/verification_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    registry[verification_id] = {
        "filename": file.filename,
        "document_hash": signature_data["document_hash"],
        "timestamp": signature_data["timestamp"],
        "signer": signature_data["signer"]["name"],
        "algorithm": signature_data["algorithm"]
    }

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)

    # =============================
    # 3. Generate QR Code
    # =============================
    qr_content = f"http://192.168.2.134:8000/verify-public?id={verification_id}robysunjaya"



    qr_path = os.path.join(UPLOAD_DIR, "qr.png")
    generate_qr(qr_content, qr_path)

    # =============================
    # 4. Buat halaman signature PDF
    # =============================
    signature_page_path = os.path.join(
        UPLOAD_DIR, "signature_page.pdf"
    )

    create_signature_page(
        output_path=signature_page_path,
        signer=signature_data["signer"]["name"],
        timestamp=signature_data["timestamp"],
        algorithm=signature_data["algorithm"],
        qr_path=qr_path
    )

    # =============================
    # 5. Gabungkan PDF asli + signature page
    # =============================
    final_pdf = os.path.join(
        UPLOAD_DIR, "SIGNED_" + file.filename
    )

    merge_pdf(
        original_pdf=file_path,
        signature_pdf=signature_page_path,
        output_pdf=final_pdf
    )

    return {
        "status": "SIGNED",
        "signed_pdf": "SIGNED_" + file.filename,
        "signature_file": file.filename + ".sig.json"
    }

@app.post("/verify")
async def verify(file: UploadFile = File(...), signature: UploadFile = File(...)):
    # =============================
    # 1. Simpan file
    # =============================
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    sig_path = os.path.join(UPLOAD_DIR, signature.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with open(sig_path, "wb") as buffer:
        shutil.copyfileobj(signature.file, buffer)

    # =============================
    # 2. Load signature metadata
    # =============================
    with open(sig_path, "r") as f:
        signature_json = json.load(f)

    # =============================
    # 3. Verifikasi
    # =============================
    valid, message = verify_document(
        file_path,
        signature_json,
        PUBLIC_KEY
    )

    return {
        "valid": valid,
        "message": message,
        "timestamp": signature_json["timestamp"],
        "signer": signature_json["signer"]["name"],
        "algorithm": signature_json["algorithm"]
    }

@app.get("/verify-public", response_class=HTMLResponse)
async def verify_public(id: str):
    registry_path = "../backend/verification_registry.json"

    if not os.path.exists(registry_path):
        return "<h2>❌ Registry verifikasi tidak ditemukan</h2>"

    with open(registry_path, "r") as f:
        registry = json.load(f)

    if id not in registry:
        return "<h2>❌ Data verifikasi tidak ditemukan</h2>"

    data = registry[id]

    return f"""
    <html>
    <head>
        <title>Verifikasi Dokumen</title>
    </head>
    <body style="font-family:Arial; padding:40px">
        <h2>✅ Dokumen TERVERIFIKASI</h2>
        <hr>
        <p><b>Nama File:</b> {data['filename']}</p>
        <p><b>Penandatangan:</b> {data['signer']}</p>
        <p><b>Waktu Tanda Tangan:</b> {data['timestamp']}</p>
        <p><b>Algoritma:</b> {data['algorithm']}</p>
        <p><b>Status:</b> <span style="color:green">VALID</span></p>
        <p><b><center>Dibuat Oleh Roby Sunjaya </center></b></p>
    </body>
    </html>
    """
