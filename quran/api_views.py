# quran/api_views.py
from __future__ import annotations
from typing import Any, Dict, List
import re
import requests
from requests import RequestException

from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from quran.models import Surah, Ayah
from quran.serializers import SurahSerializer, AyahSerializer
from quran.utils import normalize_arabic


# -------------------------------------------------
# إعدادات عامة وثوابت
# -------------------------------------------------
_SURAH_MIN, _SURAH_MAX = 1, 114
_LIMIT_MAX = 50
_HL_TAG_START = "<mark>"
_HL_TAG_END = "</mark>"

RECITERS = {
    "minshawi": "ar.minshawi",
    "afasy": "ar.alafasy",
    "ajamy": "ar.ajamy",
    "husary": "ar.husary",
}
AUDIO_API_BASE = "https://api.alquran.cloud/v1"


# -------------------------------------------------
# أدوات مساعدة
# -------------------------------------------------
def _safe_int(v: Any, default: int) -> int:
    """تحويل آمن إلى عدد صحيح."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _bound(value: int, lo: int, hi: int) -> int:
    """تقييد القيمة ضمن مجال محدد."""
    return max(lo, min(hi, value))


def _escape_regex(s: str) -> str:
    """هروب النص داخل تعبير نظامي."""
    return re.escape(s)


# -------------------------------------------------
# عرض السورة كاملة
# -------------------------------------------------
@api_view(["GET"])
@cache_page(60)  # كاش دقيقة
def surah_detail(request, number: int = 18):
    """GET /api/surah/18 — إرجاع سورة كاملة (افتراضي: الكهف)."""
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)
    surah = get_object_or_404(Surah, number=num)
    return Response(SurahSerializer(surah).data, status=status.HTTP_200_OK)


# -------------------------------------------------
# عرض آية واحدة
# -------------------------------------------------
@api_view(["GET"])
@cache_page(60)
def ayah_detail(request, number: int = 18, ayah: int = 1):
    """GET /api/surah/18/ayah/<ayah> — آية واحدة فقط."""
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)
    ay = _safe_int(ayah, 1)
    if ay < 1:
        return Response({"detail": "رقم الآية غير صحيح."}, status=status.HTTP_400_BAD_REQUEST)
    surah = get_object_or_404(Surah, number=num)
    a = get_object_or_404(Ayah, surah=surah, number=ay)
    return Response(AyahSerializer(a).data, status=status.HTTP_200_OK)


# -------------------------------------------------
# البحث في السورة
# -------------------------------------------------
@api_view(["GET"])
def search(request):
    """
    GET /api/search?surah=18&q=نص[&offset=0&limit=20&highlight=1]
    - q: نص البحث (مطلوب)
    - surah: رقم السورة (افتراضي 18)
    - offset/limit: ترقيم النتائج (limit<=50)
    - highlight=1: تظليل المطابقة بـ <mark>
    """
    raw_q = (request.GET.get("q") or "").strip()
    if not raw_q:
        return Response(
            {"hits": 0, "results": [], "detail": "حقل q مطلوب."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(raw_q) > 64:
        return Response(
            {"detail": "نص البحث طويل جدًا. الرجاء تقصيره."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    surah_num = _bound(_safe_int(request.GET.get("surah"), 18), _SURAH_MIN, _SURAH_MAX)
    offset = max(0, _safe_int(request.GET.get("offset"), 0))
    limit = _bound(_safe_int(request.GET.get("limit"), 20), 1, _LIMIT_MAX)
    do_hl = _safe_int(request.GET.get("highlight"), 0) == 1

    surah = get_object_or_404(Surah, number=surah_num)
    q_norm = normalize_arabic(raw_q)
    if not q_norm:
        return Response({"hits": 0, "results": []}, status=status.HTTP_200_OK)

    qs = Ayah.objects.filter(surah=surah, normalized__icontains=q_norm).order_by("number")
    total = qs.count()
    rows = list(qs[offset : offset + limit])

    results: List[Dict[str, Any]] = []
    if do_hl:
        pattern = re.compile(_escape_regex(raw_q), flags=re.IGNORECASE)
        for a in rows:
            highlighted = pattern.sub(f"{_HL_TAG_START}\\g<0>{_HL_TAG_END}", a.text)
            results.append({"number": a.number, "text": highlighted, "highlight": True})
    else:
        for a in rows:
            results.append({"number": a.number, "text": a.text})

    return Response(
        {
            "hits": total,
            "offset": offset,
            "limit": limit,
            "count": len(results),
            "results": results,
        },
        status=status.HTTP_200_OK,
    )


# -------------------------------------------------
# تشغيل الصوتيات (القراءات المختلفة)
# -------------------------------------------------
@api_view(["GET"])
@cache_page(60 * 60)
def surah_audio_map(request, number: int = 18):
    """
    GET /api/surah/18/audio?reciter=minshawi
    جلب روابط الصوت للسورة من API خارجي (alquran.cloud).
    """
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)
    rec = (request.GET.get("reciter") or "minshawi").lower().strip()
    edition = RECITERS.get(rec, rec)

    try:
        r = requests.get(f"{AUDIO_API_BASE}/surah/{num}/{edition}", timeout=15)
        r.raise_for_status()
    except RequestException as e:
        return Response({"detail": f"Audio API error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

    payload = r.json()
    if payload.get("code") != 200 or "data" not in payload:
        return Response({"detail": "Unexpected audio API response."}, status=status.HTTP_502_BAD_GATEWAY)

    items = []
    for a in payload["data"].get("ayahs", []):
        n = a.get("numberInSurah")
        url = a.get("audio") or (a.get("audioSecondary") or [None])[0]
        if n and url:
            items.append({"n": int(n), "url": url})

    return Response(
        {"surah": num, "reciter_code": edition, "count": len(items), "items": items},
        status=status.HTTP_200_OK,
    )
