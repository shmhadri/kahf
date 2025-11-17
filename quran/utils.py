# quran/utils.py
from __future__ import annotations

import re
from typing import Optional

# نمط للتشكيل والعلامات الزائدة في العربية (حركات، إلخ)
_ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)


def normalize_arabic(text: Optional[str]) -> str:
    """
    تطبيع نص عربي لأغراض البحث:
    - إزالة التشكيل.
    - توحيد بعض الحروف (أ/إ/آ -> ا, ى -> ي, ة -> ه, ...).
    - تقليل الفراغات.

    تُستخدم في: البحث في الآيات داخل quran.api_views.search
    """
    if not text:
        return ""

    t = str(text)

    # إزالة التشكيل
    t = _ARABIC_DIACRITICS_PATTERN.sub("", t)

    # توحيد بعض الحروف الشائعة
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ؤ": "و",
        "ئ": "ي",
        "ة": "ه",
        "ى": "ي",
    }
    for src, dst in replacements.items():
        t = t.replace(src, dst)

    # إزالة الرموز غير الحروف/الأرقام/المسافات العربية
    t = re.sub(r"[^\w\s\u0600-\u06FF]", " ", t)

    # توحيد الفراغات
    t = re.sub(r"\s+", " ", t).strip()

    return t
