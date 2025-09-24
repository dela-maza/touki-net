# apps/______register/schemas/commerce.py
# apps/______register/schemas/commerce.py
from dataclasses import dataclass
from typing import Optional
from datetime import date
from apps.______register.constants.organization_type import OrganizationType

@dataclass
class CommerceRegisterSummary:
    organization_type: OrganizationType
    organization_type_code: str
    organization_type_label_ja: str
    organization_type_label_en: str

    name: str                        # 商号・名称（法人の正式名）
    head_office_address: str         # 本店（主たる事務所）所在地
    purpose: str                     # 目的（複数ある場合はまとめて格納 or Listに後で拡張）
    representative_name: str         # 代表者氏名
    representative_address: str      # 代表者住所
    company_number: str              # 会社法人等番号
    incorporation_date: date         # 設立年月日

    @classmethod
    def build(
            cls,
            org: OrganizationType,
            name: str,
            head_office_address: str,
            purpose: str,
            representative_name: str,
            representative_address: str,
            company_number: str,
            incorporation_date: date,
    ):
        return cls(
            organization_type=org,
            organization_type_code=org.value,
            organization_type_label_ja=org.label_ja,
            organization_type_label_en=org.label_en,
            name=name,
            head_office_address=head_office_address,
            purpose=purpose,
            representative_name=representative_name,
            representative_address=representative_address,
            company_number=company_number,
            incorporation_date=incorporation_date,
        )