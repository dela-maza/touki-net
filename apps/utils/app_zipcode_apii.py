# apps/utils/app_zipcode_api.py
from __future__ import annotations
from flask import Flask, request, jsonify
import re, requests

app = Flask(__name__)

# -------- 住所の正規化＆町丁レベル切り出し --------
def normalize_jp_addr(s: str) -> str:
    z2h = str.maketrans("０１２３４５６７８９　－ー―−", "0123456789 -----")
    s = (s or "").translate(z2h)
    s = re.sub(r"[‐-‒–—―]", "-", s)    # ダッシュ類を統一
    s = re.sub(r"\s+", "", s)          # 空白除去
    return s

def cut_to_town(addr: str) -> str:
    s = normalize_jp_addr(addr)
    # 「〇丁目」以降をカット（漢数字・算用数字対応）
    s = re.sub(r"(?:[一二三四五六七八九十百千万]+|[0-9]+)丁目.*$", "", s)
    # 最初の数字（番地開始）以降をカット
    s = re.sub(r"[0-9].*$", "", s)
    # 末尾の連結記号を掃除
    s = re.sub(r"[-のノ之]+$", "", s)
    return s

# -------- 外部API（ZipCloud）ラッパ --------
def search_zipcode_by_address(address: str) -> list[dict] | None:
    """
    ZipCloud: 住所→郵便番号検索
    参考: https://zipcloud.ibsnet.co.jp/ （無料・要レート制御）
    """
    try:
        # ZipCloud は 'address' クエリで都道府県+市区町村+町名を渡すと検索可能
        resp = requests.get(
            "https://zipcloud.ibsnet.co.jp/api/search",
            params={"address": address},
            timeout=5,
        )
        data = resp.json()
        # data: { status:int, message:str|None, results:[{zipcode, address1, address2, address3, kana1..}]|None }
        if data.get("status") != 200 or not data.get("results"):
            return None
        return data["results"]
    except Exception:
        return None

# -------- エンドポイント --------
@app.post("/api/zipcode")
def api_zipcode():
    """
    JSON:
      { "address": "東京都青梅市千ヶ瀬町１−１−７" }
    Response:
      { "ok": true, "zipcode": "1980004",
        "prefecture": "東京都", "city": "青梅市", "town": "千ヶ瀬町", "raw_results": [...] }
    """
    j = request.get_json(silent=True) or {}
    address = (j.get("address") or "").strip()
    if not address:
        return jsonify(ok=False, error="address is required"), 400

    # 町丁までを抽出（番地・号は落とす）
    town_addr = cut_to_town(address)
    if not town_addr:
        return jsonify(ok=False, error="failed_to_parse_address"), 422

    # ZipCloud 検索（まずは町丁までのフルを投げる）
    results = search_zipcode_by_address(town_addr)

    # 見つからない場合は、末尾から少し緩めて再検索（例: 「大字」除去など）
    if not results:
        relaxed = re.sub(r"(大字|字)$", "", town_addr)
        if relaxed != town_addr:
            results = search_zipcode_by_address(relaxed)

    if not results:
        return jsonify(ok=False, error="zipcode_not_found", address=town_addr), 404

    # 最初の候補を代表として返す（必要なら複数返却）
    top = results[0]
    zipcode = (top.get("zipcode") or "").replace("-", "")
    out = {
        "ok": True,
        "zipcode": zipcode,
        "prefecture": top.get("address1"),
        "city": top.get("address2"),
        "town": top.get("address3"),
        "normalized_address": town_addr,
        "raw_results": results,  # UI側で絞り込みたい時に使えるように同梱
    }
    return jsonify(out), 200

if __name__ == "__main__":
    # 開発用
    app.run(debug=True)