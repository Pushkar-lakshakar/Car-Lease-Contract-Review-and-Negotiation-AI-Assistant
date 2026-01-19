from fastapi import FastAPI, UploadFile, File
from ocr_engine import run_ocr
from gemini import extract_sla_from_text
from vehicle_lookup import get_vehicle_info
from risk_analysis import analyze_risk
import os
import json
import unicodedata
import re
from datetime import datetime

app = FastAPI(
    title="Car Lease AI Assistant",
    version="1.0",
    description="Upload a lease/loan agreement PDF and get SLA fields, Vehicle API info, and Risk Analysis."
)

OUTPUT_DIR = "project_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------------------------------------
# DETECT VEHICLE NUMBER FROM TEXT
# -------------------------------------------------------
def detect_vehicle_number(text: str):
    """
    Extracts an Indian vehicle number reliably from OCR text.
    """
    # Normalize weird unicode characters
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    # Robust Indian license plate pattern
    pattern = r"[A-Z]{2}[\-\s]*\d{1,2}[\-\s]*[A-Z]{1,3}[\-\s]*\d{3,4}"

    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None

    # Clean up hyphens/spaces
    cleaned = re.sub(r'[^A-Za-z0-9]', '', match.group(0).upper())
    return cleaned


# -------------------------------------------------------
# SAVE FINAL USER-FACING JSON (Output B)
# -------------------------------------------------------
def save_final_json(data: dict, pdf_original_name: str):
    """
    Saves:
        project_output/<PDFName>.json
    """
    clean_name = os.path.splitext(pdf_original_name)[0] + ".json"
    final_path = os.path.join(OUTPUT_DIR, clean_name)

    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return final_path


# -------------------------------------------------------
# MAIN API ENDPOINT
# -------------------------------------------------------
@app.post("/analyze-lease")
async def analyze_lease(file: UploadFile = File(...)):
    """
    Pipeline:
    1. Read PDF in memory
    2. OCR → permanent TXT file
    3. SLA extraction using Gemini
    4. Vehicle number detection
    5. Vehicle API lookup (cache)
    6. Risk analysis
    7. Save final JSON with user-facing result
    """
    try:
        # ---------------------------------------------------
        # 1. Read PDF into memory (NO temp PDF created)
        # ---------------------------------------------------
        pdf_bytes = await file.read()

        # ---------------------------------------------------
        # 2. Run OCR → store TXT in project_output
        # ---------------------------------------------------
        txt_path = run_ocr(pdf_bytes, original_filename=file.filename)
        with open(txt_path, "r", encoding="utf-8") as f:
            ocr_text = f.read()

        # ---------------------------------------------------
        # 3. SLA Extraction (Gemini 2.5 Flash)
        # ---------------------------------------------------
        sla_fields = extract_sla_from_text(ocr_text)

        # ---------------------------------------------------
        # 4. Vehicle Detection + API Lookup (cached)
        # ---------------------------------------------------
        vehicle_no = detect_vehicle_number(ocr_text)

        if vehicle_no:
            vehicle_info = get_vehicle_info(vehicle_no)
        else:
            vehicle_info = {
                "status": "failed",
                "error": "No vehicle number detected in document"
            }

        # ---------------------------------------------------
        # 5. Risk Analysis
        # ---------------------------------------------------
        risk_result = analyze_risk(sla_fields, vehicle_info)

        # ---------------------------------------------------
        # 6. Build Final JSON (Output B → <PDFName>.json)
        # ---------------------------------------------------
        full_report = {
            "metadata": {
                "original_pdf": file.filename,
                "generated_at": datetime.now().isoformat(),
                "vehicle_detected": vehicle_no
            },
            "ocr_text_file": os.path.basename(txt_path),
            "sla_extraction": sla_fields,
            "vehicle_details": vehicle_info,
            "risk_analysis": risk_result
        }

        json_output_path = save_final_json(full_report, file.filename)

        # ---------------------------------------------------
        # 7. Response
        # ---------------------------------------------------
        return {
            "status": "success",
            "message": "Analysis completed successfully.",
            "pdf_txt_saved_as": os.path.basename(txt_path),
            "json_saved_as": os.path.basename(json_output_path),
            "data": full_report
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
