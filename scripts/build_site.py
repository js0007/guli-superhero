# -*- coding: utf-8 -*-
"""从 data/content + 原始素材 构建 site/books/"""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "原始素材"
DATA = ROOT / "data" / "content"
SITE = ROOT / "site"
BOOKS = SITE / "books"
TEMPLATE = SITE / "templates" / "book.html"
LOGO_SRC = ROOT / "产出素材" / "古力小超人陪读.png"
LOGO_DST = SITE / "assets" / "logo.png"

PAGE_IDS = [
    "0-1", "2-3", "4-5", "6-7", "8-9",
    "10-11", "12-13", "14-15", "16-17", "18-19",
]


def find_m4a(src_dir: Path, page_id: str) -> str | None:
    for f in src_dir.iterdir():
        if not f.name.endswith(".m4a"):
            continue
        if re.search(rf"Pg\s*{re.escape(page_id)}(?!\d)", f.name, re.I):
            return f.name
    return None


def copy_logo() -> None:
    LOGO_DST.parent.mkdir(parents=True, exist_ok=True)
    if LOGO_SRC.exists():
        shutil.copy2(LOGO_SRC, LOGO_DST)
    elif LOGO_DST.exists():
        return
    else:
        print(f"WARN  logo not found: {LOGO_SRC}")


def build_book(folder: str) -> int:
    content_path = DATA / f"{folder}.json"
    if not content_path.exists():
        raise FileNotFoundError(f"缺少内容文件: {content_path}")

    data = json.loads(content_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    src_dir = SRC / folder
    book_dir = BOOKS / folder

    if book_dir.exists():
        shutil.rmtree(book_dir)
    book_dir.mkdir(parents=True)
    (book_dir / "images").mkdir()
    (book_dir / "audio").mkdir()

    shutil.copy2(content_path, book_dir / "content.json")
    shutil.copy2(TEMPLATE, book_dir / "index.html")

    for pid in PAGE_IDS:
        img = src_dir / f"{pid}.jpg"
        if img.exists():
            shutil.copy2(img, book_dir / "images" / f"{pid}.jpg")
        m4a = find_m4a(src_dir, pid)
        if m4a:
            shutil.copy2(src_dir / m4a, book_dir / "audio" / f"Pg-{pid}.m4a")

    return len(pages)


def build_all() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"缺少模板: {TEMPLATE}")

    copy_logo()
    BOOKS.mkdir(parents=True, exist_ok=True)

    built = 0
    for folder in sorted(os.listdir(SRC)):
        src_dir = SRC / folder
        if not src_dir.is_dir():
            continue
        if not (DATA / f"{folder}.json").exists():
            print(f"SKIP  {folder} (no content.json)")
            continue
        n = build_book(folder)
        print(f"OK    books/{folder}  ({n} pages)")
        built += 1

    print(f"Done. {built} books -> {BOOKS}")


if __name__ == "__main__":
    build_all()
