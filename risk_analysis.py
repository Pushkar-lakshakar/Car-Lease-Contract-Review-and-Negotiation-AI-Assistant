import re
from typing import Dict
from utils import extract_currency_amount, parse_duration, parse_mileage

def calculate_contract_fairness(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """
    Calculate contract fairness score (0-100)
    """
    score = 100
    red_flags = []
    mismatches = []
    
    # 1. Check for missing critical fields
    critical_fields = ["Lessor Name", "Lessee Name", "Vehicle Make", "Vehicle Model", 
                      "Monthly Rental", "Lease Term", "Vehicle VIN"]
    missing = []
    for field in critical_fields:
        if contract_data.get(field, "Not Found") == "Not Found":
            missing.append(field)
    
    if missing:
        score -= len(missing) * 5
        red_flags.append(f"Missing critical fields: {', '.join(missing)}")
    
    # 2. Check financial terms
    monthly_rent_str = contract_data.get("Monthly Rental", "Not Found")
    deposit_str = contract_data.get("Security Deposit", "Not Found")
    penalty_str = contract_data.get("Early Termination Fee", "Not Found")
    
    if monthly_rent_str != "Not Found" and deposit_str != "Not Found":
        monthly, _ = extract_currency_amount(monthly_rent_str)
        deposit, _ = extract_currency_amount(deposit_str)
        
        if monthly and deposit and monthly > 0:
            deposit_months = deposit / monthly
            if deposit_months > 3:
                score -= 15
                red_flags.append(f"High security deposit: {deposit_months:.1f} months rent (should be 1-3 months)")
    
    # 3. Check mileage
    mileage_str = contract_data.get("Annual Mileage Limit", "Not Found")
    if mileage_str != "Not Found":
        mileage, _ = parse_mileage(mileage_str)
        if mileage and mileage < 12000:
            score -= 10
            red_flags.append(f"Low mileage limit: {mileage} km/year (minimum 15,000 recommended)")
    
    # 4. Check vehicle mismatch
    if vehicle_data.get("status") == "success":
        contract_make = contract_data.get("Vehicle Make", "").lower()
        contract_model = contract_data.get("Vehicle Model", "").lower()
        api_make = vehicle_data.get("result", {}).get("basic_info", {}).get("make", "").lower()
        api_model = vehicle_data.get("result", {}).get("basic_info", {}).get("model", "").lower()
        
        if contract_make and api_make and contract_make not in api_make and api_make not in contract_make:
            score -= 20
            mismatches.append(f"Vehicle make mismatch: Contract says '{contract_data.get('Vehicle Make')}', API says '{api_make.title()}'")
    
    # 5. Check insurance
    insurance = contract_data.get("Insurance Requirements", "Not Found")
    if insurance == "Not Found":
        score -= 10
        red_flags.append("Insurance requirements not specified (legally required)")
    
    # Ensure score is between 0-100
    score = max(0, min(100, score))
    
    # Determine fairness level
    if score >= 90:
        level = "EXCELLENT"
    elif score >= 75:
        level = "GOOD"
    elif score >= 60:
        level = "FAIR"
    elif score >= 40:
        level = "POOR"
    else:
        level = "UNFAIR"
    
    return {
        "contract_fairness_score": score,
        "contract_fairness_level": level,
        "red_flags": red_flags,
        "vehicle_mismatches": mismatches
    }

def quick_risk_assessment(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """Simple wrapper for API"""
    return calculate_contract_fairness(contract_data, vehicle_data)
