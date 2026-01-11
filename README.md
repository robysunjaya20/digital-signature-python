# Digital Signature System (Ed25519)

This project is an implementation of a **Digital Signature System** using Python, 
built as a learning project for Cryptography.

The system applies **public key cryptography** to ensure:
- Document authenticity
- Data integrity
- Non-repudiation

---

## 🚀 Features

- Digital signature using **Ed25519**
- Document hashing to ensure integrity
- Timestamp and signer metadata
- QR Code embedded in signed PDF
- Public verification via QR Code
- Preview PDF before signing
- Stateless document verification (no file storage)
- Unique folder per signed document
- Download signed document from verification page
- Modern web interface (FastAPI)

---

## 🛠️ Technologies Used

- Python
- FastAPI
- Ed25519 (public key cryptography)
- QR Code
- PDF processing
- HTML, CSS, JavaScript

---

## 📁 Project Structure
digital-signature/
│
├── backend/
│ ├── main.py
│ ├── crypto/
│ │ ├── sign.py
│ │ ├── verify.py
│ │ ├── qr.py
│ │ ├── pdf_signature.py
│ │ └── merge_pdf.py
│ ├── utils/
│ │ └── verification_id.py
│ └── verification_registry.json
│
├── uploads/
├── keys/
│ ├── private.key
│ └── public.key
│
├── static/
│ └── bg.jpg
│
└── README.md
