from PyPDF2 import PdfMerger

def merge_pdf(original_pdf, signature_pdf, output_pdf):
    merger = PdfMerger()
    merger.append(original_pdf)
    merger.append(signature_pdf)
    merger.write(output_pdf)
    merger.close()
