import datetime

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def safe_lower(v):
    return v.lower() if isinstance(v, str) else ""

def safe_int(v):
    try:
        return int(str(v).strip())
    except:
        return None

def safe_date(v):
    try:
        return datetime.datetime.fromisoformat(v).date()
    except:
        return None


# -------------------------------------------------------
# Main Risk Analysis
# -------------------------------------------------------

def analyze_risk(sla: dict, vehicle: dict):
    risk_flags = []
    score = 0

    sla = sla or {}
    vehicle = vehicle or {}

    v = vehicle.get("result", {})

    # ---------------------------------------------------
    # 1. SLA Checks
    # ---------------------------------------------------

    rent = safe_int(sla.get("Monthly Rental"))
    if rent and rent > 100000:
        risk_flags.append("Very high monthly rental")
        score += 2

    tenure = safe_int(sla.get("Tenure"))
    if tenure and (tenure < 6 or tenure > 60):
        risk_flags.append("Unusual lease tenure")
        score += 1

    if safe_lower(sla.get("Mileage Cap")) in ["not available", ""]:
        risk_flags.append("Mileage cap missing")
        score += 1

    pen = safe_int(sla.get("Termination Penalty"))
    if pen and pen > 100000:
        risk_flags.append("Very high termination penalty")
        score += 1

    pp = safe_int(sla.get("Purchase Price"))
    if pp and pp < 20000:
        risk_flags.append("Unusually low purchase price (possible typo)")
        score += 1

    if safe_lower(sla.get("Maintenance")) not in ["included", "covered"]:
        risk_flags.append("Maintenance unclear or not included")
        score += 1

    if safe_lower(sla.get("Taxes")) not in ["included", "covered"]:
        risk_flags.append("Taxes unclear or not included")
        score += 1


    # ---------------------------------------------------
    # 2. Vehicle API Checks
    # ---------------------------------------------------

    if safe_lower(v.get("status")) != "active":
        risk_flags.append("Vehicle RC not active")
        score += 2

    if safe_lower(v.get("blacklist_status")) not in ["na", "none", ""]:
        risk_flags.append("Vehicle appears in blacklist")
        score += 3

    ins = safe_date(v.get("vehicle_insurance_details", {}).get("insurance_upto"))
    if not ins:
        risk_flags.append("Insurance expiry unknown")
        score += 1
    else:
        if ins < datetime.date.today():
            risk_flags.append("Insurance expired")
            score += 3

    fit = safe_date(v.get("fit_upto"))
    if fit and fit < datetime.date.today():
        risk_flags.append("Vehicle fitness expired")
        score += 3

    if not safe_date(v.get("reg_date")):
        risk_flags.append("Registration date invalid/missing")
        score += 1


    # ---------------------------------------------------
    # 3. Final Categorization
    # ---------------------------------------------------

    if score <= 2:
        risk_level = "Low Risk"
    elif score <= 6:
        risk_level = "Moderate Risk"
    else:
        risk_level = "High Risk"

    return {
        "risk_level": risk_level,
        "risk_score": score,
        "flags": risk_flags,
        "vehicle_number": v.get("reg_no"),
        "owner_name": v.get("owner_name"),
        "model": v.get("model")
    }
