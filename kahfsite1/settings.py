"""
Django settings for kahfsite1 project.

- Arabic + Asia/Riyadh
- Static via WhiteNoise (CompressedManifest)
- Prod security for Render
- Optional Postgres via DATABASE_URL (falls back to SQLite)
- DRF minimal + browsable in DEBUG
"""

from pathlib import Path
import os

# ==============================
# Paths
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# Core / Modes
# ==============================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"


def _split_csv_env(name: str, default: str = "") -> list[str]:
    """Split comma-separated env var into list (trims spaces)."""
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


# تُقرأ من المتغيرات، مع افتراض onrender محميًا افتراضيًا
ALLOWED_HOSTS = _split_csv_env(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,.onrender.com",
)

# يجب أن تحتوي على البروتوكول (Django 4/5):
CSRF_TRUSTED_ORIGINS = _split_csv_env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000,https://*.onrender.com",
)

# ==============================
# Apps
# ==============================
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",

    # Local apps
    "quran",
]

# ==============================
# Middleware
# ==============================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise: يقدم static من داخل Django في الإنتاج
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # بعد Session وقبل Common
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kahfsite1.urls"

# ==============================
# Templates
# ==============================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "kahfsite1.wsgi.application"
ASGI_APPLICATION = "kahfsite1.asgi.application"

# ==============================
# Database
# - SQLite محليًا
# - إن وُجد DATABASE_URL (Postgres مثلاً) نستخدمه تلقائيًا
# ==============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

_db_url = os.getenv("DATABASE_URL")
if _db_url:
    # دعم اختياري لـ dj-database-url؛ لو غير مثبت سيستمر على SQLite
    try:
        import dj_database_url  # type: ignore

        DATABASES["default"] = dj_database_url.parse(_db_url, conn_max_age=600, ssl_require=True)
    except Exception:
        # لا تفشل الإعدادات إن لم تتوفر المكتبة – تبقى SQLite
        pass

# ==============================
# Password Validation
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================
# i18n / tz
# ==============================
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

LANGUAGES = [("ar", "Arabic"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]

# ==============================
# Static / Media
# ==============================
STATIC_URL = "/static/"
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise storage (ضغط + نسخ بأسماء مُعلَّمة)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT)},
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# DRF
# ==============================
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        ["rest_framework.renderers.JSONRenderer"]
        if not DEBUG
        else ["rest_framework.renderers.JSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer"]
    ),
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# ==============================
# Caching (خفيف داخل الذاكرة)
# ==============================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "kahfsite1-localmem",
        "TIMEOUT": 60 * 5,
    }
}

# ==============================
# Security (prod)
# ==============================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS (يوصى به عند ثبات HTTPS بالكامل)
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "31536000"))  # سنة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================
# Logging
# - في التطوير: Console + ملف django.log
# - في الإنتاج (Render): Console فقط (أفضل للخدمات المُدارة)
# ==============================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
        "simple": {"format": "[{levelname}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        **(
            {
                "file": {
                    "class": "logging.FileHandler",
                    "filename": str(BASE_DIR / "django.log"),
                    "formatter": "verbose",
                }
            }
            if DEBUG
            else {}
        ),
    },
    "loggers": {
        "django": {"handlers": ["console"] + (["file"] if DEBUG else []), "level": "INFO"},
        "quran": {"handlers": ["console"] + (["file"] if DEBUG else []), "level": "INFO", "propagate": False},
    },
}
