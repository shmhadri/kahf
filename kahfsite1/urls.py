# kahfsite1/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API للسورة والآيات
    path("api/", include("quran.api_urls")),

    # صفحة العرض HTML
    path("", TemplateView.as_view(template_name="surah18.html"), name="home"),
]
