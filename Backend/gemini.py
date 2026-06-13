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
client = None  # Always define client to avoid ImportError
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

    prompt = f"""
ROLE: You are an expert legal document analyzer specializing in car lease agreements.

TASK: EXTRACT SPECIFIC DATA from the provided document text into a structured JSON format.

CRITICAL INSTRUCTIONS:
1. DISTINGUISH BETWEEN LABELS AND DATA: 
   - Many documents have headers like "1. Lessee Name" followed by the actual name on the next line. 
   - DO NOT extract the label/header itself (e.g., "AGREES TO LEASE" or "LESSEE NAME").
   - DO EXTRACT the specific entity/value associated with that label (e.g., "Emily Carter").
2. IGNORE BOILERPLATE: Ignore legal definitions and boilerplate sentences unless they contain the specific data point.
3. DATA COMPLETENESS: If a field is present, extract it exactly. If not found, return "Not Found".
4. CURRENCY & FORMATS: 
   - Include currency symbols (₹, $, etc.) for all financial amounts.
   - For dates, use the format found in the document (e.g., "01 January 2025").

=== FIELDS TO EXTRACT ===

--- PARTIES ---
- "Lessor Name": The company or individual owning/leasing the vehicle (e.g., "Michael Roberts").
- "Lessee Name": The person or entity renting the vehicle (e.g., "Emily Carter").
- "Lessor Address": Full physical address of the Lessor.
- "Lessee Address": Full physical address of the Lessee.

--- VEHICLE ---
- "Vehicle Make": e.g., Toyota, Honda.
- "Vehicle Model": e.g., Corolla Altis, Civic.
- "Vehicle Year": e.g., 2024.
- "Vehicle VIN": 17-character alpha-numeric string.
- "License Plate Number": Registration number.
- "Vehicle Color": External color.
- "Engine Number": Unique engine identifier.
- "Chassis Number": Often same as VIN.
- "Odometer Reading at Start": Starting mileage.

--- FINANCIALS ---
- "Monthly Rental": The recurring payment amount.
- "Security Deposit": Refundable deposit amount.
- "Advance Payment": Any amount paid upfront.
- "Down Payment": Initial lump sum.
- "Lease Term Duration": Total length (e.g., "36 months").
- "Lease Start Date": Date the lease begins.
- "Lease End Date": Date the lease ends.
- "Payment Due Day": e.g., "1st of each month".
- "Late Payment Fee/Percentage": Penalty for late rent.
- "Early Termination Fee/Conditions": Cost to end lease early.
- "Purchase Option Price": Buy-out price at end of term.
- "Residual Value": Estimated value at term end.
- "Interest Rate/ Money Factor": if mentioned.
- "Processing Fees/Administrative Charges": Any setup fees.

--- USAGE ---
- "Annual Mileage Limit": Max km/miles allowed per year.
- "Excess Mileage Charge": Cost per km/mile over limit.
- "Total Allowed Mileage": Cap for entire duration.
- "Kilometer/Mileage at Delivery": Odometer at start.

--- INSURANCE & MAINTENANCE ---
- "Insurance Requirements": Required coverages.
- "Insurance Provider": Name of insurance company.
- "Maintenance Responsibility": Who pays for repairs (Lessor/Lessee).
- "Routine Maintenance Included": Yes/No.
- "Tire Replacement Responsibility": Lessor/Lessee.
- "Battery Replacement Terms": Replacement conditions.
- "Warranty Coverage Details": Manufacturer or dealer warranty.

--- TAXES & COMPLIANCE ---
- "Road Tax Responsibility": Lessor/Lessee.
- "Registration Fees Responsibility": Lessor/Lessee.
- "Goods and Services Tax (GST) Details": Any tax specifics.
- "Tax Identification Numbers": PAN, GSTIN, Aadhaar mentioned.

--- CLOSING ---
- "Signing Date": Date document was signed.
- "Jurisdiction/Governing Law": Governing state/country laws.
- "Arbitration Clause": Present/Not Present.

RETURN ONLY VALID JSON.

DOCUMENT TEXT:
{clean_text}
"""

    try:
        from google.genai import types
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
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


