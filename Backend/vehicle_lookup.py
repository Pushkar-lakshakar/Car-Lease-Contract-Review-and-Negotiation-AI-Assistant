import os
import json
import re
import requests
import time  # Add for latency measurement
from datetime import datetime, timedelta
from Backend.config import RAPIDAPI_KEY, VEHICLE_API_BASE_URL, VEHICLE_API_HOST, FORCE_API_REFRESH, CACHE_EXPIRY_DAYS
from Backend.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_vehicle_details(vin: str) -> dict:
    """
    Get comprehensive vehicle details - Uses cache first, calls API only once per VIN
    Enhanced with more vehicle data fields and latency measurement
    """
    if not vin or vin == "Not Found" or len(vin) < 17:
        return {"status": "invalid_vin", "vin": vin or "Not Found", "error": "Invalid or missing VIN"}
    
    # Clean and validate VIN
    vin = vin.upper().strip()
    vin = re.sub(r'[^A-HJ-NPR-Z0-9]', '', vin)  # Remove invalid characters
    
    # Common corrections
    vin = vin.replace('O', '0').replace('I', '1').replace('Q', '0')
    
    if len(vin) != 17:
        logger.warning(f"Invalid VIN length: {vin} (length: {len(vin)})")
        return {"status": "invalid_vin", "vin": vin, "error": f"Invalid VIN length: {len(vin)} (should be 17)"}
    
    # 1. Check database cache first (unless forced refresh)
    api_latency_ms = 0
    
    if not FORCE_API_REFRESH:
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT api_response, cached_at FROM vehicle_api_cache WHERE vin = :vin"), {"vin": vin}).fetchone()
            if result:
                cached_data, cached_at = result
                # Check if cache is expired
                if datetime.now() - cached_at < timedelta(days=CACHE_EXPIRY_DAYS):
                    logger.info(f"Using database cached data for VIN: {vin}")
                    cached_data["cache_hit"] = True
                    cached_data["api_latency_ms"] = 0
                    return cached_data
                else:
                    logger.info("Database cache expired")
        except Exception as e:
            logger.warning(f"Database cache read failed for {vin}: {e}")
        finally:
            db.close()
    
    # 2. Call API (only if no cache or forced refresh)
    logger.info(f"Calling API for VIN: {vin}")
    
    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": VEHICLE_API_HOST
        }
        
        # Measure API latency
        api_start_time = time.time()
        response = requests.get(f"{VEHICLE_API_BASE_URL}{vin}", headers=headers, timeout=15)
        api_latency_ms = round((time.time() - api_start_time) * 1000, 2)
        
        if response.status_code == 200:
            api_data = response.json()
            logger.info(f"API Response latency: {api_latency_ms}ms")
            
            # Check if API returned valid data
            if not api_data or api_data.get("status") == "error":
                logger.error(f"API returned error for VIN {vin}: {api_data}")
                return {
                    "status": "api_error",
                    "vin": vin,
                    "error": api_data.get("message", "Invalid API response"),
                    "cache_hit": False,
                    "api_latency_ms": api_latency_ms
                }
            
            # Extract data with safe defaults
            specs = api_data.get("specs") or {}
            engine = specs.get("engine") or {}
            transmission = specs.get("transmission") or {}
            dimensions = specs.get("dimensions") or {}
            market = api_data.get("market") or {}
            safety = api_data.get("safety") or {}
            
            # Create comprehensive structured response
            result = {
                "status": "success",
                "vin": vin,
                "timestamp": datetime.now().isoformat(),
                "api_latency_ms": api_latency_ms,  # Add latency measurement
                "result": {
                    "basic_info": {
                        "year": api_data.get("year"),
                        "make": api_data.get("make"),
                        "model": api_data.get("model"),
                        "trim": api_data.get("trim"),
                        "body_style": api_data.get("body_style"),
                        "vehicle_type": api_data.get("vehicle_type"),
                        "doors": api_data.get("doors"),
                        "seats": api_data.get("seats"),
                        "fuel_type": api_data.get("fuel_type"),
                        "driven_wheels": api_data.get("driven_wheels"),
                        "manufactured_in": api_data.get("manufactured_in"),
                        "exterior_color": api_data.get("exterior_color"),
                        "interior_color": api_data.get("interior_color")
                    },
                    "engine_details": {
                        "engine_type": engine.get("type"),
                        "engine_size_liters": engine.get("size"),
                        "cylinder_count": engine.get("cylinders"),
                        "horsepower_hp": engine.get("horsepower"),
                        "torque_lb_ft": engine.get("torque"),
                        "horsepower_rpm": engine.get("horsepower_rpm"),
                        "torque_rpm": engine.get("torque_rpm"),
                        "valves": engine.get("valves"),
                        "valve_timing": engine.get("valve_timing"),
                        "cam_type": engine.get("cam_type"),
                        "fuel_injection": engine.get("fuel_injection"),
                        "compression_ratio": engine.get("compression_ratio")
                    },
                    "transmission_details": {
                        "transmission_type": transmission.get("type"),
                        "transmission_speeds": transmission.get("speeds"),
                        "transmission_desc": transmission.get("description")
                    },
                    "performance": {
                        "top_speed_mph": specs.get("top_speed"),
                        "acceleration_0_60": specs.get("acceleration"),
                        "city_mpg": specs.get("city_mpg"),
                        "highway_mpg": specs.get("highway_mpg"),
                        "combined_mpg": specs.get("combined_mpg"),
                        "range_miles": specs.get("range")
                    },
                    "dimensions": {
                        "length_in": dimensions.get("length"),
                        "width_in": dimensions.get("width"),
                        "height_in": dimensions.get("height"),
                        "wheelbase_in": dimensions.get("wheelbase"),
                        "ground_clearance_in": dimensions.get("ground_clearance"),
                        "curb_weight_lbs": dimensions.get("curb_weight"),
                        "gross_weight_lbs": dimensions.get("gross_weight"),
                        "cargo_capacity_cuft": dimensions.get("cargo_capacity")
                    },
                    "features": {
                        "standard_features": api_data.get("standard_features", []),
                        "optional_features": api_data.get("optional_features", [])
                    },
                    "market_info": {
                        "msrp": market.get("msrp"),
                        "invoice_price": market.get("invoice_price"),
                        "used_price_range": market.get("used_price_range"),
                        "depreciation_rate": market.get("depreciation_rate"),
                        "current_value": market.get("current_value")
                    },
                    "safety": {
                        "safety_rating": safety.get("rating"),
                        "nhtsa_rating": safety.get("nhtsa_rating"),
                        "iihs_rating": safety.get("iihs_rating"),
                        "airbags_count": safety.get("airbags")
                    },
                    "warranty": {
                        "basic_warranty_years": api_data.get("basic_warranty_years"),
                        "basic_warranty_miles": api_data.get("basic_warranty_miles"),
                        "powertrain_warranty_years": api_data.get("powertrain_warranty_years"),
                        "powertrain_warranty_miles": api_data.get("powertrain_warranty_miles")
                    },
                    "raw_api_data": api_data  # Keep raw data for debugging
                },
                "_cache": {
                    "saved_at": datetime.now().isoformat(),
                    "api_called": True,
                    "source": "car-api2.p.rapidapi.com",
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
                logger.info(f"API response saved to database cache for VIN: {vin}")
            except Exception as e:
                logger.error(f"Failed to save to database cache: {e}")
                db.rollback()
            finally:
                db.close()
            
            return result
            
        elif response.status_code == 404:
            logger.warning(f"VIN not found in API: {vin}")
            return {
                "status": "not_found",
                "vin": vin,
                "error": "Vehicle not found in database",
                "cache_hit": False,
                "api_latency_ms": api_latency_ms
            }
        else:
            logger.error(f"API error {response.status_code}: {response.text[:200]}")
            return {
                "status": "api_error",
                "vin": vin,
                "error": f"API returned status {response.status_code}",
                "cache_hit": False,
                "api_latency_ms": api_latency_ms
            }
            
    except requests.Timeout:
        logger.error(f"API timeout for VIN: {vin}")
        return {
            "status": "timeout",
            "vin": vin,
            "error": "API request timed out",
            "cache_hit": False,
            "api_latency_ms": api_latency_ms
        }
    except Exception as e:
        logger.error(f"API exception for {vin}: {e}")
        return {
            "status": "api_error",
            "vin": vin,
            "error": str(e),
            "cache_hit": False,
            "api_latency_ms": api_latency_ms
        }
