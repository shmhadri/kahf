from rest_framework import serializers
from quran.models import Surah, Ayah

class AyahSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ayah
        fields = ("number", "text")

class SurahSerializer(serializers.ModelSerializer):
    ayahs = AyahSerializer(many=True)

    class Meta:
        model = Surah
        fields = ("number", "name", "ayahs")
