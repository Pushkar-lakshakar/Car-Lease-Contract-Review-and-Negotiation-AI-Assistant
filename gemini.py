import os
import json
from dotenv import load_dotenv
from google import genai

# LOAD API KEY
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing in .env")

client = genai.Client(api_key=api_key)

JSON_SCHEMA = {
    "Lessor Name": "",
    "Lessee Name": "",
    "Vehicle Model": "",
    "Monthly Rental": "",
    "Tenure": "",
    "Mileage Cap": "",
    "Mileage Rate": "",
    "Termination Penalty": "",
    "Purchase Price": "",
    "Security Deposit": "",
    "Maintenance": "",
    "Taxes": "",
    "Dispute Resolution": "",
    "Return Conditions": ""
}

BASE_PROMPT = """
Extract SLA fields from the lease agreement text below.

STRICT RULES:
- Output ONLY valid JSON.
- Follow the schema EXACTLY (all keys must exist).
- All values must be strings.
- If information is missing, return "Not Available".
- No markdown. No comments. No explanations.
- Do not include ```json or ``` in output.

JSON SCHEMA TO FOLLOW:
{SCHEMA}

LEASE AGREEMENT TEXT:
{DOC}
"""

# CLEAN RAW MODEL OUTPUT
def force_clean_json(raw: str) -> str:
    if not raw:
        return ""
    s = raw
    s = s.replace("```json", "").replace("```", "")
    s = s.replace("\n", " ").replace("\t", " ")
    return s.strip()


# EXTRACT {...} JSON BLOCK
def extract_json_block(text: str):
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]

    return None


# ENFORCE SCHEMA (ALWAYS RETURNS FULL JSON)
def enforce_schema(data: dict):
    fixed = {}

    for key in JSON_SCHEMA:
        val = data.get(key, "Not Available")

        if val is None or str(val).strip() == "":
            val = "Not Available"

        fixed[key] = str(val)

    return fixed

# GEMINI CALL
def call_gemini(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt]
    )

    return response.text if hasattr(response, "text") else ""


# MAIN EXTRACTOR
def extract_sla_from_text(ocr_text: str) -> dict:

    # 1. FIRST ATTEMPT
    prompt = BASE_PROMPT.replace("{SCHEMA}", json.dumps(JSON_SCHEMA, indent=2)) \
                        .replace("{DOC}", ocr_text)

    raw = call_gemini(prompt)
    cleaned = force_clean_json(raw)
    block = extract_json_block(cleaned)

    # 2. AUTO-REPAIR USING GEMINI AGAIN
    if not block:
        repair_prompt = f"""
Your previous output was NOT valid JSON.

Fix it and output ONLY valid JSON.

SCHEMA:
{json.dumps(JSON_SCHEMA, indent=2)}

BROKEN OUTPUT:
{cleaned}
"""
        raw2 = call_gemini(repair_prompt)
        cleaned2 = force_clean_json(raw2)
        block = extract_json_block(cleaned2)

        if not block:
            return enforce_schema({})

    # 3. SAFE JSON PARSING
    try:
        parsed = json.loads(block)
    except:
        # Final AI-assisted correction
        fix_prompt = f"""
The following is INVALID JSON. Fix it.

Return ONLY corrected JSON:
{block}
"""
        raw3 = call_gemini(fix_prompt)
        cleaned3 = force_clean_json(raw3)
        block2 = extract_json_block(cleaned3)

        if block2:
            try:
                parsed = json.loads(block2)
            except:
                return enforce_schema({})
        else:
            return enforce_schema({})

    # 4. ALWAYS RETURN COMPLETE JSON SCHEMA
    return enforce_schema(parsed)
