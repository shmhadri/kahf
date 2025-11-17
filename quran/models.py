from django.db import models


class Surah(models.Model):
    """
    جدول السور: رقم واسم السورة.
    """
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "سورة"
        verbose_name_plural = "السور"

    def __str__(self) -> str:
        return f"{self.number} - {self.name}"


class Ayah(models.Model):
    """
    جدول الآيات: كل آية مرتبطة بسورة معيّنة.
    - text: النص الأصلي للآية.
    - normalized: نسخة من النص مهيّأة للبحث (بدون حركات مثلاً).
    """
    surah = models.ForeignKey(
        Surah,
        related_name="ayahs",
        on_delete=models.CASCADE,
    )
    number = models.PositiveIntegerField()
    text = models.TextField()
    normalized = models.TextField(
        db_index=True,
        blank=True,
        default="",
        help_text="نص مُطهَّر للبحث (بدون تشكيل/رموز).",
    )

    class Meta:
        unique_together = ("surah", "number")
        ordering = ["number"]

    def __str__(self) -> str:
        return f"{self.surah.name}:{self.number}"


class TafseerEntry(models.Model):
    """
    تفسير مختصر لآية معيّنة (يمكن التوسّع لاحقًا لمصادر متعددة ولغات أخرى).
    """
    surah = models.PositiveSmallIntegerField(help_text="رقم السورة (1-114)")
    ayah = models.PositiveSmallIntegerField(help_text="رقم الآية داخل السورة")
    lang = models.CharField(
        max_length=5,
        default="ar",
        help_text="رمز اللغة مثل ar أو en",
    )
    source = models.CharField(
        max_length=50,
        default="sadi",
        help_text="اسم مصدر التفسير (مثلاً: السعدي).",
    )
    text_short = models.TextField(help_text="نص التفسير المختصر للآية.")

    class Meta:
        unique_together = ("surah", "ayah", "lang", "source")
        indexes = [
            models.Index(fields=["surah", "ayah"]),
        ]
        verbose_name = "تفسير مختصر"
        verbose_name_plural = "تفاسير مختصرة"

    def __str__(self) -> str:
        return f"Tafseer S{self.surah} A{self.ayah} ({self.lang}/{self.source})"
