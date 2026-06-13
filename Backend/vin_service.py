import requests
import time
import json
import re
import logging
from datetime import datetime, timedelta
from Backend.database import SessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CACHE_EXPIRY_DAYS = 7

# --- VIN Extractor ---
VIN_REGEX = r"\b[A-HJ-NPR-Z0-9]{17}\b"

def extract_vin(text: str):
    match = re.search(VIN_REGEX, text)
    return match.group(0) if match else ""


# ===== CHANGE THIS TO True TO FORCE FRESH API CALLS (ignores cache) =====
FORCE_VIN_REFRESH = True
# =========================================================================

def get_vehicle_details(vin: str) -> dict:
    """
    Get vehicle details using NHTSA's free VIN decoder API.
    Returns data in the same shape as the old vehicle_lookup.py for compatibility.
    """
    if not vin or vin == "Not Found" or len(vin) < 17:
        return {"status": "invalid_vin", "vin": vin or "Not Found", "error": "Invalid or missing VIN"}
    
    # Clean and validate VIN
    vin = vin.upper().strip()
    # First convert ambiguous letters to numbers (O->0, I->1, Q->0)
    vin = vin.replace('O', '0').replace('I', '1').replace('Q', '0')
    # Then remove any remaining invalid characters (spaces, dashes, etc.)
    vin = re.sub(r'[^A-HJ-NPR-Z0-9]', '', vin)
    
    if len(vin) != 17:
        logger.warning(f"Invalid VIN length: {vin} (length: {len(vin)})")
        return {"status": "invalid_vin", "vin": vin, "error": f"Invalid VIN length: {len(vin)}"}
    
    # 1. Check database cache first (unless force refresh is on)
    if not FORCE_VIN_REFRESH:
        db = SessionLocal()
        try:
            row = db.execute(
                text("SELECT api_response, cached_at FROM vehicle_api_cache WHERE vin = :vin"),
                {"vin": vin}
            ).fetchone()
            if row:
                cached_data = row[0]
                cached_at = row[1]
                if isinstance(cached_data, str):
                    cached_data = json.loads(cached_data)
                if datetime.now() - cached_at < timedelta(days=CACHE_EXPIRY_DAYS):
                    logger.info(f"Using database cached data for VIN: {vin}")
                    cached_data["cache_hit"] = True
                    cached_data["api_latency_ms"] = 0
                    return cached_data
                else:
                    logger.info("Database cache expired, refreshing...")
        except Exception as e:
            logger.warning(f"Database cache read failed for {vin}: {e}")
        finally:
            db.close()
    
    # 2. Call NHTSA free API
    logger.info(f"Calling NHTSA API for VIN: {vin}")
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    
    try:
        api_start = time.time()
        response = requests.get(url, timeout=15)
        api_latency_ms = round((time.time() - api_start) * 1000, 2)
        
        if response.status_code != 200:
            logger.error(f"NHTSA API error {response.status_code}")
            return {
                "status": "api_error",
                "vin": vin,
                "error": f"NHTSA API returned status {response.status_code}",
                "cache_hit": False,
                "api_latency_ms": api_latency_ms
            }
        
        data = response.json()
        raw = {}
        for item in data.get("Results", []):
            if item.get("Value") and item["Value"].strip():
                raw[item["Variable"]] = item["Value"].strip()
        
        logger.info(f"NHTSA API returned {len(raw)} fields in {api_latency_ms}ms")
        
        # Map NHTSA fields to our expected structure
        make = raw.get("Make", "")
        model = raw.get("Model", "")
        year = raw.get("Model Year", "")
        
        # Engine info
        displacement_l = raw.get("Displacement (L)", "")
        cylinders = raw.get("Engine Number of Cylinders", "")
        horsepower = raw.get("Engine Brake (hp) From", "")
        fuel_type = raw.get("Fuel Type - Primary", "")
        
        result = {
            "status": "success",
            "vin": vin,
            "timestamp": datetime.now().isoformat(),
            "api_latency_ms": api_latency_ms,
            "result": {
                "basic_info": {
                    "year": year,
                    "make": make,
                    "model": model,
                    "trim": raw.get("Trim", ""),
                    "body_style": raw.get("Body Class", ""),
                    "vehicle_type": raw.get("Vehicle Type", ""),
                    "doors": raw.get("Doors", ""),
                    "seats": raw.get("Number of Seats", ""),
                    "fuel_type": fuel_type,
                    "driven_wheels": raw.get("Drive Type", ""),
                    "manufactured_in": raw.get("Plant Country", ""),
                    "exterior_color": "",
                    "interior_color": ""
                },
                "engine_details": {
                    "engine_type": raw.get("Engine Configuration", ""),
                    "engine_size_liters": displacement_l,
                    "cylinder_count": cylinders,
                    "horsepower_hp": horsepower,
                    "torque_lb_ft": "",
                    "horsepower_rpm": "",
                    "torque_rpm": "",
                    "valves": raw.get("Engine Number of Valves", ""),
                    "valve_timing": raw.get("Valve Train Design", ""),
                    "cam_type": "",
                    "fuel_injection": "",
                    "compression_ratio": ""
                },
                "transmission_details": {
                    "transmission_type": raw.get("Transmission Style", ""),
                    "transmission_speeds": raw.get("Transmission Speeds", ""),
                    "transmission_desc": ""
                },
                "performance": {
                    "top_speed_mph": "",
                    "acceleration_0_60": "",
                    "city_mpg": "",
                    "highway_mpg": "",
                    "combined_mpg": "",
                    "range_miles": ""
                },
                "dimensions": {
                    "length_in": "",
                    "width_in": "",
                    "height_in": "",
                    "wheelbase_in": raw.get("Wheelbase (inches)", ""),
                    "ground_clearance_in": "",
                    "curb_weight_lbs": raw.get("Gross Vehicle Weight Rating From", ""),
                    "gross_weight_lbs": "",
                    "cargo_capacity_cuft": ""
                },
                "features": {
                    "standard_features": [],
                    "optional_features": []
                },
                "market_info": {},
                "safety": {
                    "safety_rating": "",
                    "nhtsa_rating": "",
                    "iihs_rating": "",
                    "airbags_count": raw.get("Air Bag Loc Front", "")
                },
                "warranty": {},
                "raw_api_data": raw
            },
            "_cache": {
                "saved_at": datetime.now().isoformat(),
                "api_called": True,
                "source": "vpic.nhtsa.dot.gov",
                "api_latency_ms": api_latency_ms
            },
            "cache_hit": False
        }
        
        # 3. Save to database cache
        db = SessionLocal()
        try:
            db.execute(text("""
                INSERT INTO vehicle_api_cache (vin, api_response)
                VALUES (:vin, :response)
                ON CONFLICT (vin) DO UPDATE
                SET api_response = EXCLUDED.api_response,
                    cached_at = CURRENT_TIMESTAMP
            """), {
                "vin": vin,
                "response": json.dumps(result)
            })
            db.commit()
            logger.info(f"NHTSA response cached for VIN: {vin}")
        except Exception as e:
            logger.error(f"Failed to cache NHTSA response: {e}")
            db.rollback()
        finally:
            db.close()
        
        return result
        
    except requests.Timeout:
        logger.error(f"NHTSA API timeout for VIN: {vin}")
        return {"status": "timeout", "vin": vin, "error": "API request timed out", "cache_hit": False, "api_latency_ms": 0}
    except Exception as e:
        logger.error(f"NHTSA API exception for {vin}: {e}")
        return {"status": "api_error", "vin": vin, "error": str(e), "cache_hit": False, "api_latency_ms": 0}
