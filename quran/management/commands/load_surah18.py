from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path
import json

from quran.models import Surah, Ayah
from quran.utils import normalize_arabic

class Command(BaseCommand):
    help = "Load Surah Al-Kahf (18) from surah18.json into DB."

    def handle(self, *args, **options):
        json_path = Path("surah18.json")
        if not json_path.exists():
            self.stderr.write(self.style.ERROR("❌ الملف surah18.json غير موجود بجانب manage.py"))
            return

        data = json.loads(json_path.read_text(encoding="utf-8"))
        if data.get("number") != 18:
            self.stderr.write(self.style.ERROR("❌ يجب أن يحتوي JSON على number=18"))
            return

        name = data.get("name") or "الكهف"
        ayahs = data.get("ayahs") or []
        if not ayahs:
            self.stderr.write(self.style.ERROR("❌ لا توجد آيات في JSON"))
            return

        with transaction.atomic():
            surah, _ = Surah.objects.get_or_create(number=18, defaults={"name": name})
            # لو موجودة نحذف آياتها لإعادة التحميل
            Ayah.objects.filter(surah=surah).delete()

            objs = []
            for item in ayahs:
                n = int(item["n"])
                t = item["text"]
                objs.append(Ayah(
                    surah=surah,
                    number=n,
                    text=t,
                    normalized=normalize_arabic(t),
                ))
            Ayah.objects.bulk_create(objs, batch_size=200)

        self.stdout.write(self.style.SUCCESS(f"✅ تم تحميل سورة الكهف ({len(ayahs)} آية)."))
