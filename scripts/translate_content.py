# -*- coding: utf-8 -*-
"""将 data/content/en/*.json 翻译为 data/content/*.json"""
import json
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
CONTENT_EN = ROOT / "data" / "content" / "en"
CONTENT = ROOT / "data" / "content"

TRANSLATOR = GoogleTranslator(source="en", target="zh-CN")

NAMES = {"bella", "jojo", "ducky", "teeny", "leo", "gyuri", "teedy"}

VOCAB_OVERRIDES = {
    "playground": "游乐场", "lion": "狮子", "fishing": "钓鱼", "octopus": "章鱼",
    "frog": "青蛙", "spring": "春天", "noise": "响声", "field": "田野",
    "snoring": "打呼噜", "slug": "鼻涕虫", "lilypad": "睡莲叶", "scooter": "滑板车",
    "helmet": "头盔", "birthday": "生日", "party": "派对", "cake": "蛋糕",
    "shadow": "影子", "umbrella": "雨伞", "puddle": "水坑", "picnic": "野餐",
    "sandwich": "三明治", "hungry": "饿了", "soap": "肥皂", "bubble": "泡泡",
    "hide": "躲藏", "seek": "寻找", "seed": "种子", "ready": "准备好了",
    "beautiful": "美丽的", "weather": "天气", "pedal": "踩踏板", "race": "比赛",
    "candle": "蜡烛", "present": "礼物", "rainy": "下雨的", "rain": "雨",
    "follow": "跟着", "yum": "好吃", "scrub": "搓洗", "splash": "溅水",
}


def polish_zh(text: str) -> str:
    text = text.strip()
    text = text.replace("！", "！").replace("？", "？")
    text = re.sub(r"\s+", "", text)
    return text


def translate_en(text: str, cache: dict) -> str:
    text = text.strip()
    if not text:
        return ""
    if text in cache:
        return cache[text]
    try:
        zh = TRANSLATOR.translate(text)
        zh = polish_zh(zh)
        cache[text] = zh
        time.sleep(0.15)
        return zh
    except Exception as e:
        print(f"  WARN translate failed: {text[:50]!r} -> {e}")
        cache[text] = text
        return text


def translate_vocab(word: str) -> str:
    lw = word.lower().strip("'")
    if lw in VOCAB_OVERRIDES:
        return VOCAB_OVERRIDES[lw]
    if lw in NAMES:
        return word.capitalize()
    try:
        return polish_zh(TRANSLATOR.translate(word))
    except Exception:
        return word


def translate_book(data: dict, cache: dict) -> dict:
    out = {"book": data["book"], "folder": data["folder"], "pages": []}
    for page in data["pages"]:
        new_page = {"id": page["id"], "extendText": [], "guides": [], "vocab": []}
        for item in page["extendText"]:
            zh = item.get("zh") or translate_en(item["en"], cache)
            new_page["extendText"].append({"en": item["en"], "zh": zh})
        for g in page["guides"]:
            zh = g.get("zh") or translate_en(g["en"], cache)
            new_page["guides"].append({
                "step": g["step"],
                "action": g["action"],
                "en": g["en"],
                "zh": zh,
                "note": g["note"],
            })
        for v in page["vocab"]:
            cn = v.get("cn")
            if not cn or cn == v["w"] or cn.lower() == v["w"].lower():
                cn = translate_vocab(v["w"])
            new_page["vocab"].append({"w": v["w"], "ipa": v.get("ipa", ""), "cn": cn})
        out["pages"].append(new_page)
    return out


def main() -> None:
    CONTENT.mkdir(parents=True, exist_ok=True)
    cache: dict[str, str] = {}
    for en_path in sorted(CONTENT_EN.glob("*.json")):
        data = json.loads(en_path.read_text(encoding="utf-8"))
        print(f"TRANSLATE {en_path.name} ...")
        translated = translate_book(data, cache)
        out_path = CONTENT / en_path.name
        out_path.write_text(json.dumps(translated, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {out_path.name}")
    print("Done.")


if __name__ == "__main__":
    main()
