# quran/api_views.py
from __future__ import annotations

from typing import Any, Dict, List
import datetime
import re

import requests
from requests import RequestException

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import cache_page

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from quran.models import Surah, Ayah, TafseerEntry
from quran.serializers import SurahSerializer, AyahSerializer
from quran.utils import normalize_arabic

# ============================================================
# إعدادات عامة وثوابت
# ============================================================
_SURAH_MIN, _SURAH_MAX = 1, 114
# نسمح حتى 110 آية (سورة الكهف كاملة) حتى لا ينقص شيء
_LIMIT_MAX = 110
_HL_TAG_START = "<mark>"
_HL_TAG_END = "</mark>"

#: خريطة أسماء القرّاء (المستخدمة في الواجهة) → كود edition في alquran.cloud
RECITERS: Dict[str, str] = {
    "minshawi": "ar.minshawi",
    "afasy": "ar.alafasy",
    "ajamy": "ar.ajamy",
    "husary": "ar.husary",
    "sudais": "ar.abdurrahmanalsudais",
    "shuraim": "ar.saoodshuraym",
    "maher": "ar.mahermualaiqly",
    "ghamdi": "ar.saadghamdi",
    "faris": "ar.faresabbad",
}

AUDIO_API_BASE = "https://api.alquran.cloud/v1"


# ============================================================
# أدوات مساعدة
# ============================================================
def _safe_int(v: Any, default: int) -> int:
    """تحويل آمن إلى int مع قيمة افتراضية عند الفشل."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _bound(value: int, lo: int, hi: int) -> int:
    """تقييد القيمة بين lo و hi."""
    return max(lo, min(hi, value))


def _escape_regex(s: str) -> str:
    """هروب النص للاستخدام داخل تعبير نمطي."""
    return re.escape(s)


def _json_error(message: str, status_code: int = 400) -> Response:
    """رد JSON موحّد للأخطاء."""
    return Response({"detail": message}, status=status_code)


# ============================================================
# 1) عرض سورة كاملة
# ============================================================
@api_view(["GET"])
@cache_page(60)  # تخزين مؤقت لمدة دقيقة
def surah_detail(request, number: int = 18) -> Response:
    """
    GET /api/surah/18

    يعيد سورة كاملة (افتراضيًا: سورة الكهف).
    """
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)
    surah = get_object_or_404(Surah, number=num)
    data = SurahSerializer(surah).data
    return Response(data, status=status.HTTP_200_OK)


# ============================================================
# 2) عرض آية معيّنة من السورة
# ============================================================
@api_view(["GET"])
@cache_page(60)
def ayah_detail(request, number: int = 18, ayah: int = 1) -> Response:
    """
    GET /api/surah/18/ayah/<ayah>

    يعيد آية واحدة من السورة.
    """
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)
    ay = _safe_int(ayah, 1)
    if ay < 1:
        return _json_error("رقم الآية غير صحيح.", status.HTTP_400_BAD_REQUEST)

    surah = get_object_or_404(Surah, number=num)
    a = get_object_or_404(Ayah, surah=surah, number=ay)
    data = AyahSerializer(a).data
    return Response(data, status=status.HTTP_200_OK)


# ============================================================
# 3) البحث في السورة (كلمة أو رقم آية)
# ============================================================
@api_view(["GET"])
def search(request) -> Response:
    """
    GET /api/search?surah=18&q=نص[&offset=0&limit=20&highlight=1]

    - q: نص البحث (مطلوب)
        * لو كان أرقام فقط → يُفسَّر كرقم آية.
        * لو حروف/كلمات → بحث نصي.
    - surah: رقم السورة (افتراضي 18)
    - offset/limit: ترقيم النتائج (limit <= 110)
    - highlight=1: تظليل المطابقة بـ <mark> في النص.
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

    surah_num = _bound(
        _safe_int(request.GET.get("surah"), 18),
        _SURAH_MIN,
        _SURAH_MAX,
    )
    offset = max(0, _safe_int(request.GET.get("offset"), 0))
    limit = _bound(_safe_int(request.GET.get("limit"), 20), 1, _LIMIT_MAX)
    do_hl = _safe_int(request.GET.get("highlight"), 0) == 1

    surah = get_object_or_404(Surah, number=surah_num)

    # --------------------------------------------------------
    # 3-أ) لو البحث عبارة عن رقم فقط → بحث برقم الآية مباشرة
    # --------------------------------------------------------
    if re.fullmatch(r"\d+", raw_q):
        ayah_num = int(raw_q)
        qs = Ayah.objects.filter(surah=surah, number=ayah_num).order_by("number")
        total = qs.count()
        rows = list(qs)

        results: List[Dict[str, Any]] = []
        for a in rows:
            results.append(
                {
                    "number": a.number,
                    "text": a.text,  # لا داعي لتظليل الرقم لأنه غير موجود في نص الآية
                    "highlight": False,
                }
            )

        return Response(
            {
                "hits": total,
                "offset": offset,
                "limit": limit,
                "count": len(results),
                "results": results,
                "search_type": "ayah_number",
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    # 3-ب) بحث نصي داخل normalized و text معًا
    # --------------------------------------------------------
    q_norm = normalize_arabic(raw_q) or raw_q

    qs = (
        Ayah.objects.filter(surah=surah)
        .filter(
            Q(normalized__icontains=q_norm)
            | Q(text__icontains=raw_q)
        )
        .order_by("number")
    )

    total = qs.count()
    rows = list(qs[offset : offset + limit])

    results: List[Dict[str, Any]] = []
    if do_hl:
        # نُظلل الكلمة نفسها كما أُرسِلت في raw_q
        pattern = re.compile(_escape_regex(raw_q), flags=re.IGNORECASE)
        for a in rows:
            highlighted = pattern.sub(
                f"{_HL_TAG_START}\\g<0>{_HL_TAG_END}",
                a.text,
            )
            results.append(
                {
                    "number": a.number,
                    "text": highlighted,
                    "highlight": True,
                }
            )
    else:
        for a in rows:
            results.append({"number": a.number, "text": a.text, "highlight": False})

    return Response(
        {
            "hits": total,
            "offset": offset,
            "limit": limit,
            "count": len(results),
            "results": results,
            "search_type": "text",
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# 4) خريطة الصوت للسورة (روابط MP3 لكل آية)
# ============================================================
@api_view(["GET"])
@cache_page(60 * 60)  # ساعة كاملة
def surah_audio_map(request, number: int = 18) -> Response:
    """
    GET /api/surah/18/audio?reciter=minshawi

    يجلب روابط الصوت للسورة (لكل آية) من API alquran.cloud
    ويعيد بنية بسيطة تستخدمها الواجهة الأمامية.
    """
    num = _bound(_safe_int(number, 18), _SURAH_MIN, _SURAH_MAX)

    # الاسم القادم من الـ <select id="reciter">
    rec_key = (request.GET.get("reciter") or "minshawi").lower().strip()

    # تحويله إلى كود الـ edition الموافق في alquran.cloud
    edition = RECITERS.get(rec_key)
    if not edition:
        return _json_error(
            f"القارئ '{rec_key}' غير مدعوم حاليًا في واجهة الصوت.",
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        r = requests.get(
            f"{AUDIO_API_BASE}/surah/{num}/{edition}",
            timeout=15,
        )
        r.raise_for_status()
    except RequestException as e:
        return _json_error(f"Audio API error: {e}", status.HTTP_502_BAD_GATEWAY)

    payload = r.json()
    # نتأكد أن الاستجابة بالشكل المتوقع
    if payload.get("code") != 200 or "data" not in payload:
        return _json_error(
            "Unexpected audio API response.",
            status.HTTP_502_BAD_GATEWAY,
        )

    items: List[Dict[str, Any]] = []
    for a in payload["data"].get("ayahs", []):
        n = a.get("numberInSurah")
        # بعض الإصدارات تعطي audioSecondary (قائمة) إضافة إلى audio
        url = a.get("audio") or (a.get("audioSecondary") or [None])[0]
        if n and url:
            items.append({"n": int(n), "url": url})

    return Response(
        {
            "surah": num,
            "reciter": rec_key,
            "reciter_code": edition,
            "count": len(items),
            "items": items,
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# 5) API التفسير المختصر
# ============================================================
@api_view(["GET"])
def tafseer_view(request) -> Response:
    """
    GET /api/tafseer?surah=18&ayah=5&lang=ar&source=sadi

    يعيد نص تفسير مختصر من جدول TafseerEntry إن وجد.
    """
    surah = request.GET.get("surah")
    ayah = request.GET.get("ayah")
    lang = request.GET.get("lang", "ar")
    source = request.GET.get("source", "sadi")

    if not surah or not ayah:
        return _json_error(
            "surah و ayah مطلوبان في الاستعلام.",
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        surah_num = int(surah)
        ayah_num = int(ayah)
    except ValueError:
        return _json_error(
            "surah و ayah يجب أن يكونا أعدادًا صحيحة.",
            status.HTTP_400_BAD_REQUEST,
        )

    if not (1 <= surah_num <= _SURAH_MAX):
        return _json_error(
            f"surah يجب أن يكون بين 1 و {_SURAH_MAX}.",
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        entry = TafseerEntry.objects.get(
            surah=surah_num,
            ayah=ayah_num,
            lang=lang,
            source=source,
        )
    except TafseerEntry.DoesNotExist:
        return _json_error(
            "لا يوجد تفسير مختصر مسجَّل لهذه الآية.",
            status.HTTP_404_NOT_FOUND,
        )

    data = {
        "surah": surah_num,
        "ayah": ayah_num,
        "lang": lang,
        "source": entry.source,
        "text": entry.text_short,
        "meta": {
            "next_ayah": ayah_num + 1,
            "prev_ayah": max(1, ayah_num - 1),
        },
    }
    return Response(data, status=status.HTTP_200_OK)


# ============================================================
# 6) أوقات الجمعة / ساعة يُرجى فيها الإجابة
# ============================================================
@api_view(["GET"])
def today_times_view(request) -> Response:
    """
    GET /api/times/today

    يعيد:
    - تاريخ اليوم
    - هل اليوم يوم جمعة؟
    - وقت صلاة الجمعة التقريبي
    - وقت بداية آخر ساعة قبل المغرب
    - التوقيتات كـ timestamp لسهولة استخدام العدّاد في الواجهة.
    """
    tz = timezone.get_default_timezone()
    now = timezone.now().astimezone(tz)

    city = getattr(settings, "QURAN_CITY", "Riyadh")
    jumuah_time_str = getattr(settings, "QURAN_JUMUAH_TIME", "12:15")
    last_hour_str = getattr(settings, "QURAN_FRIDAY_LAST_HOUR", "17:00")

    def parse_time_str(s: str) -> datetime.time:
        h, m = s.split(":")
        return datetime.time(hour=int(h), minute=int(m))

    jumuah_time = parse_time_str(jumuah_time_str)
    last_hour_time = parse_time_str(last_hour_str)

    today = now.date()
    jumuah_dt = datetime.datetime.combine(today, jumuah_time, tz)
    last_hour_dt = datetime.datetime.combine(today, last_hour_time, tz)

    data = {
        "date": today.isoformat(),
        "city": city,
        "is_friday": now.weekday() == 4,  # الاثنين=0 .. الجمعة=4
        "now": now.strftime("%H:%M:%S"),
        "jumuah_time": jumuah_time_str,
        "last_hour_start": last_hour_str,
        "last_hour_timestamp": int(last_hour_dt.timestamp()),
        "jumuah_timestamp": int(jumuah_dt.timestamp()),
    }
    return Response(data, status=status.HTTP_200_OK)
