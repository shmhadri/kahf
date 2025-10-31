import re
HARAKAT = re.compile(r"[\u064B-\u065F\u0670]")
NON_AR = re.compile(r"[^\u0600-\u06FF0-9\s]")

def normalize_arabic(s: str) -> str:
    if not s:
        return ""
    s = s.replace("إ","ا").replace("أ","ا").replace("آ","ا")
    s = s.replace("ى","ي").replace("ؤ","و").replace("ئ","ي").replace("ة","ه")
    s = HARAKAT.sub("", s)
    s = NON_AR.sub("", s)
    return re.sub(r"\s+"," ", s).strip()
