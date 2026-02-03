import re
from typing import Tuple, Optional

def extract_currency_amount(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract currency amount"""
    if not text or text == "Not Found":
        return None, None

    match = re.search(r'[\d,]+(?:\.\d+)?', text)
    if not match:
        return None, None

    try:
        amount = float(match.group().replace(',', ''))
        return amount, "INR"
    except:
        return None, None

def parse_duration(text: str) -> Optional[int]:
    """Parse duration to months"""
    if not text or text == "Not Found":
        return None

    text = text.lower()
    months = 0

    year_match = re.search(r'(\d+)\s*years?', text)
    if year_match:
        months += int(year_match.group(1)) * 12

    month_match = re.search(r'(\d+)\s*months?', text)
    if month_match:
        months += int(month_match.group(1))

    if months == 0:
        num_match = re.search(r'(\d+)', text)
        if num_match:
            months = int(num_match.group(1))

    return months if months > 0 else None

def parse_mileage(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Parse mileage"""
    if not text or text == "Not Found":
        return None, None

    match = re.search(r'(\d[\d,]*)', text)
    if match:
        try:
            value = float(match.group(1).replace(',', ''))
            return value, 'km'
        except:
            return None, None

    return None, None
