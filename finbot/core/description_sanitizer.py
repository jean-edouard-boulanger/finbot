"""Sanitize raw transaction descriptions to extract the core merchant name."""

import re

# Payment prefixes to strip (order matters: longest first)
_PAYMENT_PREFIXES = [
    "CARD PAYMENT TO",
    "CARD PAYMENT",
    "PAYMENT TO",
    "POS PURCHASE",
    "POS",
    "DD",
    "STO",
    "BGC",
    "FPO",
    "DEB",
    "BP",
]

_PREFIX_PATTERN = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in _PAYMENT_PREFIXES) + r")\s+",
    re.IGNORECASE,
)

# Card number prefix at start of description: "X8163 ...", "CARTE X8163 ..."
_CARD_PREFIX_PATTERN = re.compile(r"^(?:CARTE\s+)?X\d{4}\s+", re.IGNORECASE)

# French fee wrappers: strip everything up to and including the comma
# e.g. "FRAIS CARTE A L'ETRANGER HORS UE, X8163 ..."
#      "Frais carte UE hors zone Euro, X8163 ..."
#      "Frais carte étranger hors UE, X8163 ..."
_FRENCH_FEE_WRAPPER_PATTERN = re.compile(
    r"^FRAIS\s+CARTE[^,]*,\s*",
    re.IGNORECASE,
)

# French banking prefixes (longest first)
_FRENCH_BANKING_PREFIXES = [
    "VIREMENT EMIS WEB",
    "VIREMENT EN VOTRE FAVEUR DE",
    "VIREMENT EN VOTRE FAVEUR",
    "VIR INST DE",
    "PISP-",
]

_FRENCH_BANKING_PATTERN = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in _FRENCH_BANKING_PREFIXES) + r")\s*",
    re.IGNORECASE,
)

# Merchant code prefixes: "UEP*", "MP*", "PPG*" (2-4 uppercase letters + asterisk at start)
_MERCHANT_CODE_PATTERN = re.compile(r"^[A-Z]{2,4}\*")

# Card masks: *1234, XXXX1234, ****1234 (but NOT X1234 at word start, handled separately)
_CARD_MASK_PATTERN = re.compile(r"[*]{1,4}\d{4}|X{2,4}\d{4}")

# Dates: DD/MM, DD/MM/YY, DD/MM/YYYY, DDMMM (e.g. 14MAR), YYYY-MM-DD
_DATE_PATTERN = re.compile(
    r"\b\d{2}/\d{2}(?:/\d{2,4})?\b"
    r"|\b\d{2}[A-Z]{3}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
)

# Trailing reference IDs: 8+ alphanumeric characters (with at least one digit) at end
_TRAILING_REF_PATTERN = re.compile(r"\s+(?=[A-Z0-9]*\d)[A-Z0-9]{8,}$")

# Trailing store/terminal IDs: 3-5 digit numbers at end
_TRAILING_STORE_ID_PATTERN = re.compile(r"\s+\d{3,5}$")


# Multiple whitespace
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_description(raw: str) -> str:
    """Clean a raw transaction description to extract the core merchant name.

    Steps:
    1. Uppercase
    2. Strip French fee wrappers (must be before other prefix stripping)
    3. Strip common payment prefixes
    4. Strip French banking prefixes
    5. Strip card number prefix (X8163, CARTE X8163)
    6. Strip merchant code prefixes (UEP*, MP*, PPG*)
    7. Strip card masks
    8. Strip embedded dates
    9. Strip trailing reference IDs (8+ alphanumeric chars with at least one digit)
    10. Strip trailing store/terminal IDs (3-5 digit numbers)
    11. Normalize whitespace
    """
    result = raw.upper()
    result = _FRENCH_FEE_WRAPPER_PATTERN.sub("", result)
    result = _PREFIX_PATTERN.sub("", result)
    result = _FRENCH_BANKING_PATTERN.sub("", result)
    result = _CARD_PREFIX_PATTERN.sub("", result)
    result = _MERCHANT_CODE_PATTERN.sub("", result)
    result = _CARD_MASK_PATTERN.sub("", result)
    result = _DATE_PATTERN.sub("", result)
    result = _WHITESPACE_PATTERN.sub(" ", result).strip()
    result = _TRAILING_REF_PATTERN.sub("", result)
    result = _TRAILING_STORE_ID_PATTERN.sub("", result)
    result = _WHITESPACE_PATTERN.sub(" ", result).strip()
    return result
