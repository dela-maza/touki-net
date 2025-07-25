import pdfplumber
import re
from enum import Enum
from typing import Optional, Dict, Any


def clean_text(text: str) -> str:
    """
    テキストの縦棒やタブ、全角スペースを半角スペースに置換し、
    連続空白を単一空白にしてトリムした文字列を返す。
    """
    text = text.replace('│', ' ').replace('\t', ' ').replace('　', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_key(key: str) -> str:
    """
    キー文字列の全角・半角スペースを削除して正規化。
    """
    return key.replace(' ', '').replace('　', '')


def normalize_value(val: str) -> str:
    """
    値文字列の「：」を「．」に置換し、
    かつ必要に応じて末尾に「㎡」を付加。
    """
    val = val.replace('：', '．')
    if val and not val.endswith('㎡'):
        val += ' ㎡'
    return val


class RealEstateType(Enum):
    LAND = "土地"
    BUILDING = "建物"
    UNIT_BUILDING = "区分建物"
    UNIT_BUILDING_WITH_SITE_RIGHT = "敷地権付区分建物"


def extract_real_estate_display_as_dict(pdf_path: str) -> Dict[str, Any]:
    """
    PDFファイルから不動産の表示情報と不動産番号を抽出し、
    辞書にまとめて返す。
    """
    keywords_start = ['不動産の表示', '表題部']
    keywords_end = ['権利部', '乙区', '権利部（甲区）']

    extracted_lines = []
    in_section = False
    real_estate_number: Optional[str] = None  # 不動産番号格納用

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')

            for line in lines:
                # 不動産番号の抽出
                if '不動産番号' in line and real_estate_number is None:
                    parts = line.split()
                    for part in parts:
                        if re.match(r'\d{10,}', part):  # 10桁以上の数字列を探す
                            real_estate_number = part
                            break

                if any(k in line for k in keywords_start):
                    in_section = True
                if any(k in line for k in keywords_end):
                    in_section = False
                if in_section:
                    cleaned = clean_text(line)
                    if cleaned:
                        extracted_lines.append(cleaned)

    data = {
        '一棟の建物の表示': {},
        '敷地権の目的である土地の表示': {},
        '専有部分の建物の表示': {},
        '敷地権の表示': {}
    }

    current_section: Optional[str] = None

    # ㎡付加対象キーの定義（定数化）
    sqm_keys = {'③床面積㎡', '④地積㎡'}

    for line in extracted_lines:
        if '一棟の建物の表示' in line:
            current_section = '一棟の建物の表示'
            continue
        elif '敷地権の目的である土地の表示' in line:
            current_section = '敷地権の目的である土地の表示'
            continue
        elif '専有部分の建物の表示' in line:
            current_section = '専有部分の建物の表示'
            continue
        elif '敷地権の表示' in line:
            current_section = '敷地権の表示'
            continue

        if current_section is None:
            continue

        parts = re.split(r'\s{2,}', line)
        if len(parts) == 2:
            key = normalize_key(parts[0])
            val = normalize_value(parts[1].strip()) if key in sqm_keys else parts[1].strip()
            target_dict = data[current_section]

            if key in target_dict:
                if isinstance(target_dict[key], list):
                    target_dict[key].append(val)
                else:
                    target_dict[key] = [target_dict[key], val]
            else:
                target_dict[key] = val
        else:
            # ②床面積 の複数行対応
            key = '②床面積'
            val = line.strip()
            if val:
                val = val if val.endswith('㎡') else val + ' ㎡'
                target_dict = data[current_section]
                if key not in target_dict:
                    target_dict[key] = []
                target_dict[key].append(val)

    property_record = {
        '不動産番号': real_estate_number,
        '不動産の表示': data
    }

    return property_record


def parse_real_estate_type(pdf_path: str) -> Optional[RealEstateType]:
    """
    PDFから不動産種類（RealEstateType）を判別して返す。
    判別できなければ None。
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                if re.search(r'①\s*種類', line):
                    cleaned_line = clean_text(line)
                    parts = cleaned_line.split(' ')
                    if len(parts) >= 2:
                        kind = parts[1]
                        if kind in ("宅地", "土地"):
                            return RealEstateType.LAND
                        elif kind == "建物":
                            return RealEstateType.BUILDING
                        elif kind in ("区分建物", "専有部分"):
                            return RealEstateType.UNIT_BUILDING
                        elif kind in ("敷地権付区分建物", "敷地権付"):
                            return RealEstateType.UNIT_BUILDING_WITH_SITE_RIGHT
                        elif kind == "居宅":
                            return RealEstateType.BUILDING
    return None


def format_property_description(data: dict) -> str:
    """
    不動産の表示情報辞書を見やすく整形した文字列に変換する。
    """
    lines = []
    for section, contents in data.items():
        lines.append(f"【{section}】")
        for key, val in contents.items():
            if isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  ・{item}")
            else:
                lines.append(f"{key}: {val}")
        lines.append("")
    return "\n".join(lines)


# 実行例
if __name__ == "__main__":
    pdf_file = '福岡市博多区博多駅前３丁目３４１－１００６不動産登記（建物全部事項）2025062300313183.PDF'
    property_record = extract_real_estate_display_as_dict(pdf_file)

    import pprint

    pprint.pprint(property_record)

    real_estate_type = parse_real_estate_type(pdf_file)
    print(f"Real Estate Type: {real_estate_type}")

    formatted_text = format_property_description(property_record['不動産の表示'])
    print("\n=== 不動産の表示 ===")
    print(formatted_text)