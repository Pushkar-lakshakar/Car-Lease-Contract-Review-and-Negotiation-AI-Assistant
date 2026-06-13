import logging
import json
import re
from typing import Dict, Optional
from google import genai
from Backend.config import GEMINI_API_KEY
from Backend.utils import extract_currency_amount

logger = logging.getLogger(__name__)

# Initialize GenAI client
client = genai.Client(api_key=GEMINI_API_KEY)

def estimate_market_price(vehicle_data: Dict, financial_data: Dict) -> Dict:
    """
    Produce an approximate market price range for a vehicle.
    Hybrid approach: Basic heuristics + Gemini AI reasoning.
    """
    
    # 1. Gather signals
    vin_info = vehicle_data.get("result", {}).get("basic_info", {})
    year = vin_info.get("year", "N/A")
    make = vin_info.get("make", "N/A")
    model = vin_info.get("model", "N/A")
    trim = vin_info.get("trim", "")
    hp = vehicle_data.get("result", {}).get("engine_details", {}).get("horsepower_hp", "")
    
    monthly_payment_str = financial_data.get("monthly_rental", "N/A")
    lease_term = financial_data.get("lease_term", "N/A")
    
    # Check if we have enough data to even try
    if make == "N/A" or model == "N/A":
        return {
            "status": "insufficient_data",
            "message": "Market price estimation requires at least vehicle make and model."
        }
    
    # 2. Heuristic baseline (fallback/check)
    # We don't have a database of prices, so we rely on AI to be the primary engine
    # but we provide it with context to keep it realistic.
    
    prompt = f"""Estimate the current market price range (MSRP/Fair Market Value) for this vehicle in India (INR).
    
    VEHICLE DETAILS:
    - Year: {year}
    - Make: {make}
    - Model: {model}
    - Trim: {trim}
    - Horsepower: {hp}
    
    LEASE CONTEXT:
    - Monthly payment in contract: {monthly_payment_str}
    - Lease term: {lease_term}
    
    Return a structured JSON object with the following fields:
    - min_price: number (INR)
    - max_price: number (INR)
    - midpoint: number (INR)
    - confidence: "HIGH" | "MEDIUM" | "LOW"
    - reasoning: short summary of how this was calculated
    
    GUIDELINES:
    - Be realistic and slightly conservative.
    - If it's a luxury brand (GMC, Mercedes, GMC Canyon, etc.), prices in India can be high due to imports.
    - If you are unsure, set confidence to LOW.
    - Return ONLY the JSON object.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            }
        )
        
        result = json.loads(response.text)
        
        # 3. Add metadata
        result["is_ai_estimation"] = True
        result["status"] = "success"
        result["currency"] = "INR"
        
        # Sanity check: Ensure min < max
        if result.get("min_price", 0) > result.get("max_price", 0):
            result["min_price"], result["max_price"] = result["max_price"], result["min_price"]
            
        logger.info(f"Price estimation success for {year} {make} {model}: ₹{result['midpoint']}")
        return result
        
    except Exception as e:
        logger.error(f"Price estimation failed: {e}")
        return {
            "status": "error",
            "message": f"Estimation failed: {str(e)}",
            "confidence": "LOW"
        }

def get_price_analysis_signals(estimated_price: Dict, financial_data: Dict) -> Dict:
    """
    Calculates if the lease terms are fair relative to the estimated market price.
    """
    if estimated_price.get("status") != "success":
        return {}
    
    midpoint = estimated_price.get("midpoint", 0)
    monthly_str = financial_data.get("monthly_rental", "0")
    monthly, _ = extract_currency_amount(str(monthly_str))
    
    term_str = financial_data.get("lease_term", "36")
    try:
        term = int(re.sub(r"[^\d]", "", str(term_str)))
    except:
        term = 36
        
    if midpoint > 0 and monthly and monthly > 0:
        total_lease_cost = monthly * term
        cost_to_value_ratio = (total_lease_cost / midpoint) * 100
        
        return {
            "total_lease_cost": total_lease_cost,
            "cost_to_value_ratio": round(cost_to_value_ratio, 1),
            "is_potentially_overpriced": cost_to_value_ratio > 85, # Industry rule of thumb
            "is_extremely_overpriced": cost_to_value_ratio > 110
        }
    
    return {}
