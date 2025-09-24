# apps/______register/converters/pdf_to_json.py
from ..parser.commerce.parser import CommerceRegisterParser
from ..parser.real_estate.real_estate_parser import RealEstateRegisterParser

def pdf_to_json(file_storage, *, domain: str) -> dict:
    raw = file_storage.read()
    if domain == "commerce":
        return CommerceRegisterParser().parse(raw)   # bytes -> dict
    elif domain == "real_estate":
        return RealEstateRegisterParser().parse(raw)
    else:
        raise ValueError("unknown domain")