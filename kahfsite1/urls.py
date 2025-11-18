# kahfsite1/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from quran.views import Surah18View, KahfStoryView


urlpatterns = [
    # لوحة الإدارة
    path("admin/", admin.site.urls),

    # واجهة الـ API (السور، الآيات، البحث، الصوت، التفسير، أوقات الجمعة)
    path("api/", include("quran.api_urls")),

    # الصفحة الرئيسية: سورة الكهف
    path("", Surah18View.as_view(), name="home"),

    # رابط إضافي واضح لسورة الكهف
    path("surah/18/", Surah18View.as_view(), name="surah18_page"),

    # صفحة قصة أصحاب الكهف (ملخص)
    path("kahf/story/", KahfStoryView.as_view(), name="kahf_story"),

    # ملف robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain",
        ),
        name="robots_txt",
    ),

    # ملف sitemap.xml
    path(
        "sitemap.xml",
        TemplateView.as_view(
            template_name="sitemap.xml",
            content_type="application/xml",
        ),
        name="sitemap_xml",
    ),

    # ملف التحقق من جوجل: https://kahf-4.onrender.com/googlea532a5ae726057b6.html
    path(
        "googlea532a5ae726057b6.html",
        TemplateView.as_view(
            template_name="googlea532a5ae726057b6.html",
            content_type="text/html",
        ),
        name="google_verify_a532",
    ),
]


# عرض ملفات static/media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
