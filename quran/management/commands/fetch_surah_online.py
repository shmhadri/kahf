# quran/management/commands/fetch_surah_online.py
from django.core.management.base import BaseCommand
from django.db import transaction
import requests
from requests import RequestException

from quran.models import Surah, Ayah
from quran.utils import normalize_arabic

API_BASE = "https://api.alquran.cloud/v1"
TEXT_EDITION = "quran-uthmani"

class Command(BaseCommand):
    help = "Fetch a surah text online and store into DB (default: 18)."

    def add_arguments(self, parser):
        parser.add_argument("--number", type=int, default=18)
        parser.add_argument("--edition", type=str, default=TEXT_EDITION)

    def handle(self, *args, **opts):
        number = int(opts["number"])
        edition = (opts["edition"] or TEXT_EDITION).strip()
        url = f"{API_BASE}/surah/{number}/{edition}"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
        except RequestException as e:
            self.stderr.write(self.style.ERROR(f"HTTP error: {e}"))
            return
        payload = r.json()
        if payload.get("code") != 200 or "data" not in payload:
            self.stderr.write(self.style.ERROR("Unexpected API response"))
            return
        data = payload["data"]
        ayahs = data.get("ayahs") or []
        if not ayahs:
            self.stderr.write(self.style.ERROR("No ayahs returned"))
            return
        name = data.get("englishName") or data.get("name") or f"Surah {number}"
        with transaction.atomic():
            surah, _ = Surah.objects.get_or_create(number=number, defaults={"name": name})
            Ayah.objects.filter(surah=surah).delete()
            bulk = []
            for a in ayahs:
                n = int(a.get("numberInSurah"))
                text = a.get("text") or ""
                bulk.append(Ayah(surah=surah, number=n, text=text, normalized=normalize_arabic(text)))
            Ayah.objects.bulk_create(bulk, batch_size=200)
        self.stdout.write(self.style.SUCCESS(f"Loaded Surah {number}: {len(ayahs)} ayahs"))
