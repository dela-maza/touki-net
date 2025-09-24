# apps/register/shared/pdf_reader.py
from pathlib import Path
import tempfile, os

# =========================
# 1) PDFテキスト抽出（3段フォールバック）
# =========================
def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    PDF→テキストの抽出。
    - まず PyPDF2（軽量・速い）を試し、ダメなら pdfminer（強力）、最後に pdfplumber（表に強い）を試す。
    - いずれでも失敗したら空文字を返す（呼び出し側で判定）。
    """
    text = ""
    # (a) PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
    except Exception:
        pass

    # (b) pdfminer
    if not text.strip():
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(str(pdf_path))
        except Exception:
            pass

    # (c) pdfplumber
    if not text.strip():
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages = []
                for page in pdf.pages:
                    pages.append(page.extract_text() or "")
                text = "\n".join(pages)
        except Exception:
            pass
    return text or ""


# =========================
# 2) Flask FileStorage → テキスト抽出
# =========================
def pdf_file_to_text(file_storage) -> str:
    """
    Flask の FileStorage (form.file.data) を受け取り、
    一時ファイルに保存して PDF からテキストを抽出して返す。
    """
    data = file_storage.read()
    file_storage.seek(0)  # 呼び出し側で再利用できるように戻す

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return extract_text_from_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)