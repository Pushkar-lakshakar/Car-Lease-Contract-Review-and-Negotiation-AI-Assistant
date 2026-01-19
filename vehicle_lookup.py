import os
import json
import requests
from dotenv import load_dotenv
import re

load_dotenv()

# CACHE DIRECTORY
CACHE_DIR = "vehicle_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

FORCE_REFRESH = False  # Set True to force re-API call


# LICENSE PLATE VALIDATION (INDIAN PLATES)
def is_valid_plate(num: str) -> bool:
    if not num:
        return False

    num = num.replace(" ", "").replace("-", "").upper()

    # Valid Indian format: MH12AB1234
    pattern = r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,4}$"
    return re.match(pattern, num) is not None


# CACHE
def cache_path(vehicle_number: str):
    clean = vehicle_number.replace(" ", "").upper().strip()
    return os.path.join(CACHE_DIR, f"{clean}.json")


# DATE NORMALIZER
def normalize_date(value):
    if not value:
        return None

    value = str(value).strip()

    import datetime

    # Already ISO
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

    # 8/2017 → 2017-01-01
    if "/" in value:
        parts = value.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[1]}-01-01"

    return None


# MAIN LOOKUP FUNCTION

def get_vehicle_info(vehicle_number: str):

    # Reject invalid numbers
    if not is_valid_plate(vehicle_number):
        return {
            "status": "invalid_vehicle_number",
            "error": f"{vehicle_number} is not a valid Indian license plate",
            "result": {}
        }

    # Check cache
    cpath = cache_path(vehicle_number)

    if os.path.exists(cpath) and not FORCE_REFRESH:
        with open(cpath, "r", encoding="utf-8") as f:
            return json.load(f)

    # API request
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {
            "status": "failed",
            "error": "RAPIDAPI_KEY missing in .env",
            "result": {}
        }

    url = "https://vehicle-rc-information-v2.p.rapidapi.com/"

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "vehicle-rc-information-v2.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    payload = {"vehicle_number": vehicle_number}

    try:
        response = requests.post(url, headers=headers, json=payload)
        raw_data = response.json()
    except Exception as e:
        return {"status": "failed", "error": str(e), "result": {}}

    # Extract "response" key or fallback
    data = raw_data.get("response", raw_data)
    if not isinstance(data, dict):
        data = {}

    # If API returned nothing
    if not data.get("license_plate"):
        result = {
            "status": "vehicle_not_found",
            "error": "Vehicle number not found in RTO database",
            "result": {}
        }
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
        return result

    # Standardize fields (for risk analysis)
    out = {
        "status": "success",
        "result": {
            "reg_no": data.get("license_plate"),
            "owner_name": data.get("owner_name"),
            "model": data.get("brand_model"),
            "class": data.get("class"),
            "fuel_descr": data.get("fuel_type"),
            "color": data.get("color"),

            "reg_date": normalize_date(data.get("registration_date")),

            "manufacturing_yr": (
                int(data.get("manufacturing_date").split("/")[-1])
                if data.get("manufacturing_date") else None
            ),

            "vehicle_seat_capacity": data.get("seating_capacity"),
            "blacklist_status": data.get("blacklist_status"),
            "status": data.get("rc_status"),

            "vehicle_insurance_details": {
                "insurance_upto": normalize_date(data.get("insurance_expiry"))
            },

            "tax_upto": normalize_date(data.get("tax_upto")),
            "fit_upto": normalize_date(data.get("fit_up_to")),
        }
    }

    # Save to cache
    with open(cpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=4)

    return out
