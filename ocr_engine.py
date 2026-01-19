import pytesseract
from pdf2image import convert_from_bytes
import os

# Path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Path to Poppler (required for pdf2image)
POPPLER_PATH = r"C:\poppler\Library\bin"

# Output folder for OCR TXT
OUTPUT_DIR = "project_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# OCR ENGINE

def run_ocr(pdf_bytes: bytes, original_filename: str) -> str:
    """
    Creates ONE FILE:
        project_output/<PDFName>.txt

    Returns:
        permanent_txt_path (str)
    """

    # Final TXT path
    clean_name = os.path.splitext(original_filename)[0] + ".txt"
    permanent_txt_path = os.path.join(OUTPUT_DIR, clean_name)

    try:
        # Convert PDF bytes → list of images
        pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)

        combined_text = ""

        # OCR each page
        for page in pages:
            text = pytesseract.image_to_string(page)
            combined_text += text + "\n\n"

        # Save permanent OCR TXT file
        with open(permanent_txt_path, "w", encoding="utf-8") as f:
            f.write(combined_text)

        return permanent_txt_path

    except Exception as e:
        # If OCR fails, still save a meaningful error file
        error_msg = f"OCR_ERROR: {str(e)}"

        with open(permanent_txt_path, "w", encoding="utf-8") as f:
            f.write(error_msg)

        return permanent_txt_path
