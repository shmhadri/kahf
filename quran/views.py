# quran/views.py
from django.views.generic import TemplateView


class Surah18View(TemplateView):
    """
    صفحة سورة الكهف (الصفحة الرئيسية)
    - تعتمد على القالب: templates/surah18.html
    """
    template_name = "surah18.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # عنوان الصفحة والميتا
        context["page_title"] = "سورة الكهف"
        context["meta_description"] = "قراءة سورة الكهف مع صوت، بحث، تفسير مختصر، وتذكير بفضائل يوم الجمعة."
        return context


class KahfStoryView(TemplateView):
    """
    صفحة ملخّص قصة أصحاب الكهف
    - تعتمد على القالب: templates/kahf_story.html
    - يتم ربطها في urls.py بالاسم 'kahf_story'
    """
    template_name = "kahf_story.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "قصة أصحاب الكهف"
        context["meta_description"] = "ملخص بسيط لقصة أصحاب الكهف كما وردت في القرآن الكريم."
        return context
