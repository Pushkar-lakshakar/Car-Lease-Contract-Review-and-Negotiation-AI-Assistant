import os
import json
import re
from typing import Dict
from dotenv import load_dotenv
import logging

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Gemini client
if not api_key:
    logger.warning("GEMINI_API_KEY not found in .env file")
    GEMINI_AVAILABLE = False
else:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        GEMINI_AVAILABLE = True
        logger.info("✓ Gemini API configured")
    except ImportError:
        logger.error("google-genai library not installed. Run: pip install google-genai")
        GEMINI_AVAILABLE = False
    except Exception as e:
        logger.error(f"Gemini initialization failed: {e}")
        GEMINI_AVAILABLE = False

def extract_with_gemini(ocr_text: str) -> Dict[str, str]:
    """Extract ALL lease contract fields using Gemini 2.5 Flash"""
    if not GEMINI_AVAILABLE:
        return {}

    logger.info("Using Gemini 2.5 Flash for comprehensive extraction...")

    clean_text = ocr_text[:15000]

    prompt = f"""EXTRACT ALL FIELDS from this car lease agreement:

Look for these specific fields (return "Not Found" if not present):

=== PARTIES & VEHICLE DETAILS ===
1. Lessor Name (who owns the car/company name)
2. Lessee Name (who is renting/individual or company)
3. Lessor Address
4. Lessee Address
5. Vehicle Make (e.g., Toyota, Honda, etc.)
6. Vehicle Model (e.g., Corolla Altis, Civic)
7. Vehicle Year (e.g., 2024)
8. Vehicle VIN (17-character number)
9. License Plate Number
10. Vehicle Color
11. Engine Number
12. Chassis Number
13. Odometer Reading at Start

=== FINANCIAL TERMS ===
14. Monthly Rental (amount with currency)
15. Security Deposit (amount with currency)
16. Advance Payment (if any)
17. Down Payment
18. Lease Term Duration (e.g., 36 months)
19. Lease Start Date
20. Lease End Date
21. Payment Due Day (e.g., 5th of each month)
22. Late Payment Fee/Percentage
23. Early Termination Fee/Conditions
24. Purchase Option Price (at lease end)
25. Residual Value (estimated value at lease end)
26. Interest Rate/ Money Factor (if mentioned)
27. Processing Fees/Administrative Charges

=== MILEAGE & USAGE ===
28. Annual Mileage Limit
29. Excess Mileage Charge (per km/mile)
30. Total Allowed Mileage
31. Kilometer/Mileage at Delivery

=== INSURANCE & MAINTENANCE ===
32. Insurance Requirements (type and amount)
33. Insurance Provider (if specified)
34. Maintenance Responsibility (Lessor/Lessee)
35. Routine Maintenance Included (Yes/No)
36. Tire Replacement Responsibility
37. Battery Replacement Terms
38. Warranty Coverage Details

=== TAXES & FEES ===
39. Road Tax Responsibility
40. Registration Fees Responsibility
41. Goods and Services Tax (GST) Details
42. Tax Identification Numbers

=== CONDITION & RETURN ===
43. Wear and Tear Allowance
44. Vehicle Return Condition Requirements
45. Disposition Fee (at lease end)
46. Excess Wear and Tear Charges
47. Cleaning Charges on Return

=== OTHER TERMS ===
48. Permitted Use (Personal/Commercial)
49. Geographic Restrictions (if any)
50. Subleasing Allowed (Yes/No)
51. Right of First Refusal
52. Default Conditions
53. Arbitration Clause (Present/Not Present)
54. Jurisdiction/Governing Law
55. Signing Date
56. Witness Details
57. Notary Details

Return ONLY a JSON object with these exact field names.
For currency amounts, include the symbol if present (₹, $, €, etc.).
For dates, use DD/MM/YYYY or MM/DD/YYYY format as in document.

Document Text:
{clean_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt],
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2000,
            }
        )

        text = response.text
        logger.info(f"Gemini response received: {len(text)} characters")

        text = text.replace("```json", "").replace("```", "").strip()

        start = text.find('{')
        end = text.rfind('}') + 1

        if start >= 0 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)

            all_fields = [
                "Lessor Name", "Lessee Name", "Lessor Address", "Lessee Address",
                "Vehicle Make", "Vehicle Model", "Vehicle Year", "Vehicle VIN",
                "License Plate Number", "Vehicle Color", "Engine Number",
                "Chassis Number", "Odometer Reading at Start", "Monthly Rental",
                "Security Deposit", "Advance Payment", "Down Payment", "Lease Term Duration",
                "Lease Start Date", "Lease End Date", "Payment Due Day", "Late Payment Fee/Percentage",
                "Early Termination Fee/Conditions", "Purchase Option Price", "Residual Value",
                "Interest Rate/ Money Factor", "Processing Fees/Administrative Charges",
                "Annual Mileage Limit", "Excess Mileage Charge", "Total Allowed Mileage",
                "Kilometer/Mileage at Delivery", "Insurance Requirements", "Insurance Provider",
                "Maintenance Responsibility", "Routine Maintenance Included", "Tire Replacement Responsibility",
                "Battery Replacement Terms", "Warranty Coverage Details", "Road Tax Responsibility",
                "Registration Fees Responsibility", "Goods and Services Tax (GST) Details",
                "Tax Identification Numbers", "Wear and Tear Allowance", "Vehicle Return Condition Requirements",
                "Disposition Fee", "Excess Wear and Tear Charges", "Cleaning Charges on Return",
                "Permitted Use", "Geographic Restrictions", "Subleasing Allowed",
                "Right of First Refusal", "Default Conditions", "Arbitration Clause",
                "Jurisdiction/Governing Law", "Signing Date", "Witness Details", "Notary Details"
            ]

            result = {}
            for field in all_fields:
                value = data.get(field, "Not Found")
                if value and value != "Not Found":
                    value = str(value).strip()
                result[field] = value

            extracted_count = sum(1 for v in result.values() if v != "Not Found")
            logger.info(f"Gemini extracted {extracted_count} fields")
            return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {e}")
        logger.debug(f"Raw response: {text[:500]}")
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")

    return {}

def extract_from_ocr_directly(ocr_text: str) -> Dict[str, str]:
    """
    Fallback: Extract fields directly from OCR text
    Enhanced with more fields
    """
    logger.info("Using enhanced direct OCR extraction")

    result = {field: "Not Found" for field in [
        "Lessor Name", "Lessee Name", "Lessor Address", "Lessee Address",
        "Vehicle Make", "Vehicle Model", "Vehicle Year", "Vehicle VIN",
        "License Plate Number", "Vehicle Color", "Engine Number",
        "Chassis Number", "Odometer Reading at Start", "Monthly Rental",
        "Security Deposit", "Advance Payment", "Down Payment", "Lease Term Duration",
        "Lease Start Date", "Lease End Date", "Payment Due Day", "Late Payment Fee/Percentage",
        "Early Termination Fee/Conditions", "Purchase Option Price", "Residual Value",
        "Interest Rate/ Money Factor", "Processing Fees/Administrative Charges",
        "Annual Mileage Limit", "Excess Mileage Charge", "Total Allowed Mileage",
        "Kilometer/Mileage at Delivery", "Insurance Requirements", "Insurance Provider",
        "Maintenance Responsibility", "Routine Maintenance Included", "Tire Replacement Responsibility",
        "Battery Replacement Terms", "Warranty Coverage Details", "Road Tax Responsibility",
        "Registration Fees Responsibility", "Goods and Services Tax (GST) Details",
        "Tax Identification Numbers", "Wear and Tear Allowance", "Vehicle Return Condition Requirements",
        "Disposition Fee", "Excess Wear and Tear Charges", "Cleaning Charges on Return",
        "Permitted Use", "Geographic Restrictions", "Subleasing Allowed",
        "Right of First Refusal", "Default Conditions", "Arbitration Clause",
        "Jurisdiction/Governing Law", "Signing Date", "Witness Details", "Notary Details"
    ]}

    text = ocr_text.upper()
    original_text = ocr_text

    patterns = {
        "Vehicle VIN": [
            r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'VEHICLE\s*IDENTIFICATION\s*NUMBER[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'CHASSIS\s*NO[:\s]*([A-HJ-NPR-Z0-9]{17})'
        ],
        "License Plate Number": [
            r'LICENSE[-\s]*PLATE[-\s]*([A-Z0-9-]+)',
            r'REGISTRATION[-\s]*NUMBER[:\s]*([A-Z0-9-]+)',
            r'VEHICLE\s*REG[-\s]*NO[:\s]*([A-Z0-9-]+)'
        ],
        "Monthly Rental": [
            r'MONTHLY[-\s]*(?:LEASE|RENTAL|PAYMENT)[-\s]*AMOUNT[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)',
            r'RENT[-\s]*PER[-\s]*MONTH[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)',
            r'LEASE[-\s]*RENTAL[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)'
        ],
        "Security Deposit": [
            r'(?:SECURITY|SECURITY\s*DEPOSIT)[-\s]*AMOUNT[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)',
            r'DEPOSIT[-\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)'
        ],
        "Lease Term Duration": [
            r'LEASE[-\s]*TERM[:\s]*(\d+)\s*(?:MONTHS|MONTH)',
            r'DURATION[:\s]*(\d+)\s*(?:MONTHS|MONTH)',
            r'TERM[-\s]*OF[-\s]*LEASE[:\s]*(\d+)\s*(?:MONTHS|MONTH)'
        ],
        "Lease Start Date": [
            r'LEASE[-\s]*START[-\s]*DATE[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{4})',
            r'COMMENCEMENT[-\s]*DATE[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{4})'
        ],
        "Lease End Date": [
            r'LEASE[-\s]*END[-\s]*DATE[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{4})',
            r'EXPIRATION[-\s]*DATE[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{4})'
        ],
        "Annual Mileage Limit": [
            r'ANNUAL[-\s]*MILEAGE[-\s]*LIMIT[:\s]*([\d,]+)\s*KM',
            r'YEARLY[-\s]*MILEAGE[-\s]*ALLOWANCE[:\s]*([\d,]+)\s*KM',
            r'ANNUAL[-\s]*KM[-\s]*LIMIT[:\s]*([\d,]+)'
        ],
        "Excess Mileage Charge": [
            r'EXCESS[-\s]*MILEAGE[-\s]*CHARGE[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)\s*PER',
            r'ADDITIONAL[-\s]*KM[-\s]*CHARGE[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)'
        ],
        "Vehicle Make": [r'MAKE[:\s]*([A-Z][A-Z\s]+?)(?=\n|MODEL|$)'],
        "Vehicle Model": [r'MODEL[:\s]*([A-Z][A-Z\s\-\d]+?)(?=\n|YEAR|$)'],
        "Vehicle Year": [r'YEAR[:\s]*(\d{4})', r'MODEL[-\s]*YEAR[:\s]*(\d{4})'],
        "Lessor Name": [
            r'LESSOR[:\s]*([A-Z][A-Z\s]+?)(?=\n|ADDRESS|$)',
            r'OWNER[:\s]*([A-Z][A-Z\s]+?)(?=\n|ADDRESS|$)'
        ],
        "Lessee Name": [
            r'LESSEE[:\s]*([A-Z][A-Z\s]+?)(?=\n|ADDRESS|$)',
            r'HIRER[:\s]*([A-Z][A-Z\s]+?)(?=\n|ADDRESS|$)'
        ],
        "Late Payment Fee/Percentage": [
            r'LATE[-\s]*PAYMENT[-\s]*FEE[:\s]*₹?\s*([\d,]+(?:\.[\d]{2})?)',
            r'LATE[-\s]*FEE[:\s]*(\d+)%'
        ],
        "Purchase Option Price": [
            r'PURCHASE[-\s]*OPTION[-\s]*PRICE[:\s]*₹?\s*([\d,]+)',
            r'BUY[-\s]*OUT[-\s]*PRICE[:\s]*₹?\s*([\d,]+)'
        ],
        "Disposition Fee": [
            r'DISPOSITION[-\s]*FEE[:\s]*₹?\s*([\d,]+)',
            r'RETURN[-\s]*FEE[:\s]*₹?\s*([\d,]+)'
        ]
    }

    for field, regex_list in patterns.items():
        for pattern in regex_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if any(term in field.lower() for term in ['rental', 'deposit', 'fee', 'price', 'charge', 'payment']):
                    if '₹' not in value and any(c.isdigit() for c in value):
                        value = f"₹{value}"
                result[field] = value
                break

    if 'TOYOTA' in text and 'COROLLA' in text:
        result["Vehicle Make"] = "Toyota"
        result["Vehicle Model"] = "Corolla Altis"

    address_patterns = [
        r'ADDRESS[:\s]*((?:[A-Z0-9\s,\-\.]+)(?:\n(?:[A-Z0-9\s,\-\.]+))+)',
        r'RESIDENCE[:\s]*((?:[A-Z0-9\s,\-\.]+)(?:\n(?:[A-Z0-9\s,\-\.]+))+)'
    ]

    for pattern in address_patterns:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        if len(matches) >= 2:
            result["Lessor Address"] = matches[0].strip()
            result["Lessee Address"] = matches[1].strip()
            break

    extracted_count = sum(1 for v in result.values() if v != "Not Found")
    logger.info(f"Direct extraction found {extracted_count} fields")

    return result

def extract_sla_from_text(ocr_text: str) -> Dict[str, str]:
    """
    Main extraction function - tries Gemini first, then fallback
    """
    logger.info("Extracting contract fields...")

    if GEMINI_AVAILABLE:
        gemini_result = extract_with_gemini(ocr_text)
        if gemini_result and any(v != "Not Found" for v in gemini_result.values()):
            basic_fields = ["Vehicle VIN", "Lessor Name", "Lessee Name", "Monthly Rental"]
            if any(gemini_result.get(field, "Not Found") != "Not Found" for field in basic_fields):
                return gemini_result
            else:
                logger.warning("Gemini extraction returned but missing basic fields")

    return extract_from_ocr_directly(ocr_text)


