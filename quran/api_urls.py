# quran/api_urls.py
from django.urls import path
from . import api_views

app_name = "quran_api"

urlpatterns = [
    # نص السورة
    path("surah/<int:number>", api_views.surah_detail, name="surah_detail"),

    # آية واحدة (اختياري)
    path(
        "surah/<int:number>/ayah/<int:ayah>",
        api_views.ayah_detail,
        name="ayah_detail",
    ),

    # البحث
    path("search", api_views.search, name="search"),

    # خريطة الصوت
    path(
        "surah/<int:number>/audio",
        api_views.surah_audio_map,
        name="surah_audio_map",
    ),

    # التفسير
    path("tafseer", api_views.tafseer_view, name="tafseer"),

    # أوقات الجمعة
    path("times/today", api_views.today_times_view, name="times_today"),
]
