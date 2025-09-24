# apps/______register/views.py
from __future__ import annotations

from flask import Blueprint
import os, uuid
from pathlib import Path
from flask import current_app, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from .forms import RegisterUploadForm

# 任意：拡張子チェック
ALLOWED_EXTS = {"pdf"}

# --------------------------
# ブループリント
# --------------------------
register_bp = Blueprint(
    "______register",
    __name__,
    url_prefix="/______register",
    template_folder="templates",
    static_folder="static",
)


# --------------------------
# 内部ユーティリティ
# --------------------------
def _allowed_file(filename: str) -> bool:
    # filename に "."が含まれる。かつ、"."を右側から分割した最初の配列にALLOWED_EXTS内の文字列が含まれる。
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def _save_upload(file_storage: FileStorage) -> tuple[str, str]:
    """
    アップロードファイルを /uploads/______register/ に保存して token を返す
    戻り値: (token, abs_path)
    """

    # FileStorage型
    # HTML フォームで <input type="file" name="xxx"> を送信すると、
    # Flask 側で request.files["xxx"] に FileStorage オブジェクトが入る。
    upload_root = current_app.config["UPLOAD_FOLDER"]
    save_dir = os.path.join(upload_root, "______register")
    os.makedirs(save_dir, exist_ok=True)  # exist_ok=True : フォルダが存在する場合は、そのまま何もしない。

    # Universally Unique Identifier
    # uuid を先頭に付けて「ユニーク保証」＋「元のファイル名も残す」方式にしてる。
    # 同じ名前のファイルを複数アップロードされると上書きされる。
    # ユーザーが 登記簿.pdf をアップ → c92f3d9d3b...__登記簿.pdf
    token = uuid.uuid4().hex  # 表示用トークン uuid4を使うのが安全で一般的
    ext = file_storage.filename.rsplit(".", 1)[1].lower()

    # ecure_filename() は OS に安全なファイル名に変換してくれる（空白や記号を除去）。
    # ユーザーが ../../../etc/passwd とか妙な名前を付けて送ってくる可能性がある。
    # 全角文字はすべて削除させる。
    safe_name = secure_filename(file_storage.filename) or f"upload.{ext}"
    # 実ファイル名: <token>__<元名>
    save_name = f"{token}__{safe_name}"
    abs_path = os.path.join(save_dir, save_name)
    file_storage.save(abs_path)
    return token, abs_path


def _find_saved_path(token: str) -> str | None:
    """保存先ディレクトリから token に一致するファイルを探す（簡易）"""
    save_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "______register")
    if not os.path.isdir(save_dir):
        return None
    for name in os.listdir(save_dir):
        if name.startswith(token + "__"):
            return os.path.join(save_dir, name)
    return None


# --------------------------
# アップロード
# --------------------------
@register_bp.route("/upload", methods=["GET", "POST"])
def upload():
    form = RegisterUploadForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("入力内容を確認してください。", "danger")
            return render_template("______register/upload.html",
                                   form=form,
                                   title="Register - Upload")

        f = form.file.data
        if not f or not getattr(f, "filename", ""):  # f がオブジェクトなら、その属性 filename を取りに行く
            flash("ファイルを選択してください。", "danger")
            return render_template("______register/upload.html",
                                   form=form,
                                   title="Register - Upload")

        if not _allowed_file(f.filename):
            flash("PDF（.pdf）のみアップロード可能です。", "danger")
            return render_template("______register/upload.html",
                                   form=form,
                                   title="Register - Upload")

        token, _ = _save_upload(f)
        # 解析は別エンドポイントで実行（PRG）
        return redirect(url_for("______register.parse", token=token),
                        code=303)

    # GET：フォーム表示
    return render_template("______register/upload.html",
                           form=form,
                           title="Register - Upload")


# --------------------------
# 解析
# --------------------------
@register_bp.route("/parse/<token>", methods=["GET"])
def parse(token: str):
    """
    保存済みPDFを読み込み、その場で解析して結果表示。
    パーサは後で実装差し替え予定。今はダミーのJSONを返して形だけ作る。
    """
    pdf_path = _find_saved_path(token)
    if not pdf_path or not os.path.exists(pdf_path):
        flash("アップロード済みファイルが見つかりません。再度アップロードしてください。", "danger")
        return redirect(url_for("______register.upload"))

    # --- ここで実パーサに差し替える想定 ---
    # 例）from apps.______register.services.commerce import CommerceRegisterParser
    # data = CommerceRegisterParser(pdf_path).parse()  # dict を返す想定
    # とりあえずダミー
    data = {
        "source": os.path.basename(pdf_path),
        "kind": "commerce_register",
        "company": {
            "name": "（ダミー）株式会社サンプル",
            "company_number": "5123456789012",
            "head_office": "東京都千代田区○○一丁目1番1号",
        },
        "events": [
            {"date": "令和7年6月26日", "type": "役員変更"},
            {"date": "令和7年7月10日", "type": "本店移転"},
        ],
    }
    return render_template("______register/parser_result.html",
                           title="Register - Parsed",
                           token=token,
                           data=data,
                           pdf_path=pdf_path)
