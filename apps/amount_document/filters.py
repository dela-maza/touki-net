### amount_document/filters.py
from apps.amount_document.models import AmountDocumentType

def amount_document_type_label(value):
    try:
        return AmountDocumentType(value).label
    except ValueError:
        return ''