# apps/register/converters/json_to_html.py
import json
from flask import render_template_string, render_template

def json_to_html(json_src, *, domain: str) -> str:
    data = json.loads(json_src) if isinstance(json_src, (str, bytes)) else json_src
    # domain毎の専用ページ（中身は presenters/pages/** を include）
    tmpl = f"register/result_{domain}.html"  # 例: result_commerce.html
    return render_template(tmpl, data=data)