import os
from PyPDF2 import PdfReader
import sys

def is_valid_pdf(file_path):
    if not os.path.isfile(file_path):
        return False

    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            # Attempt to read at least one page to ensure the PDF is valid.
            if reader.pages:
                _ = reader.pages[0]
        return True
    except Exception:
        return False

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python pdf.py /path/to/document.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    if is_valid_pdf(file_path):
        print("The PDF is valid.")
    else:
        print("The PDF is not valid.")