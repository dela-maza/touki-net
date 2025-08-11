#!/usr/bin/env python3
"""
プロジェクト全体から pyreverse で PlantUML を生成し、docs/uml に配置。
@startuml の直後にテーマ(!include ./theme-dark.puml)を差し込む。

想定ディレクトリ:
- このスクリプトは tools/ 配下に置く
- プロジェクトルート: tools/ の1つ上
- テーマ: docs/uml/theme-dark.puml
"""

from pathlib import Path
import subprocess
import sys
import re
from typing import Iterable

# ルートと出力先
ROOT: Path = Path(__file__).resolve().parents[1]   # tools/ の1つ上 = プロジェクト直下
OUT: Path = ROOT / "docs" / "uml"
OUT.mkdir(parents=True, exist_ok=True)

# 設定（必要に応じて変更）
DIAG_NAME = "touki_net"                 # pyreverse の -p 名（出力ファイル名にも反映）
THEME_INCLUDE = "!include ./theme-dark.puml"
EXPECTED_SOURCES: Iterable[str] = (
    f"classes_{DIAG_NAME}.plantuml",
    f"packages_{DIAG_NAME}.plantuml",
)

def run_pyreverse() -> None:
    """
    プロジェクト全体を対象に pyreverse を実行し、
    カレント(ROOT) に PlantUML 形式の .plantuml を生成する。

    生成物:
      - classes_<DIAG_NAME>.plantuml
      - packages_<DIAG_NAME>.plantuml

    Raises:
        FileNotFoundError: pyreverse コマンドが見つからない場合
        subprocess.CalledProcessError: pyreverse がエラー終了した場合
    """
    try:
        # pyreverse の有無を軽くチェック（--help で存在確認）
        subprocess.run(["pyreverse", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ pyreverse が見つかりません。`pip install pylint` を実行してから再試行してください。", file=sys.stderr)
        raise

    # 実行（プロジェクトルートで走らせる）
    subprocess.run(
        ["pyreverse", "-o", "plantuml", "-p", DIAG_NAME, "."],
        cwd=ROOT,
        check=True
    )

def inject_theme(puml_path: Path) -> None:
    """
    与えられた .puml ファイルの @startuml 行「直後」にテーマを 1 回だけ差し込む。

    既にテーマ行が入っていれば何もしない。

    Args:
        puml_path: 編集対象の .puml ファイルパス
    """
    txt = puml_path.read_text(encoding="utf-8")

    # 既にテーマが含まれていればスキップ
    if THEME_INCLUDE in txt:
        return

    # @startuml の直後に挿入（最初の @startuml のみ対象）
    new_txt = re.sub(
        r"(^@startuml[^\n]*\n)",
        r"\1" + THEME_INCLUDE + "\n",
        txt,
        count=1,
        flags=re.MULTILINE
    )

    # @startuml が無い異常系でも元テキストと変わらないので、その場合は警告だけ出す
    if new_txt == txt:
        print(f"⚠️  {puml_path.name} に @startuml が見つかりませんでした。テーマ挿入をスキップします。")
        return

    puml_path.write_text(new_txt, encoding="utf-8")

def main() -> None:
    """
    1) pyreverse を実行して .plantuml を生成
    2) docs/uml/ に .puml へリネーム配置
    3) テーマ(!include ./theme-dark.puml)を挿入
    """
    try:
        run_pyreverse()
    except Exception:
        # run_pyreverse 内でエラーメッセージ済み。上位に伝播させて終了。
        sys.exit(1)

    # 生成物を docs/uml/ へコピーして拡張子を .puml に変更
    for src_name in EXPECTED_SOURCES:
        src = ROOT / src_name
        if not src.exists():
            print(f"⚠️  期待した出力が見つかりません: {src_name}")
            continue

        dst = OUT / src_name.replace(".plantuml", ".puml")
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        inject_theme(dst)
        print(f"✅ {dst.relative_to(ROOT)} を生成しました")

if __name__ == "__main__":
    main()