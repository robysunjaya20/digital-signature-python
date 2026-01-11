from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import shutil, json, os, uuid
from datetime import datetime
import tempfile

from crypto.sign import sign_document
from crypto.verify import verify_document
from crypto.qr import generate_qr
from crypto.pdf_signature import create_signature_page
from crypto.merge_pdf import merge_pdf
from utils.verification_id import generate_verification_id

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "../uploads")
REGISTRY_PATH = os.path.join(BASE_DIR, "verification_registry.json")
PRIVATE_KEY = os.path.join(BASE_DIR, "../keys/private.key")
PUBLIC_KEY = os.path.join(BASE_DIR, "../keys/public.key")

SERVER_HOST = "http://192.168.2.134:8000"

os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(REGISTRY_PATH):
    with open(REGISTRY_PATH, "w") as f:
        json.dump({}, f)

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def create_unique_upload_dir():
    folder = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    path = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return path

@app.post("/sign")
async def sign(file: UploadFile = File(...)):
    doc_dir = create_unique_upload_dir()

    # Simpan PDF asli
    file_path = os.path.join(doc_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Digital signature
    signature_data = sign_document(
        file_path,
        PRIVATE_KEY,
        signer_name="Roby Sunjaya"
    )

    # Simpan signature JSON
    with open(file_path + ".sig.json", "w") as f:
        json.dump(signature_data, f, indent=2)

    verification_id = generate_verification_id()

    # Registry
    with open(REGISTRY_PATH, "r") as f:
        registry = json.load(f)

    registry[verification_id] = {
        "filename": file.filename,
        "signed_filename": "SIGNED_" + file.filename,
        "doc_dir": doc_dir,
        "timestamp": signature_data["timestamp"],
        "signer": signature_data["signer"]["name"],
        "algorithm": signature_data["algorithm"]
    }

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    # QR Code
    qr_content = f"{SERVER_HOST}/verify-public?id={verification_id}"
    qr_path = os.path.join(doc_dir, "qr.png")
    generate_qr(qr_content, qr_path)

    # Signature page
    signature_page = os.path.join(doc_dir, "signature_page.pdf")
    create_signature_page(
        output_path=signature_page,
        signer=signature_data["signer"]["name"],
        timestamp=signature_data["timestamp"],
        algorithm=signature_data["algorithm"],
        qr_path=qr_path
    )

    # Final PDF
    final_pdf = os.path.join(doc_dir, "SIGNED_" + file.filename)
    merge_pdf(file_path, signature_page, final_pdf)

    return {
        "status": "SIGNED",
        "verification_id": verification_id,
        "signed_pdf": "SIGNED_" + file.filename
    }

@app.post("/verify")
async def verify(
    file: UploadFile = File(...),
    signature: UploadFile = File(...)
):
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        shutil.copyfileobj(file.file, tmp_pdf)
        tmp_pdf.close()  

        signature_bytes = await signature.read()
        signature_json = json.loads(signature_bytes.decode("utf-8"))

        valid, message = verify_document(
            tmp_pdf.name,
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

    finally:
        # HAPUS FILE TEMP (CLEAN & AMAN)
        if os.path.exists(tmp_pdf.name):
            os.remove(tmp_pdf.name)

@app.get("/verify-public", response_class=HTMLResponse)
async def verify_public(id: str):
    with open(REGISTRY_PATH, "r") as f:
        registry = json.load(f)

    if id not in registry:
        return "<h2>❌ Data verifikasi tidak ditemukan</h2>"

    d = registry[id]

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verifikasi Dokumen</title>
<style>
body {{
 background: linear-gradient(rgba(0,0,0,.45),rgba(0,0,0,.45)),
 url('/static/bgon.jpg') center/cover fixed;
 font-family: Arial;
}}
.card {{
 max-width:480px; margin:40px auto; background:rgba(255,255,255,.8);
 padding:30px; border-radius:12px;
 box-shadow:0 10px 25px rgba(0,0,0,.15);
}}
.badge {{ background:#e8f5e9; color:#2e7d32; padding:6px 14px; border-radius:20px; }}
.badge.valid {{
    background: #e8f5e9;
    color: #2e7d32;
    font-weight: bold;
}}
.download {{
    display:block;
    width:100%;
    margin:20px auto 0;
    padding:12px;
    background:#2563eb;
    color:white;
    border:none;
    border-radius:8px;
    font-size:16px;
    font-weight:600;
    cursor:pointer;
    text-align:center;
}}
</style>
</head>
<body>
<div class="card">
<h2 id="docTitle">🔍 Informasi Dokumen</h2>
<span class="badge" id="docStatus">Belum Diverifikasi</span>
<p><b>File:</b> {d['filename']}</p>
<p><b>Penandatangan:</b> {d['signer']}</p>
<p><b>Waktu:</b> {d['timestamp']}</p>
<p><b>Algoritma:</b> {d['algorithm']}</p>

<button class="download" onclick="downloadDoc()">⬇ Download Dokumen</button>
<div id="downloadStatus" style="
    display:none; 
    margin-top:15px; 
    padding:12px; 
    border-radius:8px; 
    font-size:14px; 
    background:#ffebee; 
    color:#c62828;">
</div>

<script>
async function downloadDoc() {{
    const statusBox = document.getElementById("downloadStatus");
    statusBox.style.display = "none";

    const res = await fetch("/download/{id}");

    if (!res.ok) {{
        const data = await res.json();
        statusBox.innerText = "❌ " + (data.message || "Dokumen tidak valid atau sudah berubah");
        statusBox.style.display = "block";
        return;
    }}

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    document.getElementById("docTitle").innerText = "✔️ Dokumen Terverifikasi";
    const statusBadge = document.getElementById("docStatus");
    statusBadge.innerText = "VALID";
    statusBadge.classList.add("valid");

    const a = document.createElement("a");
    a.href = url;
    a.download = "SIGNED_{d['filename']}";
    document.body.appendChild(a);
    a.click();
    a.remove();
}}
</script>

<p style="margin-top:20px;font-size:13px;text-align:center;color:#555">
Sistem Digital Signature<br><b>Roby Sunjaya</b>
</p>
</div>
</body>
</html>
"""

@app.get("/sign-page", response_class=HTMLResponse)
async def sign_page():
    return """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Tanda Tangan Digital</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background:
                linear-gradient(
                    rgba(0,0,0,0.45),
                    rgba(0,0,0,0.45)
                ),
                url('/static/bg.jpg') no-repeat center center fixed;
            background-size: cover;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .card {
            background: #ffffff;
            width: 100%;
            max-width: 520px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            padding: 30px;
        }
        h1 {
            font-size: 22px;
            text-align: center;
            margin-bottom: 6px;
        }
        .subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 20px;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
        }
        .preview {
            display: none;
            margin-bottom: 20px;
        }
        iframe {
            width: 100%;
            height: 320px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover {
            background: #1e40af;
        }
        .loader {
            display: none;
            text-align: center;
            margin-top: 15px;
            color: #374151;
            font-size: 14px;
        }
        .footer {
            margin-top: 25px;
            font-size: 13px;
            color: #6b7280;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>Tanda Tangan Digital</h1>
        <div class="subtitle">
            Preview dokumen sebelum ditandatangani
        </div>

        <form id="signForm">
            <input type="file" id="file" accept="application/pdf" required>

            <div class="preview" id="previewBox">
                <iframe id="pdfPreview"></iframe>
            </div>

            <button type="submit">Tandatangani Dokumen</button>
        </form>

        <div class="loader" id="loader">
            ⏳ Proses tanda tangan sedang berlangsung...
        </div>

        <div class="footer">
            Sistem Digital Signature (Ed25519)<br>
            Dokumen akan INVALID jika diubah
        </div>
    </div>
</div>

<script>
const fileInput = document.getElementById("file");
const previewBox = document.getElementById("previewBox");
const pdfPreview = document.getElementById("pdfPreview");

fileInput.addEventListener("change", function() {
    const file = this.files[0];
    if (file && file.type === "application/pdf") {
        const fileURL = URL.createObjectURL(file);
        pdfPreview.src = fileURL;
        previewBox.style.display = "block";
    } else {
        previewBox.style.display = "none";
    }
});

document.getElementById("signForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    if (!fileInput.files.length) return;

    document.getElementById("loader").style.display = "block";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const response = await fetch("/sign", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    document.getElementById("loader").style.display = "none";

    if (result.signed_pdf) {
        alert("Dokumen berhasil ditandatangani!\\n\\nFile: " + result.signed_pdf);
    } else {
        alert("Terjadi kesalahan saat menandatangani dokumen");
    }
});
</script>
</body>
</html>
"""

@app.get("/verify-page", response_class=HTMLResponse)
async def verify_page():
    return """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Verifikasi Dokumen</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background:
                    linear-gradient(
                        rgba(0,0,0,0.45),
                        rgba(0,0,0,0.45)
                    ),
                    url('/static/bg.jpg') no-repeat center center fixed;
                background-size: cover;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                margin: 0;
                padding: 0;
        }
        .container {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .card {
            background: #ffffff;
            width: 100%;
            max-width: 480px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            padding: 30px;
        }
        h1 {
            font-size: 22px;
            text-align: center;
            margin-bottom: 6px;
        }
        .subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 25px;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover {
            background: #1e40af;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            display: none;
        }
        .valid {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .invalid {
            background: #ffebee;
            color: #c62828;
        }
        .footer {
            margin-top: 25px;
            font-size: 13px;
            color: #6b7280;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>Verifikasi Dokumen</h1>
        <div class="subtitle">
            Upload dokumen dan file signature untuk memverifikasi keaslian
        </div>

        <form id="verifyForm">
            <input type="file" id="doc" accept="application/pdf" required>
            <input type="file" id="sig" accept=".json" required>
            <button type="submit">Verifikasi Dokumen</button>
        </form>

        <div class="result" id="result"></div>

        <div class="footer">
            Sistem Digital Signature (Ed25519)<br>
            Perubahan sekecil apa pun akan membuat dokumen INVALID
        </div>
    </div>
</div>

<script>
document.getElementById("verifyForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const doc = document.getElementById("doc").files[0];
    const sig = document.getElementById("sig").files[0];

    if (!doc || !sig) return;

    const formData = new FormData();
    formData.append("file", doc);
    formData.append("signature", sig);

    const response = await fetch("/verify", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    const resultDiv = document.getElementById("result");

    resultDiv.style.display = "block";

    if (result.valid) {
        resultDiv.className = "result valid";
        resultDiv.innerHTML = `
            ✔️ <b>DOKUMEN VALID</b><br>
            Penandatangan: ${result.signer}<br>
            Waktu: ${result.timestamp}<br>
            Algoritma: ${result.algorithm}
        `;
    } else {
        resultDiv.className = "result invalid";
        resultDiv.innerHTML = `
            ❌ <b>DOKUMEN TIDAK VALID</b><br>
            ${result.message}
        `;
    }
});
</script>
</body>
</html>
"""

from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse
@app.get("/download/{verification_id}")
async def download_signed_file(verification_id: str):
    # 1️⃣ Load registry
    with open(REGISTRY_PATH, "r") as f:
        registry = json.load(f)

    if verification_id not in registry:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")

    d = registry[verification_id]
    doc_dir = d["doc_dir"]

    original_pdf = os.path.join(doc_dir, d["filename"])
    sig_path = original_pdf + ".sig.json"
    signature_page = os.path.join(doc_dir, "signature_page.pdf")

    # 2️⃣ Pastikan file ada
    if not all(map(os.path.exists, [original_pdf, sig_path, signature_page])):
        raise HTTPException(status_code=404, detail="File tidak lengkap")

    # 3️⃣ Load signature JSON
    with open(sig_path, "r") as f:
        signature_json = json.load(f)

    # 4️⃣ VERIFIKASI ULANG (INTI KEAMANAN)
    valid, message = verify_document(
        original_pdf,
        signature_json,
        PUBLIC_KEY
    )

    if not valid:
        return JSONResponse(
            status_code=400,
            content={"status": "INVALID", "message": "Dokumen tidak valid"}
        )

    # 5️⃣ Jika VALID → gabungkan PDF + signature_page
    final_pdf = os.path.join(doc_dir, "SIGNED_" + d["filename"])

    if not os.path.exists(final_pdf):
        merge_pdf(original_pdf, signature_page, final_pdf)

    # 6️⃣ Download hasil FINAL
    return FileResponse(
        final_pdf,
        filename="SIGNED_" + d["filename"],
        media_type="application/pdf"
    )