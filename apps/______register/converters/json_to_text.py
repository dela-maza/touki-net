# apps/______register/converters/json_to_text.py
import json

def json_to_text(json_src, *, domain: str) -> str:
    data = json.loads(json_src) if isinstance(json_src, (str, bytes)) else json_src
    # ドメインごとに文面を整形
    if domain == "commerce":
        # 例：会社名/本店/代表者 などを箇条書き or 1段落に
        lines = [
            f"会社法人等番号：{data.get('company_number','')}",
            f"商号：{data.get('company_name','')}",
            f"本店：{data.get('head_office_address','')}",
            f"代表者：{data.get('rep_title','')}{data.get('rep_name','')}",
        ]
        return "\n".join(filter(None, lines))
    # real_estate も同様に
    return ""