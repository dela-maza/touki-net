# apps/register/schemas/commerce.py
from pydantic import BaseModel
from typing import Optional, List

class Officer(BaseModel):
    title: Optional[str]
    name: Optional[str]

class CommerceRegister(BaseModel):
    company_number: Optional[str]
    company_name: Optional[str]
    head_office_address: Optional[str]
    purpose: Optional[List[str]]
    officers: Optional[List[Officer]]
    # …あとで拡張