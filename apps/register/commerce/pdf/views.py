# apps/register/commerce/pdf/views.py
import json
from typing import List
from flask import Blueprint, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pprint import pprint
from ...shared.pdf_reader import pdf_file_to_text
from .forms import PDFUploadForm
from .services.parser import parse_corporation_registry
from .services.normalize import extract_table_block, normalize_text
from .services.debug_utils import split_section_blocks, Section  # ← 追加
from .services.adapters import to_registry_sections             # ← 追加
from .services.structures import RegistrySection                # ← 追加
register_commerce_pdf_bp = Blueprint(
    "register_commerce_pdf",
    __name__,
    url_prefix="/pdf",
    template_folder="templates",
)
bp = register_commerce_pdf_bp

@bp.app_template_filter("pretty_json")
def pretty_json(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)

@bp.route("/upload", methods=["GET", "POST"])
def upload():
    form = PDFUploadForm()
    if form.validate_on_submit():
        f = form.file.data
        fn = secure_filename(f.filename or "")
        if not fn.lower().endswith(".pdf"):
            flash("PDFを選んでください。", "warning")
            return redirect(url_for(".upload"))

        text = pdf_file_to_text(f)

        # parse_corporation_registry は Path 前提なので一時保存して渡す
        import tempfile, os, pathlib
        f.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(f.read())
            tmp_path = pathlib.Path(tmp.name)
        try:
            result = parse_corporation_registry(tmp_path)
        finally:
            os.unlink(tmp_path)

        return render_template("result.html", filename=fn, text=text, result=result)
    return render_template("upload.html", form=form)

@bp.route("/debug_norm", methods=["GET", "POST"])
def debug_norm():
    form = PDFUploadForm()
    if form.validate_on_submit():
        f = form.file.data
        fn = secure_filename(f.filename or "")
        if not fn.lower().endswith(".pdf"):
            flash("PDFを選んでください。", "warning")
            return redirect(url_for(".debug_norm"))

        raw = pdf_file_to_text(f)
        table_block = extract_table_block(raw)
        norm = normalize_text(table_block)

        return render_template(
            "debug_norm.html",
            filename=fn,
            raw=raw,
            table_block=table_block,
            norm=norm,
            form=form,
        )
    return render_template("upload.html", form=form)

@bp.route("/debug_sections", methods=["GET", "POST"])
def debug_sections():
    """
    現行テンプレは sections を「文字列リスト」として描画。
    解析用に (sec_text, items) も sections_with_items として同梱。
    """
    form = PDFUploadForm()
    if form.validate_on_submit():
        f = form.file.data
        fn = secure_filename(f.filename or "")
        if not fn.lower().endswith(".pdf"):
            flash("PDFを選んでください。", "warning")
            return redirect(url_for(".debug_sections"))

        raw = pdf_file_to_text(f)
        norm = normalize_text(extract_table_block(raw))

        sections_with_items: List[Section] = split_section_blocks(norm)
        sections = [sec_text for sec_text, _ in sections_with_items]  # 互換表示用

        return render_template(
            "debug_sections.html",
            filename=fn,
            sections=sections,
            sections_with_items=sections_with_items,
            form=form,
        )
    return render_template("upload.html", form=form)

@bp.route("/debug_objects", methods=["GET", "POST"])
def debug_objects():
    """
    split_section_blocks → RegistrySection/Item/EntryBlock(Line) に変換して、
    values() / histories() を可視化するデバッグ用。
    """
    form = PDFUploadForm()
    if form.validate_on_submit():
        f = form.file.data
        fn = secure_filename(f.filename or "")
        if not fn.lower().endswith(".pdf"):
            flash("PDFを選んでください。", "warning")
            return redirect(url_for(".debug_objects"))

        raw  = pdf_file_to_text(f)
        norm = normalize_text(extract_table_block(raw))
        sections_with_items: List[Section] = split_section_blocks(norm)

        # 変換してオブジェクト化
        reg_sections: List[RegistrySection] = to_registry_sections(sections_with_items)

        # JSON文字列を Python 側で整形してから渡す（ensure_ascii=False, indent=2）
        import json
        sections_json      = [s.to_json() for s in reg_sections]  # 既に ensure_ascii=False, indent=2 のはず
        values_json        = [json.dumps(s.values(),    ensure_ascii=False, indent=2) for s in reg_sections]
        histories_json     = [json.dumps(s.histories(), ensure_ascii=False, indent=2) for s in reg_sections]

        # Jinjaでzipは使えないので、ここでペアリングして渡す
        paired = list(zip(reg_sections, sections_json, values_json, histories_json))

        return render_template(
            "debug_objects.html",
            filename=fn,
            paired=paired,   # ← これだけ見ればOK
            form=form,
        )
    return render_template("upload.html", form=form)