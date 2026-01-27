import os
import json
import re
from typing import Dict
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env file")
    GEMINI_AVAILABLE = False
else:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        GEMINI_AVAILABLE = True
        print("✓ Gemini API configured")
    except ImportError:
        print("ERROR: google-genai library not installed. Run: pip install google-genai")
        GEMINI_AVAILABLE = False
    except Exception as e:
        print(f"ERROR: Gemini initialization failed: {e}")
        GEMINI_AVAILABLE = False

def extract_with_gemini(ocr_text: str) -> Dict[str, str]:
    """Extract fields using Gemini 2.5 Flash"""
    if not GEMINI_AVAILABLE:
        return {}
    
    print("Using Gemini 2.5 Flash for extraction...")
    
    # Take a reasonable chunk
    clean_text = ocr_text[:10000]
    
    # Simple, clear prompt
    prompt = f"""EXTRACT ALL FIELDS from this car lease agreement:

    Look for these specific fields:
    
    1. Lessor Name (who owns the car)
    2. Lessee Name (who is renting)
    3. Vehicle Make (e.g., Toyota, Honda, etc.)
    4. Vehicle Model (e.g., Corolla Altis)
    5. Vehicle Year (e.g., 2024)
    6. Vehicle VIN (17-character number like 1GTG6CEN0L1139305)
    7. License Plate (e.g., MP-07-CK-8399)
    8. Monthly Rental (amount like ₹41,500)
    9. Security Deposit (amount like ₹76,500)
    10. Lease Term (e.g., 36 months)
    11. Annual Mileage Limit (e.g., 24,000 km)
    12. Excess Mileage Charge (e.g., ₹25 per km)
    13. Early Termination Fee (amount like ₹1,00,000)
    14. Purchase Option Price (amount like ₹16,00,000)
    15. Insurance Requirements (what insurance is required)
    
    For each field, return the exact value from the document.
    If a field is not found, return "Not Found".
    
    Return ONLY JSON format with these exact field names.
    
    Document Text:
    {clean_text}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",  # Use this or gemini-2.0-flash
            contents=[prompt],
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 1000,
            }
        )
        
        text = response.text
        print(f"Gemini raw response: {text[:500]}...")
        
        # Clean and extract JSON
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Find JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)
            
            # Ensure all fields exist
            all_fields = [
                "Lessor Name", "Lessee Name", "Vehicle Make", "Vehicle Model",
                "Vehicle Year", "Vehicle VIN", "License Plate", "Monthly Rental",
                "Security Deposit", "Lease Term", "Annual Mileage Limit",
                "Excess Mileage Charge", "Early Termination Fee", "Purchase Option Price",
                "Insurance Requirements"
            ]
            
            result = {}
            for field in all_fields:
                value = data.get(field, "Not Found")
                if value and value != "Not Found":
                    # Clean up
                    value = str(value).strip()
                    # Add ₹ for amounts
                    if any(term in field.lower() for term in ['rental', 'deposit', 'fee', 'price', 'charge']):
                        if '₹' not in value and any(c.isdigit() for c in value):
                            value = f"₹{value}"
                result[field] = value
            
            print(f"Gemini extracted {sum(1 for v in result.values() if v != 'Not Found')} fields")
            return result
            
    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        return {}

def extract_from_ocr_directly(ocr_text: str) -> Dict[str, str]:
    """
    Fallback: Extract fields directly from OCR text
    This is your original document's structure
    """
    print("Using direct OCR extraction (Gemini fallback)")
    
    result = {
        "Lessor Name": "Not Found",
        "Lessee Name": "Not Found",
        "Vehicle Make": "Not Found",
        "Vehicle Model": "Not Found",
        "Vehicle Year": "Not Found",
        "Vehicle VIN": "Not Found",
        "License Plate": "Not Found",
        "Monthly Rental": "Not Found",
        "Security Deposit": "Not Found",
        "Lease Term": "Not Found",
        "Annual Mileage Limit": "Not Found",
        "Excess Mileage Charge": "Not Found",
        "Early Termination Fee": "Not Found",
        "Purchase Option Price": "Not Found",
        "Insurance Requirements": "Not Found"
    }
    
    text = ocr_text.upper()
    
    # Extract from your specific document structure
    # 1. Extract VIN
    vin_match = re.search(r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})', text)
    if vin_match:
        result["Vehicle VIN"] = vin_match.group(1)
    
    # 2. Extract License Plate
    plate_match = re.search(r'LICENSE[-\s]*PLATE[-\s]*([A-Z0-9-]+)', text)
    if plate_match:
        result["License Plate"] = plate_match.group(1)
    
    # 3. Extract Monthly Rental
    rent_match = re.search(r'MONTHLY[-\s]*LEASE[-\s]*AMOUNT[:\s]*₹?\s*([\d,]+)', text)
    if rent_match:
        result["Monthly Rental"] = f"₹{rent_match.group(1)}"
    
    # 4. Extract Security Deposit
    deposit_match = re.search(r'DEPOSIT[-\s]*AMOUNT[:\s]*₹?\s*([\d,]+)', text)
    if deposit_match:
        result["Security Deposit"] = f"₹{deposit_match.group(1)}"
    
    # 5. Extract Lease Term
    term_match = re.search(r'LEASE[-\s]*TERM[:\s]*(\d+)\s*MONTHS', text, re.IGNORECASE)
    if term_match:
        result["Lease Term"] = f"{term_match.group(1)} months"
    
    # 6. Extract Mileage Limit
    mileage_match = re.search(r'ANNUAL[-\s]*MILEAGE[-\s]*LIMIT[:\s]*([\d,]+)\s*KM', text, re.IGNORECASE)
    if mileage_match:
        result["Annual Mileage Limit"] = f"{mileage_match.group(1)} km"
    
    # 7. Extract Vehicle Make/Model
    if 'TOYOTA' in text and 'COROLLA' in text:
        result["Vehicle Make"] = "Toyota"
        result["Vehicle Model"] = "Corolla Altis"
    
    # 8. Extract Names (simplified)
    # Look for patterns like "Lessor: Michael Roberts"
    lessor_match = re.search(r'LESSOR[:\s]*([A-Z][A-Z\s]+?)(?=\n|LESSEE|$)', text)
    if lessor_match:
        result["Lessor Name"] = lessor_match.group(1).title()
    
    lessee_match = re.search(r'LESSEE[:\s]*([A-Z][A-Z\s]+?)(?=\n|VEHICLE|$)', text)
    if lessee_match:
        result["Lessee Name"] = lessee_match.group(1).title()
    
    # 9. Extract Early Termination Fee
    term_fee_match = re.search(r'TERMINATION[-\s]*FEE[-\s]*OF[-\s]*₹?\s*([\d,]+)', text, re.IGNORECASE)
    if term_fee_match:
        result["Early Termination Fee"] = f"₹{term_fee_match.group(1)}"
    
    # 10. Extract Purchase Price
    purchase_match = re.search(r'PURCHASE[-\s]*PRICE[-\s]*₹?\s*([\d,]+)', text, re.IGNORECASE)
    if purchase_match:
        result["Purchase Option Price"] = f"₹{purchase_match.group(1)}"
    
    print(f"Direct extraction found {sum(1 for v in result.values() if v != 'Not Found')} fields")
    return result

def extract_sla_from_text(ocr_text: str) -> Dict[str, str]:
    """
    Main extraction function - tries Gemini first, then fallback
    """
    print("Extracting contract fields...")
    
    # Try Gemini first if available
    if GEMINI_AVAILABLE:
        gemini_result = extract_with_gemini(ocr_text)
        if gemini_result and any(v != "Not Found" for v in gemini_result.values()):
            return gemini_result
        else:
            print("Gemini extraction failed or returned empty, using fallback")
    
    # Use direct OCR extraction as fallback
    return extract_from_ocr_directly(ocr_text)
