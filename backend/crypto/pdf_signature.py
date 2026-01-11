from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_signature_page(
    output_path,
    signer,
    timestamp,
    algorithm,
    qr_path
):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 80, "DIGITAL SIGNATURE")

    c.setFont("Helvetica", 11)
    c.drawString(50, height - 120, f"Penandatangan : {signer}")
    c.drawString(50, height - 145, f"Waktu         : {timestamp}")
    c.drawString(50, height - 170, f"Algoritma     : {algorithm}")

    c.drawString(50, height - 210,
        "Dokumen ini telah ditandatangani secara digital."
    )
    c.drawString(50, height - 230,
        "Perubahan sekecil apapun akan membuat signature tidak valid."
    )

    c.drawImage(qr_path, 50, height - 400, width=120, height=120)

    c.showPage()
    c.save()
