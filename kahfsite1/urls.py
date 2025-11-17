# kahfsite1/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from quran.views import Surah18View, KahfStoryView

urlpatterns = [
    # لوحة الإدارة
    path("admin/", admin.site.urls),

    # واجهة الـ API (السور، الآيات، البحث، الصوت، التفسير، أوقات الجمعة)
    path("api/", include("quran.api_urls")),

    # صفحة سورة الكهف (الصفحة الرئيسية للموقع)
    path("", Surah18View.as_view(), name="home"),

    # نفس صفحة سورة الكهف لكن برابط واضح
    path("surah/18/", Surah18View.as_view(), name="surah18_page"),

    # صفحة ملخص قصة أصحاب الكهف
    # تستخدم في القالب عبر: {% url 'kahf_story' %}
    path("kahf/story/", KahfStoryView.as_view(), name="kahf_story"),
]

# في وضع التطوير: تقديم الملفات الثابتة/الوسائط من Django مباشرة
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
