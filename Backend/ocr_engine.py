import pytesseract
from pdf2image import convert_from_bytes
import os
from Backend.config import TESSERACT_PATH, POPPLER_PATH, OUTPUT_DIR

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def run_ocr(pdf_bytes: bytes, original_filename: str) -> str:
    """
    Returns extracted text directly (storage handled by main.py in DB)
    """
    print(f"OCR processing: {original_filename}")

    try:
        pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH, dpi=300)

        combined_text = ""
        for page_num, page in enumerate(pages, 1):
            text = pytesseract.image_to_string(page)
            combined_text += f"\n--- Page {page_num} ---\n{text}"

        return combined_text

    except Exception as e:
        print(f"OCR error: {str(e)}")
        return f"OCR_ERROR: {str(e)}"

