#!/usr/bin/env python3
"""Build curated seed language packs (EN/RU/ZH/AR) keyed to the N'Ko lexicon.

Each seed entry is a hand-verified translation of a common French headword into
English, Russian, Chinese and Arabic. The N'Ko is taken from the authentic
French→N'Ko lexicon (``app/data/lexicon-fr-nko.json``) by exact French match,
so the script never invents N'Ko — it only attaches translations to real
entries. Words whose French form is not in the lexicon are skipped and
reported.

These packs are intentionally a **partial seed** (common vocabulary), not full
47k-entry translations, which would require a translation source this build
environment cannot reach. Complete a pack later with ``build_langpack.py``.

Run from the repo's ``nko-voice-transcriptor`` directory:
    python scripts/build_seed_langpacks.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "app" / "data"
LEXICON = DATA / "lexicon-fr-nko.json"
OUT_DIR = DATA / "langpacks"

# (fr, en, ru, zh, ar). fr must match a headword in the lexicon.
CURATED: list[tuple[str, str, str, str, str]] = [
    # --- numbers ---
    ("un", "one", "один", "一", "واحد"),
    ("trois", "three", "три", "三", "ثلاثة"),
    ("quatre", "four", "четыре", "四", "أربعة"),
    ("six", "six", "шесть", "六", "ستة"),
    ("neuf", "nine", "девять", "九", "تسعة"),
    # --- greetings / basics ---
    ("bonjour", "hello", "здравствуйте", "你好", "مرحبا"),
    ("merci", "thank you", "спасибо", "谢谢", "شكرا"),
    ("oui", "yes", "да", "是", "نعم"),
    # --- people / family ---
    ("homme", "man", "мужчина", "男人", "رجل"),
    ("femme", "woman", "женщина", "女人", "امرأة"),
    ("enfant", "child", "ребёнок", "孩子", "طفل"),
    ("mère", "mother", "мать", "母亲", "أم"),
    ("père", "father", "отец", "父亲", "أب"),
    ("roi", "king", "король", "国王", "ملك"),
    ("ami", "friend", "друг", "朋友", "صديق"),
    # --- nature / world ---
    ("eau", "water", "вода", "水", "ماء"),
    ("feu", "fire", "огонь", "火", "نار"),
    ("soleil", "sun", "солнце", "太阳", "شمس"),
    ("lune", "moon", "луна", "月亮", "قمر"),
    ("arbre", "tree", "дерево", "树", "شجرة"),
    ("fleur", "flower", "цветок", "花", "زهرة"),
    ("pierre", "stone", "камень", "石头", "حجر"),
    ("terre", "earth", "земля", "土地", "أرض"),
    ("ciel", "sky", "небо", "天空", "سماء"),
    ("vent", "wind", "ветер", "风", "ريح"),
    ("pluie", "rain", "дождь", "雨", "مطر"),
    ("mer", "sea", "море", "海", "بحر"),
    ("fleuve", "river", "река", "河", "نهر"),
    # --- animals ---
    ("animal", "animal", "животное", "动物", "حيوان"),
    ("chien", "dog", "собака", "狗", "كلب"),
    ("chat", "cat", "кошка", "猫", "قطة"),
    ("oiseau", "bird", "птица", "鸟", "طائر"),
    ("poisson", "fish", "рыба", "鱼", "سمك"),
    ("cheval", "horse", "лошадь", "马", "حصان"),
    ("vache", "cow", "корова", "牛", "بقرة"),
    ("chèvre", "goat", "коза", "山羊", "ماعز"),
    ("poule", "hen", "курица", "母鸡", "دجاجة"),
    # --- food ---
    ("nourriture", "food", "еда", "食物", "طعام"),
    ("pain", "bread", "хлеб", "面包", "خبز"),
    ("lait", "milk", "молоко", "牛奶", "حليب"),
    ("riz", "rice", "рис", "米", "أرز"),
    ("viande", "meat", "мясо", "肉", "لحم"),
    # --- body / abstract ---
    ("main", "hand", "рука", "手", "يد"),
    ("tête", "head", "голова", "头", "رأس"),
    ("cœur", "heart", "сердце", "心", "قلب"),
    ("nom", "name", "имя", "名字", "اسم"),
    ("amour", "love", "любовь", "爱", "حب"),
    ("paix", "peace", "мир", "和平", "سلام"),
    ("vérité", "truth", "правда", "真理", "حقيقة"),
    ("force", "strength", "сила", "力量", "قوة"),
    ("santé", "health", "здоровье", "健康", "صحة"),
    ("maladie", "illness", "болезнь", "疾病", "مرض"),
    ("mort", "death", "смерть", "死亡", "موت"),
    ("vie", "life", "жизнь", "生命", "حياة"),
    ("parole", "word", "слово", "话语", "كلمة"),
    # --- places / society ---
    ("pays", "country", "страна", "国家", "بلد"),
    ("langue", "language", "язык", "语言", "لغة"),
    ("dieu", "god", "бог", "神", "إله"),
    ("marché", "market", "рынок", "市场", "سوق"),
    ("chemin", "path", "путь", "路", "طريق"),
    ("ville", "city", "город", "城市", "مدينة"),
    ("village", "village", "деревня", "村庄", "قرية"),
    ("monde", "world", "мир", "世界", "عالم"),
    ("école", "school", "школа", "学校", "مدرسة"),
    ("argent", "money", "деньги", "钱", "مال"),
    ("livre", "book", "книга", "书", "كتاب"),
    # --- time ---
    ("jour", "day", "день", "白天", "يوم"),
    ("temps", "time", "время", "时间", "وقت"),
    ("année", "year", "год", "年", "سنة"),
    ("mois", "month", "месяц", "月", "شهر"),
    ("semaine", "week", "неделя", "星期", "أسبوع"),
    ("matin", "morning", "утро", "早晨", "صباح"),
    # --- verbs (French infinitives) ---
    ("manger", "to eat", "есть", "吃", "أكل"),
    ("boire", "to drink", "пить", "喝", "شرب"),
    ("aller", "to go", "идти", "去", "ذهب"),
    ("venir", "to come", "приходить", "来", "أتى"),
    ("voir", "to see", "видеть", "看", "رأى"),
    ("parler", "to speak", "говорить", "说", "تكلم"),
    ("écrire", "to write", "писать", "写", "كتب"),
    ("lire", "to read", "читать", "读", "قرأ"),
    ("dormir", "to sleep", "спать", "睡觉", "نام"),
    ("travailler", "to work", "работать", "工作", "عمل"),
    ("donner", "to give", "давать", "给", "أعطى"),
    ("prendre", "to take", "брать", "拿", "أخذ"),
    ("savoir", "to know", "знать", "知道", "عرف"),
    ("aimer", "to love", "любить", "爱", "أحب"),
    ("vouloir", "to want", "хотеть", "想要", "أراد"),
    ("faire", "to do", "делать", "做", "فعل"),
    # --- adjectives ---
    ("mauvais", "bad", "плохой", "坏", "سيّئ"),
    ("chaud", "hot", "горячий", "热", "حار"),
    ("froid", "cold", "холодный", "冷", "بارد"),
    ("nouveau", "new", "новый", "新", "جديد"),
    ("vieux", "old", "старый", "老", "قديم"),
    ("rouge", "red", "красный", "红色", "أحمر"),
]

LANGS = ["en", "ru", "zh", "ar"]
LANG_INDEX = {"en": 1, "ru": 2, "zh": 3, "ar": 4}


def main() -> None:
    raw = json.loads(LEXICON.read_text(encoding="utf-8"))
    idx: dict[str, dict] = {}
    for e in raw["entries"]:
        idx.setdefault(e["fr"].strip().lower(), e)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    skipped = []
    packs = {lang: [] for lang in LANGS}
    for row in CURATED:
        fr = row[0].strip().lower()
        entry = idx.get(fr)
        if not entry:
            skipped.append(fr)
            continue
        for lang in LANGS:
            term = row[LANG_INDEX[lang]]
            packs[lang].append({"term": term, "nko": entry["nko"], "cat": entry.get("cat", "")})

    names = {"en": "English", "ru": "Русский", "zh": "中文", "ar": "العربية"}
    for lang in LANGS:
        doc = {
            "_language": lang,
            "_name": names[lang],
            "_partial": True,
            "_source": "Seed pack — translations curated by hand; N'Ko from the "
            "NKo Wuruki / N'Ko Institute lexicon. Complete via build_langpack.py.",
            "_count": len(packs[lang]),
            "entries": packs[lang],
        }
        out = OUT_DIR / f"{lang}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {out.name}: {len(packs[lang])} entries")
    if skipped:
        print(f"skipped (not in lexicon): {skipped}")


if __name__ == "__main__":
    main()
