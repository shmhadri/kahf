from django.db import models

class Surah(models.Model):
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "سورة"
        verbose_name_plural = "السور"

    def __str__(self):
        return f"{self.number} - {self.name}"

class Ayah(models.Model):
    surah = models.ForeignKey(Surah, related_name="ayahs", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    text = models.TextField()
    normalized = models.TextField(db_index=True, blank=True, default="")

    class Meta:
        unique_together = ("surah", "number")
        ordering = ["number"]

    def __str__(self):
        return f"{self.surah.name}:{self.number}"
