import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

CACHE_DIR = "vehicle_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Set to True only when you want to FORCE a fresh API call
FORCE_REFRESH = False


def get_cache_path(vehicle_number: str):
    clean = vehicle_number.replace(" ", "").upper().strip()
    return os.path.join(CACHE_DIR, f"{clean}.json")


# -------------------------------------------------------
# DATE NORMALIZER
# -------------------------------------------------------
def normalize_date(value):
    """
    Normalize any date format into YYYY-MM-DD.
    Works for:
    - 31-Oct-2032
    - 23/11/2024
    - 8/2017
    - 2017-11-24
    """
    if not value:
        return None

    value = str(value).strip()
    import datetime

    # Already YYYY-MM-DD
    if len(value) == 10 and value.count("-") == 2:
        return value

    # DD-MMM-YYYY
    try:
        dt = datetime.datetime.strptime(value, "%d-%b-%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    # DD/MM/YYYY
    try:
        dt = datetime.datetime.strptime(value, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    # Month/Year: 8/2017
    if "/" in value:
        parts = value.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            yr = parts[1]
            return f"{yr}-01-01"

    return None


# -------------------------------------------------------
# API CALL + CACHE HANDLING
# -------------------------------------------------------
def get_vehicle_info(vehicle_number: str):
    cache_file = get_cache_path(vehicle_number)

    # 1. Use CACHE if available
    if os.path.exists(cache_file) and not FORCE_REFRESH:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Call API (only if cache missing or forced)
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"status": "failed", "error": "RAPIDAPI_KEY missing in .env"}

    url = "https://vehicle-rc-information-v2.p.rapidapi.com/"

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "vehicle-rc-information-v2.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    payload = {"vehicle_number": vehicle_number}

    try:
        resp = requests.post(url, headers=headers, json=payload)
        api_data = resp.json()
    except Exception as e:
        return {"status": "failed", "error": f"API error: {str(e)}"}

    data = api_data.get("response", api_data)
    if not isinstance(data, dict):
        return {"status": "failed", "raw_response": api_data}

    # ---------------------------------------------------
    # STANDARDIZED FORMAT (required for risk_analysis.py)
    # ---------------------------------------------------

    result = {
        "status": "success",
        "result": {
            "reg_no": data.get("license_plate"),
            "owner_name": data.get("owner_name"),
            "model": data.get("brand_model"),
            "class": data.get("class"),
            "fuel_descr": data.get("fuel_type"),
            "color": data.get("color"),

            # Dates
            "reg_date": normalize_date(data.get("registration_date")),
            "manufacturing_yr": (
                int(data.get("manufacturing_date").split("/")[-1])
                if data.get("manufacturing_date") else None
            ),

            "vehicle_seat_capacity": data.get("seating_capacity"),
            "blacklist_status": data.get("blacklist_status"),
            "status": data.get("rc_status"),

            # Insurance
            "vehicle_insurance_details": {
                "insurance_upto": normalize_date(data.get("insurance_expiry"))
            },

            # Tax / fitness
            "tax_upto": normalize_date(data.get("tax_upto")),
            "fit_upto": normalize_date(data.get("fit_up_to")),
        }
    }

    # ---------------------------------------------------
    # SAVE TO CACHE so no repeated API calls
    # ---------------------------------------------------
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    return result
