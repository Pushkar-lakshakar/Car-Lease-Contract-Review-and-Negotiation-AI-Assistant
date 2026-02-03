import re
from typing import Dict, List, Tuple
from Backend.utils import extract_currency_amount, parse_duration, parse_mileage
from Backend.config import RISK_THRESHOLD_HIGH, RISK_THRESHOLD_LOW
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_contract_fairness(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """
    Calculate comprehensive contract fairness score (0-100)
    Ensures score and red flags remain consistent
    """
    score = 100
    red_flags = []
    mismatches = []

    logger.info("Starting contract analysis...")

    # 1. Check for missing critical fields (weighted)
    critical_fields = {
        "Lessor Name": 5,
        "Lessee Name": 5,
        "Vehicle Make": 5,
        "Vehicle Model": 5,
        "Vehicle VIN": 10,
        "Monthly Rental": 8,
        "Lease Term Duration": 5,
        "Insurance Requirements": 8
    }

    missing_critical = []
    for field, weight in critical_fields.items():
        if contract_data.get(field, "Not Found") == "Not Found":
            missing_critical.append(field)
            score -= weight

    if missing_critical:
        red_flags.append(
            f"MISSING CRITICAL FIELDS: {', '.join(missing_critical)}"
        )

    # 2. Financial
    financial_analysis = analyze_financial_terms(contract_data, vehicle_data)
    score += financial_analysis["score_adjustment"]
    red_flags.extend(financial_analysis["red_flags"])

    # 3. Mileage
    mileage_analysis = analyze_mileage_terms(contract_data)
    score += mileage_analysis["score_adjustment"]
    red_flags.extend(mileage_analysis["red_flags"])

    # 4. Vehicle mismatch
    mismatch_analysis = analyze_vehicle_mismatch(contract_data, vehicle_data)
    score += mismatch_analysis["score_adjustment"]
    red_flags.extend(mismatch_analysis["red_flags"])
    mismatches.extend(mismatch_analysis["mismatches"])

    # 5. Legal
    legal_analysis = analyze_legal_compliance(contract_data)
    score += legal_analysis["score_adjustment"]
    red_flags.extend(legal_analysis["red_flags"])

    # 6. Clauses
    clause_analysis = analyze_contract_clauses(contract_data)
    score += clause_analysis["score_adjustment"]
    red_flags.extend(clause_analysis["red_flags"])

    # 7. Suspicious patterns
    suspicious_analysis = detect_suspicious_patterns(contract_data)
    red_flags.extend(suspicious_analysis["red_flags"])

    # Ensure suspicious findings also impact score
    if suspicious_analysis["red_flags"]:
        score -= len(suspicious_analysis["red_flags"]) * 5

    # Ensure logical consistency:
    # If score is low but no red flags exist, add system-level flag
    if score < 40 and not red_flags:
        red_flags.append(
            "LOW SCORE WITHOUT EXPLICIT FLAGS - REVIEW SCORING LOGIC"
        )

    # Clamp score
    score = max(0, min(100, score))

    # Fairness level
    if score >= 90:
        level = "EXCELLENT"
    elif score >= 75:
        level = "GOOD"
    elif score >= 60:
        level = "FAIR"
    elif score >= 40:
        level = "POOR"
    else:
        level = "UNFAIR - REVIEW REQUIRED"

    # Risk level
    risk_level = (
        "LOW" if score >= RISK_THRESHOLD_HIGH
        else "MEDIUM" if score >= RISK_THRESHOLD_LOW
        else "HIGH"
    )

    return {
        "contract_fairness_score": round(score, 1),
        "contract_fairness_level": level,
        "risk_level": risk_level,
        "red_flags": red_flags,
        "vehicle_mismatches": mismatches
    }


def analyze_financial_terms(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """Analyze financial terms for fairness - returns only red flags"""
    score_adj = 0
    red_flags = []
    
    monthly_rent_str = contract_data.get("Monthly Rental", "Not Found")
    deposit_str = contract_data.get("Security Deposit", "Not Found")
    advance_str = contract_data.get("Advance Payment", "Not Found")
    termination_str = contract_data.get("Early Termination Fee/Conditions", "Not Found")
    late_fee_str = contract_data.get("Late Payment Fee/Percentage", "Not Found")
    purchase_str = contract_data.get("Purchase Option Price", "Not Found")
    residual_str = contract_data.get("Residual Value", "Not Found")
    
    # 1. Check deposit amount
    if monthly_rent_str != "Not Found" and deposit_str != "Not Found":
        monthly, _ = extract_currency_amount(monthly_rent_str)
        deposit, _ = extract_currency_amount(deposit_str)
        
        if monthly and deposit and monthly > 0:
            deposit_months = deposit / monthly
            
            if deposit_months > 3:
                score_adj -= 20
                red_flags.append(f"EXCESSIVE SECURITY DEPOSIT: {deposit_months:.1f} months rent (industry standard: 1-3 months)")
    
    # 2. Check early termination fee
    if termination_str != "Not Found":
        term_fee, _ = extract_currency_amount(termination_str)
        if term_fee:
            if monthly_rent_str != "Not Found":
                monthly, _ = extract_currency_amount(monthly_rent_str)
                if monthly and monthly > 0:
                    term_months = term_fee / monthly
                    if term_months > 6:
                        score_adj -= 15
                        red_flags.append(f"EXCESSIVE EARLY TERMINATION FEE: {term_months:.1f} months rent (should be ≤ 6 months)")
    
    # 3. Check late payment fees
    if late_fee_str != "Not Found":
        if "%" in late_fee_str:
            # Percentage-based late fee
            match = re.search(r'(\d+)%', late_fee_str)
            if match:
                percentage = int(match.group(1))
                if percentage > 10:
                    score_adj -= 10
                    red_flags.append(f"HIGH LATE FEE PERCENTAGE: {percentage}% (typical: 5-10%)")
        else:
            # Fixed amount late fee
            late_fee, _ = extract_currency_amount(late_fee_str)
            if late_fee and monthly_rent_str != "Not Found":
                monthly, _ = extract_currency_amount(monthly_rent_str)
                if monthly and monthly > 0:
                    if late_fee > monthly * 0.1:  # More than 10% of monthly rent
                        score_adj -= 10
                        red_flags.append(f"HIGH LATE FEE AMOUNT: ₹{late_fee:,.0f} (should be ≤ 10% of monthly rent)")
    
    # 4. Check advance payment
    if advance_str != "Not Found":
        advance, _ = extract_currency_amount(advance_str)
        if advance and monthly_rent_str != "Not Found":
            monthly, _ = extract_currency_amount(monthly_rent_str)
            if monthly and monthly > 0:
                advance_months = advance / monthly
                if advance_months > 3:
                    score_adj -= 10
                    red_flags.append(f"HIGH ADVANCE PAYMENT: {advance_months:.1f} months rent")
    
    # 5. Check purchase option price vs residual value
    if purchase_str != "Not Found" and residual_str != "Not Found":
        purchase_price, _ = extract_currency_amount(purchase_str)
        residual, _ = extract_currency_amount(residual_str)
        if purchase_price and residual and residual > 0:
            difference = ((purchase_price - residual) / residual) * 100
            if difference > 30:  # More than 30% above residual value
                score_adj -= 15
                red_flags.append(f"EXCESSIVE PURCHASE OPTION PRICE: {difference:+.1f}% above residual value")
    
    # 6. Check if monthly rent is reasonable compared to vehicle value
    if monthly_rent_str != "Not Found" and vehicle_data.get("status") == "success":
        monthly_rent, _ = extract_currency_amount(monthly_rent_str)
        if monthly_rent:
            msrp = vehicle_data.get("result", {}).get("market_info", {}).get("msrp")
            if msrp:
                monthly_as_percentage = (monthly_rent * 12 * 3) / msrp * 100  # 3-year total
                if monthly_as_percentage > 80:  # More than 80% of vehicle value
                    score_adj -= 15
                    red_flags.append(f"HIGH LEASE PAYMENTS: 3-year total is {monthly_as_percentage:.1f}% of vehicle MSRP")
    
    return {
        "score_adjustment": score_adj,
        "red_flags": red_flags
    }

def analyze_mileage_terms(contract_data: Dict) -> Dict:
    """Analyze mileage terms - returns only red flags"""
    score_adj = 0
    red_flags = []
    
    mileage_str = contract_data.get("Annual Mileage Limit", "Not Found")
    excess_str = contract_data.get("Excess Mileage Charge", "Not Found")
    
    if mileage_str != "Not Found":
        mileage, _ = parse_mileage(mileage_str)
        if mileage:
            if mileage < 12000:
                score_adj -= 15
                red_flags.append(f"VERY LOW MILEAGE LIMIT: {mileage:,.0f} km/year (minimum 15,000 recommended)")
    
    if excess_str != "Not Found":
        excess, _ = extract_currency_amount(excess_str)
        if excess:
            if excess > 50:  # ₹50 per km
                score_adj -= 12
                red_flags.append(f"HIGH EXCESS MILEAGE CHARGE: ₹{excess:.0f}/km (industry average: ₹15-30/km)")
    
    return {
        "score_adjustment": score_adj,
        "red_flags": red_flags
    }

def analyze_vehicle_mismatch(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """Analyze vehicle data mismatches - returns only red flags and mismatches"""
    score_adj = 0
    mismatches = []
    red_flags = []
    
    if vehicle_data.get("status") == "success":
        # Extract contract values
        contract_make = contract_data.get("Vehicle Make", "").lower().strip()
        contract_model = contract_data.get("Vehicle Model", "").lower().strip()
        contract_year = contract_data.get("Vehicle Year", "").strip()
        contract_vin = contract_data.get("Vehicle VIN", "").upper().strip()
        
        # Extract API values - safely handle None values
        api_data = vehicle_data.get("result", {}).get("basic_info", {}) or {}
        
        # Safely get all API values with defaults
        api_make = (api_data.get("make") or "").lower().strip()
        api_model = (api_data.get("model") or "").lower().strip()
        api_year = str(api_data.get("year") or "").strip()
        api_vin = vehicle_data.get("vin", "").upper().strip()
        
        # Log what we found for debugging
        logger.info(f"Contract: {contract_make} {contract_model} {contract_year}")
        logger.info(f"API: {api_make} {api_model} {api_year}")
        
        # VIN mismatch check (most critical)
        if contract_vin and api_vin and contract_vin != api_vin:
            score_adj -= 30
            red_flags.append(f"CRITICAL VIN MISMATCH: Contract VIN {contract_vin} vs API VIN {api_vin}")
        
        # Make mismatch
        if contract_make and api_make:
            # Allow partial matches (e.g., "Toyota" vs "Toyota Motor Corporation")
            if contract_make and api_make and contract_make not in api_make and api_make not in contract_make:
                score_adj -= 25
                mismatch_msg = f"Vehicle make mismatch: Contract '{contract_data.get('Vehicle Make')}' vs API '{api_data.get('make')}'"
                mismatches.append(mismatch_msg)
                red_flags.append(f"SERIOUS: {mismatch_msg} - Verify VIN authenticity")
        
        # Model mismatch
        if contract_model and api_model:
            # More lenient model matching
            contract_words = set(contract_model.split())
            api_words = set(api_model.split())
            common = contract_words.intersection(api_words)
            if len(common) < 1:  # No common words
                score_adj -= 20
                mismatch_msg = f"Vehicle model mismatch: Contract '{contract_data.get('Vehicle Model')}' vs API '{api_data.get('model')}'"
                mismatches.append(mismatch_msg)
                red_flags.append(f"SERIOUS: {mismatch_msg} - Possible fraud or error")
        
        # Year mismatch
        if contract_year and api_year and contract_year != api_year:
            try:
                contract_year_int = int(contract_year)
                api_year_int = int(api_year)
                year_diff = abs(contract_year_int - api_year_int)
                
                if year_diff > 2:  # More than 2 years difference is serious
                    score_adj -= 25
                    red_flags.append(f"CRITICAL VEHICLE YEAR MISMATCH: {year_diff} years difference! Contract {contract_year} vs API {api_year}")
                else:
                    score_adj -= 10
                    mismatches.append(f"Vehicle year mismatch: Contract {contract_year} vs API {api_year}")
            except:
                score_adj -= 10
                mismatches.append(f"Vehicle year mismatch: Contract {contract_year} vs API {api_year}")
        
        # Check if vehicle is too old for leasing
        if api_year:
            try:
                vehicle_year = int(api_year)
                current_year = datetime.now().year
                age = current_year - vehicle_year
                
                if age > 5:
                    score_adj -= 15
                    red_flags.append(f"VEHICLE TOO OLD FOR LEASING: {age} years old (manufactured {api_year})")
            except:
                pass
    
    # If we have serious mismatches, add a comprehensive red flag
    if mismatches:
        red_flags.append(f"MULTIPLE VEHICLE MISMATCHES DETECTED: Verify VIN {contract_data.get('Vehicle VIN', '')} authenticity")
    
    return {
        "score_adjustment": score_adj,
        "red_flags": red_flags,
        "mismatches": mismatches
    }

def analyze_legal_compliance(contract_data: Dict) -> Dict:
    """Analyze legal compliance issues - returns only red flags"""
    score_adj = 0
    red_flags = []
    
    # 1. Insurance requirements (legally required)
    insurance = contract_data.get("Insurance Requirements", "Not Found")
    if insurance == "Not Found":
        score_adj -= 15
        red_flags.append("INSURANCE REQUIREMENTS NOT SPECIFIED (legally required for leased vehicles)")
    
    # 2. Check for unreasonable default conditions
    default = contract_data.get("Default Conditions", "Not Found")
    if default != "Not Found":
        if any(term in default.lower() for term in ["immediate", "24 hours", "without notice"]):
            score_adj -= 10
            red_flags.append("UNREASONABLE DEFAULT CONDITIONS - immediate termination without notice")
    
    # 3. Check arbitration clause (can limit legal rights)
    arbitration = contract_data.get("Arbitration Clause", "Not Found")
    if arbitration != "Not Found" and "present" in arbitration.lower():
        red_flags.append("ARBITRATION CLAUSE PRESENT - may limit right to sue in court")
    
    return {
        "score_adjustment": score_adj,
        "red_flags": red_flags
    }

def analyze_contract_clauses(contract_data: Dict) -> Dict:
    """Analyze specific contract clauses for fairness - returns only red flags"""
    score_adj = 0
    red_flags = []
    
    # 1. Wear and tear allowance
    wear_tear = contract_data.get("Wear and Tear Allowance", "Not Found")
    if wear_tear == "Not Found":
        score_adj -= 8
        red_flags.append("WEAR AND TEAR ALLOWANCE NOT SPECIFIED - may lead to disputes at return")
    
    # 2. Disposition fee check
    disposition = contract_data.get("Disposition Fee", "Not Found")
    if disposition != "Not Found":
        fee, _ = extract_currency_amount(disposition)
        if fee and fee > 5000:  # ₹5000
            score_adj -= 8
            red_flags.append(f"HIGH DISPOSITION FEE: ₹{fee:,.0f} (typical: ₹2,000-5,000)")
    
    # 3. Maintenance responsibility
    maintenance = contract_data.get("Maintenance Responsibility", "Not Found")
    if maintenance == "Not Found":
        score_adj -= 8
        red_flags.append("MAINTENANCE RESPONSIBILITY NOT SPECIFIED")
    
    # 4. Subleasing restrictions
    subleasing = contract_data.get("Subleasing Allowed", "Not Found")
    if subleasing != "Not Found" and "no" in subleasing.lower():
        red_flags.append("SUBLEASING NOT ALLOWED - severely limits flexibility")
    
    # 5. Geographic restrictions
    geo_restrict = contract_data.get("Geographic Restrictions", "Not Found")
    if geo_restrict != "Not Found":
        red_flags.append(f"GEOGRAPHIC RESTRICTIONS: {geo_restrict}")
    
    return {
        "score_adjustment": score_adj,
        "red_flags": red_flags
    }

def detect_suspicious_patterns(contract_data: Dict) -> Dict:
    """Detect suspicious patterns in contract - returns only red flags"""
    red_flags = []
    
    # 1. Check for vague terms
    vague_terms = ["as determined by lessor", "at lessor's discretion", "sole discretion"]
    for field, value in contract_data.items():
        if value != "Not Found":
            if any(term in value.lower() for term in vague_terms):
                red_flags.append(f"VAGUE TERM IN '{field}': '{value}'")
    
    # 2. Check for blank spaces to be filled later
    if any("_____" in str(v) or "________" in str(v) for v in contract_data.values()):
        red_flags.append("CONTRACT HAS BLANK SPACES TO BE FILLED - ensure completion before signing")
    
    # 3. Check for unreasonable acceleration clauses
    for field, value in contract_data.items():
        if "acceleration" in field.lower() and value != "Not Found":
            if "all payments" in value.lower() or "entire balance" in value.lower():
                red_flags.append("ACCELERATION CLAUSE DEMANDS FULL PAYMENT IMMEDIATELY")
    
    # 4. Check for one-sided modification rights
    modification_terms = ["lessor may modify", "terms may change", "subject to change"]
    for field, value in contract_data.items():
        if value != "Not Found":
            if any(term in value.lower() for term in modification_terms):
                red_flags.append(f"ONE-SIDED MODIFICATION CLAUSE IN '{field}'")
    
    # 5. Check for hidden fees
    hidden_fee_terms = ["additional charges may apply", "fees subject to change", "administrative fees"]
    for field, value in contract_data.items():
        if value != "Not Found":
            if any(term in value.lower() for term in hidden_fee_terms):
                red_flags.append(f"HIDDEN FEES POSSIBLE IN '{field}': '{value}'")
    
    return {
        "red_flags": red_flags
    }

def quick_risk_assessment(contract_data: Dict, vehicle_data: Dict) -> Dict:
    """Simple wrapper for API"""
    return calculate_contract_fairness(contract_data, vehicle_data)
