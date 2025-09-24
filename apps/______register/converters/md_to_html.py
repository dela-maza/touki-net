# apps/______register/converters/md_to_html.py
from markdown import markdown

def md_to_html(file_storage) -> str:
    text = file_storage.read().decode("utf-8")
    return markdown(text, extensions=["tables","fenced_code","toc"])