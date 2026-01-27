import os
import json
import re
import requests
from datetime import datetime, timedelta
from config import CACHE_DIR, RAPIDAPI_KEY, VEHICLE_API_BASE_URL, VEHICLE_API_HOST, FORCE_API_REFRESH

def get_vehicle_details(vin: str) -> dict:
    """
    Get vehicle details - Uses cache first, calls API only once per VIN
    Saves to: vehicle_cache/<VIN>.json
    """
    if not vin or vin == "Not Found":
        return {"status": "no_vin", "vin": vin}
    
    # Clean VIN
    vin = vin.upper().strip()
    vin = vin.replace('O', '0')  # Fix common error
    
    # 1. Check cache first (unless forced refresh)
    cache_file = os.path.join(CACHE_DIR, f"{vin}.json")
    
    if not FORCE_API_REFRESH and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            
            # Check if cache is expired (7 days)
            cache_time_str = cached_data.get("_cache", {}).get("saved_at", "")
            if cache_time_str:
                cache_time = datetime.fromisoformat(cache_time_str)
                if datetime.now() - cache_time < timedelta(days=7):
                    print(f"Using cached data for VIN: {vin}")
                    cached_data["cache_hit"] = True
                    return cached_data
        except:
            pass  # If cache read fails, call API
    
    # 2. Call API (only if no cache or forced refresh)
    print(f"Calling API for VIN: {vin}")
    
    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": VEHICLE_API_HOST
        }
        
        response = requests.get(f"{VEHICLE_API_BASE_URL}{vin}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            api_data = response.json()
            
            # Create structured response
            result = {
                "status": "success",
                "vin": vin,
                "result": {
                    "basic_info": {
                        "year": api_data.get("year"),
                        "make": api_data.get("make"),
                        "model": api_data.get("model"),
                        "trim": api_data.get("trim")
                    },
                    "specs": api_data.get("specs", {})
                },
                "_cache": {
                    "saved_at": datetime.now().isoformat(),
                    "api_called": True
                },
                "cache_hit": False
            }
            
            # 3. Save to cache file FIRST (before any matching)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            
            print(f"API response saved to cache: {cache_file}")
            return result
            
    except Exception as e:
        print(f"API error: {str(e)}")
    
    # Return error if API fails
    return {
        "status": "api_error",
        "vin": vin,
        "error": "Could not fetch vehicle details"
    }
