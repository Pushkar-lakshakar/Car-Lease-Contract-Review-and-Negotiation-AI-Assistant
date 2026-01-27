import pytesseract
from pdf2image import convert_from_bytes
import os
from config import TESSERACT_PATH, POPPLER_PATH, OUTPUT_DIR

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def run_ocr(pdf_bytes: bytes, original_filename: str) -> str:
    """
    Save OCR text to: project_output/<pdf_name>.txt
    """
    # Create filename
    base_name = os.path.splitext(original_filename)[0]
    txt_filename = f"{base_name}.txt"
    txt_path = os.path.join(OUTPUT_DIR, txt_filename)
    
    print(f"OCR processing: {original_filename}")
    
    try:
        # Convert PDF to images
        pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH, dpi=300)
        
        combined_text = ""
        for page_num, page in enumerate(pages, 1):
            text = pytesseract.image_to_string(page)
            combined_text += f"\n--- Page {page_num} ---\n{text}"
        
        # Save text file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(combined_text)
        
        print(f"OCR saved: {txt_path}")
        return txt_path
        
    except Exception as e:
        print(f"OCR error: {str(e)}")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"OCR_ERROR: {str(e)}")
        return txt_path

