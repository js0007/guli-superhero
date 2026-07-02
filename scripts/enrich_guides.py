# -*- coding: utf-8 -*-
"""根据每页英文内容，生成对齐 02 风格的丰富互动指导"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "content"
SKIP = {"02_Wake Up"}

CHARS = ("Bella", "Jojo", "Ducky", "Teeny", "Leo", "Gyuri")

# ---------- 文本分析 ----------

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def page_text(items: list[dict]) -> str:
    return " ".join(x["en"] for x in items)


def zh_of(en: str, items: list[dict], cache: dict) -> str:
    en = norm(en)
    for x in items:
        if norm(x["en"]) == en or en in norm(x["en"]) or norm(x["en"]) in en:
            return x["zh"]
    if en in cache:
        return cache[en]
    return ""


def pick_sentences(items: list[dict]) -> dict:
    ens = [norm(x["en"]) for x in items]
    questions = [s for s in ens if "?" in s]
    exclaims = [s for s in ens if s.endswith("!") and "?" not in s]
    imperatives = [s for s in ens if re.match(r"^(Look|Say|Let's|Wake|Can you|Find|Count|Help)", s, re.I)]
    intros = [s for s in ens if re.match(r"^This is ", s, re.I)]
    lets = [s for s in ens if re.match(r"^Let'?s ", s, re.I)]
    sounds = [s for s in ens if re.search(r"\b(meow|grrr|whoosh|ssss|tickle|tap|shake)\b", s, re.I)]
    counts = [s for s in ens if re.search(r"\b(how many|count|one, two|1, 2)\b", s, re.I)]
    finds = [s for s in ens if re.search(r"\b(find|look|see|where)\b", s, re.I)]
    emotions = [s for s in ens if re.search(r"\b(happy|sad|scared|nervous|afraid|excited)\b", s, re.I)]
    wakes = [s for s in ens if re.search(r"wake up", s, re.I)]
    greetings = [s for s in ens if re.search(r"\b(hello|hi everybody)\b", s, re.I)]
    return {
        "all": ens,
        "questions": questions,
        "exclaims": exclaims,
        "imperatives": imperatives,
        "intros": intros,
        "lets": lets,
        "sounds": sounds,
        "counts": counts,
        "finds": finds,
        "emotions": emotions,
        "wakes": wakes,
        "greetings": greetings,
    }


def detect_tags(p: dict, page_idx: int, total: int) -> list[str]:
    items = p["extendText"]
    text = page_text(items).lower()
    tags = []
    s = pick_sentences(items)

    if page_idx == 0:
        tags.append("opening")
    if page_idx >= total - 2:
        tags.append("closing")
    if s["counts"]:
        tags.append("count")
    if s["intros"]:
        tags.append("introduce")
    if s["finds"] or re.search(r"\blook[!]|\bsee\b", text):
        tags.append("observe")
    if s["greetings"] or re.search(r'\bsay,\s*["\']?hello', text, re.I):
        tags.append("greet")
    if s["sounds"]:
        tags.append("sound")
    if s["wakes"]:
        tags.append("wake")
    if s["emotions"]:
        tags.append("emotion")
    if s["lets"]:
        tags.append("lets")
    if s["questions"]:
        tags.append("question")
    if re.search(r"\b(birthday|party|cake|candle|present)\b", text):
        tags.append("party")
    if re.search(r"\b(eat|yum|hungry|food|sandwich|picnic|apple)\b", text):
        tags.append("food")
    if re.search(r"\b(shadow|sun|light|dark)\b", text):
        tags.append("shadow")
    if re.search(r"\b(rain|umbrella|puddle|wet)\b", text):
        tags.append("rain")
    if re.search(r"\b(scrub|wash|bath|soap|bubble|shower)\b", text):
        tags.append("bath")
    if re.search(r"\b(hide|seek|found|hiding)\b", text):
        tags.append("hide")
    if re.search(r"\b(follow|track|footprint|lead)\b", text):
        tags.append("follow")
    if re.search(r"\b(race|ready|go|scooter|bike|helmet)\b", text):
        tags.append("race")
    if re.search(r"\b(pat|seed|plant|dig|hole)\b", text):
        tags.append("plant")
    if re.search(r"\b(monster|scary|brave|save|help)\b", text):
        tags.append("brave")
    if not tags:
        tags.append("story")
    return tags


def chars_in(text: str) -> list[str]:
    return [c for c in CHARS if c.lower() in text.lower()]


def noun_hints(text: str) -> str:
    t = text.lower()
    for kw, label in (
        (r"\bplayground\b", "游乐场设施"),
        (r"\bfrog", "青蛙"),
        (r"\bhedgehog", "刺猬"),
        (r"\bsnake", "蛇"),
        (r"\bshadow", "影子"),
        (r"\bmushroom", "蘑菇"),
        (r"\btree", "树"),
        (r"\bflower", "花"),
        (r"\bapple", "苹果"),
        (r"\bcake", "蛋糕"),
        (r"\bballoon", "气球"),
        (r"\bscooter", "滑板车"),
        (r"\btrack", "脚印"),
        (r"\bsoap|bubble", "泡泡"),
    ):
        if re.search(kw, t):
            return label
    return "画面细节"


# ---------- 单条 guide 构造 ----------

def g(step, action, en, zh, note):
    return {"step": step, "action": action, "en": en, "zh": zh, "note": note}


def next_unused(s: dict, used: set[str]) -> str | None:
    for pool in (s["questions"], s["exclaims"], s["imperatives"], s["lets"],
                 s["wakes"], s["sounds"], s["intros"], s["all"]):
        for en in pool:
            if en and en not in used:
                return en
    return None


def finalize_guides(guides: list[dict], s: dict, z) -> list[dict]:
    used = {g["en"] for g in guides}
    fillers = [
        ("互动拓展", "指着纸质书画面，邀请孩子跟读这句；不会就点英文听发音", "关键词跟读即可，不必整句一次说对"),
        ("跟读巩固", "选本页最喜欢的一句，妈妈先说一遍，再请孩子复述 2 遍", "复述允许中英夹杂，敢说就比说对更重要"),
    ]
    fi = 0
    while len(guides) < 3:
        en = next_unused(s, used)
        if not en:
            break
        name, action, note = fillers[fi % len(fillers)]
        fi += 1
        guides.append(g(f"PLACEHOLDER {name}", action, en, z(en), note))
        used.add(en)

    # 去重：若 en 重复，换一句
    seen: set[str] = set()
    for guide in guides:
        if guide["en"] in seen:
            en = next_unused(s, seen)
            if en:
                guide["en"] = en
                guide["zh"] = z(en)
        seen.add(guide["en"])

    labels = ["①", "②", "③"]
    for i, guide in enumerate(guides[:3]):
        tail = re.sub(r"^[①②③]\s*|^PLACEHOLDER\s*", "", guide["step"])
        guide["step"] = f"{labels[i]} {tail}"
    return guides[:3]


def build_guides_for_page(p: dict, page_idx: int, total: int, book: str, cache: dict) -> list[dict]:
    items = p["extendText"]
    s = pick_sentences(items)
    tags = detect_tags(p, page_idx, total)
    text = page_text(items)
    hint = noun_hints(text)
    chars = chars_in(text)
    char_str = "、".join(chars[:2]) if chars else "角色"

    def z(en: str) -> str:
        zt = zh_of(en, items, cache)
        if zt:
            return zt
        return cache.get(en, en)

    guides = []

    # --- ① 第一环节：观察 / 认识 / 数数 ---
    if "count" in tags and s["counts"]:
        en = s["counts"][0]
        guides.append(g(
            "① 数数互动",
            f"指着纸质书上的{hint}，和孩子一起大声数，数完击掌庆祝",
            en, z(en),
            "数错不要紧，重点是开口跟节奏；可以中英文混着说数字",
        ))
    elif "introduce" in tags and s["intros"]:
        en = s["intros"][0]
        name = re.sub(r"^This is ", "", en, flags=re.I).strip("!.")
        guides.append(g(
            "① 认识角色",
            f"指着纸质书上的{name}，问孩子叫什么、是什么动物，再点「整页原音」",
            en, z(en),
            "角色介绍页不用一次讲完所有词，熟悉感比准确度更重要",
        ))
    elif "opening" in tags and "race" in tags:
        en = s["all"][0] if s["all"] else ""
        guides.append(g(
            "① 运动暖场",
            f"指着{hint}，问孩子会不会骑、出门要不要戴头盔，再听「整页原音」",
            en, z(en),
            "安全提示（头盔、护膝）可以顺带用中文强调一句",
        ))
    elif "opening" in tags:
        if len(chars) >= 3:
            en = next((x for x in s["all"] if any(c.lower() in x.lower() for c in chars)), s["all"][0])
            guides.append(g(
                "① 认识伙伴",
                f"指着纸质书上{'、'.join(chars[:4])}，让孩子认一认谁是谁，再点「整页原音」",
                en, z(en),
                "角色名不用一次讲完，熟悉感会贯穿全系列",
            ))
        else:
            en = s["all"][0] if s["all"] else ""
            guides.append(g(
                "① 观察暖场",
                "先不急着读字，让孩子看纸质书跨页图，说出看到了什么；再播放「整页原音」",
                en, z(en),
                "第一遍允许只听不说，建立「看图→听→说」的顺序",
            ))
    elif "observe" in tags or "finds" in s:
        en = s["finds"][0] if s["finds"] else (s["imperatives"][0] if s["imperatives"] else s["all"][0])
        guides.append(g(
            "① 观察找一找",
            f"在纸质书上用手指圈出{hint}，让孩子找全、找齐再往下讲",
            en, z(en),
            "找物游戏让页面「活」起来，别一直线性往下读",
        ))
    elif "party" in tags:
        en = s["questions"][0] if s["questions"] else s["all"][0]
        guides.append(g(
            "① 派对情境",
            f"问孩子有没有参加过生日会，指着画面里的{hint}一一认读",
            en, z(en),
            "先激活生活经验，孩子更容易代入故事",
        ))
    elif "food" in tags:
        en = s["all"][0]
        guides.append(g(
            "① 美食引入",
            f"指着纸质书上的食物，问孩子喜不喜欢吃、是什么味道",
            en, z(en),
            "可以假装闻一下、尝一下，调动感官记忆",
        ))
    elif "bath" in tags:
        en = s["imperatives"][0] if s["imperatives"] else s["all"][0]
        guides.append(g(
            "① 洗澡情境",
            f"联系孩子自己的洗澡经验，指着{hint}问「你洗澡时也这样吗？」",
            en, z(en),
            "生活场景绘本最适合母子互相比划动作",
        ))
    elif "race" in tags:
        en = s["all"][0]
        guides.append(g(
            "① 运动暖场",
            f"指着{hint}，问孩子会不会骑、要不要戴头盔，再听整页原音",
            en, z(en),
            "安全提示（头盔、护膝）可以顺带用中文强调一句",
        ))
    else:
        en = s["all"][0] if s["all"] else ""
        guides.append(g(
            "① 看图讲述",
            f"对照纸质书画面，先描述你看到了什么，再邀请孩子补充",
            en, z(en),
            "妈妈先示范描述，孩子更愿意接着开口",
        ))

    # --- ② 第二环节：提问 / 打招呼 / 声音 / 情绪 ---
    used_en = {guides[0]["en"]}

    if "greet" in tags:
        en = s["greetings"][0] if s["greetings"] else (
            next((x for x in s["all"] if "hello" in x.lower()), s["all"][1] if len(s["all"]) > 1 else s["all"][0])
        )
        if en not in used_en:
            guides.append(g(
                "② 打招呼跟读",
                "拍手或挥手说 Hello，邀请孩子向画面里的朋友打招呼",
                en, z(en),
                "打招呼句式比单词更重要，说完可问孩子最想和谁说 Hello",
            ))
            used_en.add(en)
    elif "sound" in tags and s["sounds"]:
        en = s["sounds"][0]
        guides.append(g(
            "② 声音模仿",
            "先妈妈示范叫声，再让孩子跟读；可以配手势或身体动作",
            en, z(en),
            "学动物/声音叫能降低开口压力，孩子更愿意参与",
        ))
        used_en.add(en)
    elif "emotion" in tags and s["emotions"]:
        en = s["emotions"][0]
        guides.append(g(
            "② 情绪共鸣",
            f"指着{char_str}的表情，问 happy 还是 sad，让孩子说说为什么",
            en, z(en),
            "情绪词用表情比划比翻译更有效，允许孩子用中文回答",
        ))
        used_en.add(en)
    elif "question" in tags and s["questions"]:
        en = s["questions"][0]
        if en not in used_en:
            guides.append(g(
                "② 提问互动",
                f"指着{hint}提问，等 3～5 秒给孩子思考时间，不会就一起听音频再试",
                en, z(en),
                "开放式问题没有标准答案，孩子沉默时可以先用中文聊",
            ))
            used_en.add(en)
    elif "hide" in tags:
        en = s["questions"][0] if s["questions"] else s["all"][-1]
        guides.append(g(
            "② 躲猫猫",
            "用手遮住一部分画面，让孩子猜谁藏在哪里，揭晓时夸张一点",
            en, z(en),
            "悬念感是这册的核心玩法，别急着揭晓答案",
        ))
        used_en.add(en)
    elif "shadow" in tags:
        en = s["questions"][0] if s["questions"] else s["all"][1] if len(s["all"]) > 1 else s["all"][0]
        guides.append(g(
            "② 影子游戏",
            "用手电筒或阳光下比划影子，对照书页讨论影子为什么会动",
            en, z(en),
            "能联系生活实验最好，孩子印象更深",
        ))
        used_en.add(en)
    elif "follow" in tags:
        en = s["questions"][0] if s["questions"] else s["all"][-1]
        guides.append(g(
            "② 跟着做",
            "妈妈说 Follow me，带孩子做一步动作（走、跳、停），再对照书页",
            en, z(en),
            "全身参与比坐着听记得牢，注意安全别闹太猛",
        ))
        used_en.add(en)
    elif "plant" in tags:
        en = s["lets"][0] if s["lets"] else s["all"][-1]
        guides.append(g(
            "② 动手模仿",
            "假装挖洞、放种子、拍土，带孩子做 Pat pat pat 的节奏",
            en, z(en),
            "节奏感用拍腿/拍手做出来，英文会跟着嘴巴走",
        ))
        used_en.add(en)
    elif "brave" in tags:
        en = s["exclaims"][0] if s["exclaims"] else s["all"][-1]
        guides.append(g(
            "② 勇气时刻",
            "语气变得紧张又期待，问孩子害不害怕、要不要帮忙",
            en, z(en),
            "共情比练句型重要——怕就说 Me too, a little scared",
        ))
        used_en.add(en)
    else:
        cand = next_unused(s, used_en)
        if not cand and s["questions"]:
            cand = s["questions"][0]
        if cand and cand not in used_en:
            is_q = "?" in cand
            guides.append(g(
                "② 互动提问" if is_q else "② 跟读互动",
                f"指着{hint}，{'用问句邀请孩子回答' if is_q else '邀请孩子跟读这句'}，等几秒给孩子思考时间",
                cand, z(cand),
                "开放式问题没有标准答案，孩子沉默时可以先用中文聊" if is_q
                else "不会说就重复关键词，或点英文听发音",
            ))
            used_en.add(cand)

    # --- ③ 第三环节：跟读 / 喊叫 / 一起做 ---
    if "wake" in tags and s["wakes"]:
        en = next((x for x in reversed(s["wakes"]) if x not in used_en), None)
        if en:
            guides.append(g(
                "③ 喊醒跟读",
                "音量逐渐加大，第三遍最大声，带动孩子一起喊 Wake up",
                en, z(en),
                "配合拍书页或拍腿增加节奏感，喊完可以问为什么还不醒",
            ))
            used_en.add(en)
    elif "lets" in tags and s["lets"]:
        en = next((x for x in reversed(s["lets"]) if x not in used_en), None)
        if en:
            guides.append(g(
                "③ 一起做",
                "妈妈说 Let's...，带孩子完整做一遍动作或跟读整句",
                en, z(en),
                "「一起做」比「听我讲」更能留住注意力",
            ))
            used_en.add(en)
    elif s["exclaims"]:
        en = next((x for x in s["exclaims"] if x not in used_en), None)
        if en:
            guides.append(g(
                "③ 重点跟读",
                "挑本页最有情绪的句子，重复 2～3 遍，一遍比一遍有表现力",
                en, z(en),
                "感叹句最适合练语气，夸张一点孩子反而记得牢",
            ))
            used_en.add(en)

    return finalize_guides(guides, s, z)


# ---------- 批量处理 ----------

def enrich_book(path: Path, cache: dict) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = data["pages"]
    total = len(pages)
    book = data.get("book", "")
    for i, p in enumerate(pages):
        p["guides"] = build_guides_for_page(p, i, total, book, cache)
    return data


def main():
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="en", target="zh-CN")
    except ImportError:
        translator = None

    cache: dict[str, str] = {}

    def fill_zh(guides, items):
        for guide in guides:
            if not guide["zh"] or guide["zh"] == guide["en"]:
                en = guide["en"]
                zt = zh_of(en, items, cache)
                if not zt and translator:
                    try:
                        zt = translator.translate(en)
                        cache[en] = zt
                    except Exception:
                        zt = en
                guide["zh"] = zt or guide["zh"] or en

    for path in sorted(CONTENT.glob("*.json")):
        if path.parent.name == "en":
            continue
        folder = json.loads(path.read_text(encoding="utf-8")).get("folder", "")
        if folder in SKIP:
            continue
        print(f"ENRICH {path.name}")
        data = enrich_book(path, cache)
        for p in data["pages"]:
            fill_zh(p["guides"], p["extendText"])
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")


if __name__ == "__main__":
    main()
