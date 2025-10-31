# quran/api_urls.py
from django.urls import path
from quran.api_views import (
    surah_detail,
    ayah_detail,
    search,
    surah_audio_map,
)

urlpatterns = [
    path("surah/<int:number>", surah_detail, name="surah_detail"),
    path("surah/<int:number>/ayah/<int:ayah>", ayah_detail, name="ayah_detail"),
    path("search", search, name="search"),
    path("surah/<int:number>/audio", surah_audio_map, name="surah_audio"),
]
