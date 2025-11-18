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

    # صفحة قصة أصحاب الكهف
    path("kahf/story/", KahfStoryView.as_view(), name="kahf_story"),

    # ملف robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain"
        ),
        name="robots_txt",
    ),

    # ملف sitemap.xml (يتم إنشاؤه يدويًا في templates)
    path(
        "sitemap.xml",
        TemplateView.as_view(
            template_name="sitemap.xml",
            content_type="application/xml"
        ),
        name="sitemap_xml",
    ),
]


# عرض ملفات static/media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
