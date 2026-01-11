import qrcode

def generate_qr(data, output_path):
    qr = qrcode.make(data)
    qr.save(output_path)
