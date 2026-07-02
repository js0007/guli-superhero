# -*- coding: utf-8 -*-
"""批量生成带读内容：提取英文 → 翻译 → 丰富指导 → 构建 site"""
import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SRC = ROOT / "原始素材"
DATA = ROOT / "data" / "content"
DATA_EN = DATA / "en"
SKIP = {"02_Wake Up"}

PAGE_IDS = [
    "0-1", "2-3", "4-5", "6-7", "8-9",
    "10-11", "12-13", "14-15", "16-17", "18-19",
]

STOP = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can",
    "need", "dare", "ought", "used", "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "what", "which", "who", "whom", "whose",
    "where", "when", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "don", "now", "look", "say", "let", "see", "oh",
    "yes", "hm", "hello", "page",
}

VOCAB_CN = {
    "playground": "游乐场", "lion": "狮子", "fishing": "钓鱼", "octopus": "章鱼",
    "frog": "青蛙", "spring": "春天", "noise": "响声", "field": "田野",
    "snoring": "打呼噜", "slug": "鼻涕虫", "lilypad": "睡莲叶", "wake": "醒来",
    "scrub": "搓洗", "soap": "肥皂", "bath": "洗澡", "bubble": "泡泡",
    "hide": "躲藏", "seek": "寻找", "found": "找到了", "behind": "在后面",
    "pat": "轻拍", "seed": "种子", "hole": "洞", "water": "水",
    "ready": "准备好了", "scooter": "滑板车", "helmet": "头盔", "race": "比赛",
    "birthday": "生日", "party": "派对", "cake": "蛋糕", "candle": "蜡烛",
    "yum": "好吃", "hungry": "饿了", "sandwich": "三明治", "picnic": "野餐",
    "shadow": "影子", "sun": "太阳", "follow": "跟着", "rainy": "下雨的",
    "umbrella": "雨伞", "puddle": "水坑", "who": "谁",
}


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    parts = []
    for t in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if t.text:
            parts.append(t.text)
        if t.tail:
            parts.append(t.tail)
    return "".join(parts)


def read_doc(path: Path) -> str:
    try:
        import win32com.client
    except ImportError:
        raise RuntimeError("读取 .doc 需要 pywin32：pip install pywin32") from None
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(path.resolve()))
    text = doc.Content.Text
    doc.Close(False)
    word.Quit()
    return text


def find_source_doc(src_dir: Path) -> Path | None:
    docx = sorted(src_dir.glob("*.docx"))
    if docx:
        return docx[0]
    doc = sorted(src_dir.glob("*.doc"))
    return doc[0] if doc else None


def read_source_doc(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return read_doc(path)


def parse_doc_pages(text: str) -> dict[str, str]:
    text = text.replace("\r", "\n")
    text = re.sub(r"(\w+)Page\s+(\d+-\d+)\s*:?", r"Page \2:", text, flags=re.I)
    text = re.sub(r"\bage\s+(\d+-\d+)\s*:", r"Page \1:", text, flags=re.I)
    text = re.sub(r"^BOOK[-\w ]+\s*", "", text, flags=re.I | re.M)
    text = re.sub(r"^Book\s+\d+\s+.*?\n+", "", text, flags=re.I | re.M)
    chunks = re.split(r"Page\s+(\d+-\d+)\s*:?\s*", text, flags=re.I)
    pages = {}
    for i in range(1, len(chunks), 2):
        pages[chunks[i]] = chunks[i + 1].strip()
    return pages


def clean_page_body(text: str, book_title: str) -> str:
    text = text.strip()
    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    first = re.sub(r"[^\w\s]", " ", book_title).split()[0]
    for prefix in (book_title, first, book_title.upper(), first.upper()):
        if text.upper().startswith(prefix.upper() + " "):
            text = text[len(prefix) :].strip()
            break
    text = re.sub(r"([.!?])(?=[A-Z\"'])", r"\1 ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"^[\s:;]+", "", text)
    return text


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([.!?])\s*(?=[A-Z\"'])", r"\1\n", text)
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    if not parts:
        parts = [text.strip()] if text.strip() else []
    merged = []
    for p in parts:
        if merged and len(p) < 20 and p[0].islower():
            merged[-1] += " " + p
        else:
            merged.append(p)
    return [s for s in merged if len(s) > 2]


def pick_vocab(sentences: list[str]) -> list[dict]:
    words = []
    for s in sentences:
        for w in re.findall(r"[A-Za-z']+", s):
            lw = w.lower().strip("'")
            if len(lw) < 3 or lw in STOP or lw.isdigit():
                continue
            if lw not in words:
                words.append(lw)
    picks = words[:3]
    while len(picks) < 3:
        picks.append("hello")
    return [{"w": w, "ipa": "", "cn": VOCAB_CN.get(w, w)} for w in picks[:3]]


def pick_question(sentences: list[str]) -> str | None:
    for s in sentences:
        if "?" in s:
            return s
    return None


def build_page_skeleton(page_id: str, body: str, book_title: str) -> dict:
    sentences = split_sentences(body)
    if not sentences:
        sentences = [f"Let's read {book_title} together. Turn to page {page_id} in your book."]

    extend = [{"en": s, "zh": ""} for s in sentences[:4]]
    q = pick_question(sentences)
    guides = [
        {
            "step": "① 导读",
            "action": "对照纸质书画面，先点「整页原音」听一遍",
            "en": sentences[0],
            "zh": "",
            "note": "点击英文可听发音（系统 TTS）",
        },
        {
            "step": "② 互动",
            "action": "指着画面邀请孩子回答或跟读",
            "en": q or sentences[min(1, len(sentences) - 1)],
            "zh": "",
            "note": "不会说就一起听音频再试",
        },
    ]
    if len(sentences) >= 3:
        guides.append(
            {
                "step": "③ 跟读",
                "action": "挑一句孩子最感兴趣的，重复 2～3 遍",
                "en": sentences[-1],
                "zh": "",
                "note": "可配合拍腿或指图增加趣味",
            }
        )

    return {
        "id": page_id,
        "extendText": extend,
        "guides": guides,
        "vocab": pick_vocab(sentences),
    }


def book_display(folder: str) -> str:
    return folder.split("_", 1)[1]


def extract_book(folder: str) -> dict:
    src_dir = SRC / folder
    title = book_display(folder)
    doc = find_source_doc(src_dir)
    if not doc:
        raise FileNotFoundError(f"{folder}: 未找到 doc/docx")
    page_texts = parse_doc_pages(read_source_doc(doc))
    pages = []
    for pid in PAGE_IDS:
        body = page_texts.get(pid, "")
        if body:
            body = clean_page_body(body, title)
        if not body:
            body = f"This is {title}. Please read page {pid} with your child."
        pages.append(build_page_skeleton(pid, body, title))
    return {"book": title, "folder": folder, "pages": pages}


def cmd_extract() -> None:
    DATA_EN.mkdir(parents=True, exist_ok=True)
    for folder in sorted(os.listdir(SRC)):
        if folder in SKIP or not (SRC / folder).is_dir():
            continue
        data = extract_book(folder)
        path = DATA_EN / f"{folder}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"EXTRACT  {path.name}")


def cmd_build() -> None:
    import build_all
    build_all.build()


def cmd_enrich() -> None:
    import enrich_guides
    enrich_guides.main()


def cmd_translate() -> None:
    import translate_content
    translate_content.main()


def main() -> None:
    parser = argparse.ArgumentParser(description="带读版内容构建工具")
    parser.add_argument(
        "command",
        choices=["extract", "translate", "enrich", "build", "all"],
        nargs="?",
        default="build",
    )
    args = parser.parse_args()
    if args.command == "extract":
        cmd_extract()
    elif args.command == "translate":
        cmd_translate()
    elif args.command == "enrich":
        cmd_enrich()
    elif args.command == "build":
        cmd_build()
    else:
        cmd_extract()
        cmd_translate()
        cmd_enrich()
        cmd_build()


if __name__ == "__main__":
    main()
