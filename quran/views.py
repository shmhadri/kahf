# quran/views.py
from django.views.generic import TemplateView

class Surah18View(TemplateView):
    """عرض صفحة سورة الكهف HTML"""
    template_name = "surah18.html"
