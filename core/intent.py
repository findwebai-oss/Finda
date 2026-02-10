"""Intent detection utility for routing queries to product or flight search."""

import re


FLIGHT_KEYWORDS = {
    'tr': ['uçuş', 'bilet', 'uçak',  'seyahat', 'havayolu', 'gidiş', 'biniş'],
    'en': ['flight', 'ticket', 'airplane', 'plane', 'fly', 'airport', 'airline', 'trip', 'travel'],
}

TURKISH_CITIES = {
    'istanbul': ['ist', 'iow'],
    'ankara': ['ank', 'esr'],
    'izmir': ['izm', 'adb'],
    'antalya': ['ant', 'gny'],
    'adana': ['adp', 'gwj'],
    'bursa': ['yeg'],
    'gaziantep': ['gno'],
    'bodrum': ['bjv'],
    'alanya': ['acy'],
    'erzurum': ['erz'],
    'kayseri': ['kay'],
    'konya': ['kya'],
    'trabzon': ['trz'],
}


def detect_flight_intent(query):
    """
    Detect if a query is flight-related.
    
    Returns:
        dict: {'is_flight': bool, 'confidence': float, 'reason': str}
    """
    if not query or not isinstance(query, str):
        return {'is_flight': False, 'confidence': 0.0, 'reason': 'empty'}
    
    query_lower = query.lower().strip()
    
    # Check for exact city code patterns (e.g., "ist ank")
    city_code_pattern = r'\b([a-z]{3})\s+([a-z]{3})\b'
    if re.search(city_code_pattern, query_lower):
        return {'is_flight': True, 'confidence': 0.9, 'reason': 'city_code_pattern'}
    
    # Check for flight keywords in Turkish
    for keyword in FLIGHT_KEYWORDS['tr']:
        if keyword in query_lower:
            return {'is_flight': True, 'confidence': 0.8, 'reason': f'keyword_tr: {keyword}'}
    
    # Check for flight keywords in English
    for keyword in FLIGHT_KEYWORDS['en']:
        if keyword in query_lower:
            return {'is_flight': True, 'confidence': 0.8, 'reason': f'keyword_en: {keyword}'}
    
    # Check for city name patterns (e.g., "istanbul ankara", "ankara to istanbul")
    cities_pattern = '|'.join(list(TURKISH_CITIES.keys()))
    if re.search(rf'\b({cities_pattern})\b.*\b({cities_pattern})\b', query_lower):
        return {'is_flight': True, 'confidence': 0.85, 'reason': 'city_names'}
    
    # Check for "to" or "->" patterns with cities
    if re.search(r'\b(?:to|den|dan|\'dan|from)\b', query_lower):
        if re.search(rf'\b({cities_pattern})\b', query_lower):
            return {'is_flight': True, 'confidence': 0.7, 'reason': 'city_with_direction'}
    
    # Check for date patterns (YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY)
    date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4})'
    has_date = bool(re.search(date_pattern, query))
    
    # If has date + city code/keyword = likely flight
    if has_date and (re.search(city_code_pattern, query_lower) or 
                     any(kw in query_lower for kw in FLIGHT_KEYWORDS['tr'] + FLIGHT_KEYWORDS['en'])):
        return {'is_flight': True, 'confidence': 0.9, 'reason': 'date_with_flight_marker'}
    
    return {'is_flight': False, 'confidence': 0.0, 'reason': 'no_flight_markers'}

# """
# Intent detection utility for routing queries to product or flight search.
# Improved version with strict flight intent rules.
# """

# import re


# FLIGHT_KEYWORDS = {
#     'tr': ['uçuş', 'bilet', 'uçak', 'seyahat', 'havayolu', 'gidiş', 'dönüş'],
#     'en': ['flight', 'ticket', 'airplane', 'plane', 'fly', 'airport', 'airline', 'trip', 'travel'],
# }

# # Smalltalk & weather blocker
# BLOCKED_PATTERNS = [
#     'nasılsın', 'merhaba', 'selam',
#     'hava nasıl', 'bugün hava', 'kaç derece',
#     'iyi misin', 'naber'
# ]

# TURKISH_CITIES = {
#     'istanbul': ['ist', 'saw'],
#     'ankara': ['ank', 'esb'],
#     'izmir': ['izm', 'adb'],
#     'antalya': ['ant', 'gny'],
#     'adana': ['adp'],
#     'bursa': ['yeg'],
#     'gaziantep': ['gno'],
#     'bodrum': ['bjv'],
#     'alanya': ['gzl'],
#     'erzurum': ['erz'],
#     'kayseri': ['asr'],
#     'konya': ['kya'],
#     'trabzon': ['trz'],
# }

# ALL_CITY_CODES = []
# for codes in TURKISH_CITIES.values():
#     ALL_CITY_CODES.extend(codes)

# CITIES_PATTERN = '|'.join(TURKISH_CITIES.keys())
# CITY_CODE_PATTERN = r'\b([a-z]{3})\s+([a-z]{3})\b'

# DATE_PATTERN = r'(\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4})'


# def detect_flight_intent(query: str):
#     """
#     Detect if a query is flight-related.

#     Returns:
#         dict: {'is_flight': bool, 'confidence': float, 'reason': str}
#     """

#     if not query or not isinstance(query, str):
#         return {'is_flight': False, 'confidence': 0.0, 'reason': 'empty'}

#     query_lower = query.lower().strip()

#     # Block smalltalk & weather
#     for bp in BLOCKED_PATTERNS:
#         if bp in query_lower:
#             return {'is_flight': False, 'confidence': 0.0, 'reason': 'blocked_smalltalk'}

#     # Flags
#     has_city_name = bool(re.search(rf'\b({CITIES_PATTERN})\b', query_lower))
#     has_city_code = bool(re.search(CITY_CODE_PATTERN, query_lower))
#     has_date = bool(re.search(DATE_PATTERN, query_lower))

#     has_keyword = any(
#         kw in query_lower for kw in FLIGHT_KEYWORDS['tr'] + FLIGHT_KEYWORDS['en']
#     )

#     # Case 1: IATA code pattern (IST ESB)
#     if has_city_code:
#         return {'is_flight': True, 'confidence': 0.95, 'reason': 'city_code_pattern'}

#     # Case 2: Two city names (istanbul ankara)
#     if re.search(rf'\b({CITIES_PATTERN})\b.*\b({CITIES_PATTERN})\b', query_lower):
#         return {'is_flight': True, 'confidence': 0.9, 'reason': 'two_city_names'}

#     # Case 3: Keyword + city
#     if has_keyword and has_city_name:
#         return {'is_flight': True, 'confidence': 0.85, 'reason': 'keyword_with_city'}

#     # Case 4: Date + keyword or city
#     if has_date and (has_keyword or has_city_name or has_city_code):
#         return {'is_flight': True, 'confidence': 0.9, 'reason': 'date_with_route'}

#     return {'is_flight': False, 'confidence': 0.0, 'reason': 'no_flight_markers'}


# # ------------------------
# # TEST (optional)
# # ------------------------
# if __name__ == "__main__":
#     tests = [
#         "SAW ESB",
#         "istanbul ankara uçak bileti",
#         "12.02.2026 istanbul ankara",
#         "bugün hava nasıl",
#         "nasılsın",
#         "ağrının yüz ölçümü",
#         "uçak bileti",
#         "ankara izmir"
#     ]

#     for t in tests:
#         print(t, "=>", detect_flight_intent(t))
# """
# Intent detection utility for routing queries to product or flight search.
# Flight intent triggers even with keywords only (no city required).
# """

# import re


# FLIGHT_KEYWORDS = {
#     "tr": ["uçak", "uçuş", "bilet", "hava", "havayolu", "seyahat"],
#     "en": ["flight", "ticket", "airplane", "plane", "fly", "airport", "airline", "travel"],
# }

# TURKISH_CITIES = {
#     "istanbul": ["ist", "saw"],
#     "ankara": ["esb"],
#     "izmir": ["adb"],
#     "antalya": ["ayt"],
#     "adana": ["ada"],
#     "bursa": ["yei"],
#     "gaziantep": ["gzt"],
#     "bodrum": ["bjv"],
#     "alanya": ["gzk"],
#     "erzurum": ["erz"],
#     "kayseri": ["asr"],
#     "konya": ["kya"],
#     "trabzon": ["tzx"],
# }


# def detect_flight_intent(query: str) -> dict:
#     """
#     Detect if a query is flight-related.

#     Returns:
#         dict: {
#             'is_flight': bool,
#             'confidence': float,
#             'reason': str
#         }
#     """

#     if not query or not isinstance(query, str):
#         return {"is_flight": False, "confidence": 0.0, "reason": "empty"}

#     q = query.lower().strip()

#     # 1️⃣ IATA code pattern (IST ESB)
#     if re.search(r"\b[a-z]{3}\s+[a-z]{3}\b", q):
#         return {"is_flight": True, "confidence": 0.95, "reason": "city_code_pattern"}

#     # 2️⃣ City name pattern (istanbul ankara)
#     cities_pattern = "|".join(TURKISH_CITIES.keys())
#     if re.search(rf"\b({cities_pattern})\b.*\b({cities_pattern})\b", q):
#         return {"is_flight": True, "confidence": 0.9, "reason": "city_names"}

#     # 3️⃣ Direction words (istanbul'dan ankara'ya)
#     if re.search(r"\b(to|from|dan|den|ya|ye)\b", q) and re.search(
#         rf"\b({cities_pattern})\b", q
#     ):
#         return {"is_flight": True, "confidence": 0.85, "reason": "city_with_direction"}

#     # 4️⃣ Date pattern + keyword
#     date_pattern = r"(\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4})"
#     has_date = bool(re.search(date_pattern, q))
#     has_keyword = any(kw in q for kw in FLIGHT_KEYWORDS["tr"] + FLIGHT_KEYWORDS["en"])

#     if has_date and has_keyword:
#         return {"is_flight": True, "confidence": 0.9, "reason": "date_with_keyword"}

#     # 5️⃣ Keyword alone is enough (uçak / bilet / flight)
#     if has_keyword:
#         return {"is_flight": True, "confidence": 0.7, "reason": "keyword_only"}

#     return {"is_flight": False, "confidence": 0.0, "reason": "no_match"}


# # =========================
# # Simple manual tests
# # =========================
# if __name__ == "__main__":
#     tests = [
#         "uçak",
#         "uçak bileti",
#         "flight ticket",
#         "istanbul ankara",
#         "IST ESB",
#         "12.02.2026 istanbul ankara",
#         "ankara'dan izmir'e",
#         "telefon al",
#         "laptop fiyatları",
#     ]

#     for t in tests:
#         print(t, "=>", detect_flight_intent(t))

