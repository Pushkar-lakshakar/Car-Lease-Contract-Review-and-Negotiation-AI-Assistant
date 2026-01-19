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
    version="1.2",
    description="Upload a lease/loan agreement PDF and get SLA fields, Vehicle API info, and Risk Analysis."
)

OUTPUT_DIR = "project_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# VALID PLATE FORMATS (INDIA)

PLATE_REGEX = re.compile(
    r"\b([A-Z]{2}\s?-?\s?\d{1,2}\s?-?\s?[A-Z]{1,3}\s?-?\s?\d{3,4})\b",
    re.IGNORECASE
)

def is_valid_plate(text: str) -> bool:
    """Strict Indian license plate validation."""
    if not text:
        return False

    t = re.sub(r"[^A-Za-z0-9]", "", text).upper()

    # Format like MH12AB1234
    pattern = r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,4}$"
    return re.match(pattern, t) is not None


# DETECT VEHICLE NUMBER
# (Keyword → Strict Regex → Cleanup → Validation)
def detect_vehicle_number(text: str):
    """
    1. First detect explicitly from lines containing:
       'License Plate', 'Registration No', 'Reg No'

    2. Then fallback to regex but EXCLUDE VIN patterns.
    """

    if not text:
        return None

    # Normalize text
    clean_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    # KEYWORD BASED EXTRACTION
    KEYWORDS = ["license plate", "plate", "registration no", "reg no", "registration number"]

    for line in clean_text.split("\n"):
        line_l = line.lower()
        if any(k in line_l for k in KEYWORDS):

            # Extract all plate-like patterns
            candidates = PLATE_REGEX.findall(line)
            for c in candidates:
                cleaned = re.sub(r"[^A-Za-z0-9]", "", c).upper()
                if is_valid_plate(cleaned):
                    return cleaned

    # REGEX SCAN (EXCLUDING VIN)
    matches = PLATE_REGEX.findall(clean_text)

    for m in matches:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", m).upper()

        # EXCLUDE VIN-like sequences (length > 10, mixed upper/digits)
        if len(cleaned) > 10:  
            continue

        if is_valid_plate(cleaned):
            return cleaned

    return None  # Nothing valid found


# SAVE USER-FACING OUTPUT JSON
def save_final_json(data: dict, pdf_name: str):
    clean = os.path.splitext(pdf_name)[0] + ".json"
    path = os.path.join(OUTPUT_DIR, clean)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return path


# MAIN API ENDPOINT
@app.post("/analyze-lease")
async def analyze_lease(file: UploadFile = File(...)):
    try:
        # 1. Read PDF in memory
        pdf_bytes = await file.read()

        # 2. OCR → permanent TXT file
        txt_path = run_ocr(pdf_bytes, original_filename=file.filename)
        ocr_text = open(txt_path, "r", encoding="utf-8").read()

        # 3. SLA extraction (Gemini)
        sla_fields = extract_sla_from_text(ocr_text)

        # 4. Detect Vehicle Number
        vehicle_no = detect_vehicle_number(ocr_text)

        if vehicle_no:
            vehicle_info = get_vehicle_info(vehicle_no)
        else:
            vehicle_info = {
                "status": "failed",
                "error": "No valid license plate detected in document"
            }

        # 5. Risk Analysis
        risk_result = analyze_risk(sla_fields, vehicle_info)

        # 6. Build Final JSON Output
        report = {
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

        saved_path = save_final_json(report, file.filename)

        return {
            "status": "success",
            "message": "Lease analysis completed.",
            "txt_saved_as": os.path.basename(txt_path),
            "json_saved_as": os.path.basename(saved_path),
            "data": report
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
