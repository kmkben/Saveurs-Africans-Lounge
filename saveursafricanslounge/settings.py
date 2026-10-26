
import os
from pathlib import Path

import dj_database_url
import environ
from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")

IS_PRODUCTION = not DEBUG

SITE_NAME = "Saveurs Africans Lounge"
SITE_URL = env("SITE_URL", default="http://127.0.0.1:8000")

DEVELOPER_NAME = "KMK-IoTech"
DEVELOPER_URL = "https://kmk-iotech.com"


# ============================================================
# HOSTS AND SECURITY
# ============================================================

# ALLOWED_HOSTS = env.list(
#     "ALLOWED_HOSTS",
#     default=["localhost", "127.0.0.1"],
# )

ALLOWED_HOSTS=[
    '127.0.0.1',
    'saveursafricanslounge.com',
    'www.saveursafricanslounge.com',
    'saveurs-africans-lounge-production.up.railway.app',
    'https://saveurs-africans-lounge-production.up.railway.app/'
    
]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

if IS_PRODUCTION:
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be configured.")

    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "Wildcard ALLOWED_HOSTS is not allowed in production."
        )

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "crispy_forms",
    "crispy_bootstrap5",
    "fontawesomefree",

    "core",
    "menu",
    "reservations",
    "events",
    "gallery",
    "contact",
    "daily_specials",
    "orders",
    "payments",
    "notifications",
    "management",
    "promotions",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URLS, TEMPLATES AND WSGI
# ============================================================

ROOT_URLCONF = "saveursafricanslounge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "core.context_processors.site_settings",
                "orders.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "saveursafricanslounge.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = env("DATABASE_URL", default="")

if IS_PRODUCTION and not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL is required in production. "
        "Configure the Railway PostgreSQL service."
    )

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"

USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# STATICFILES_DIRS = [BASE_DIR / "core" / "static"]

STATICFILES_DIRS = [
    BASE_DIR / "static",
] if (BASE_DIR / "static").is_dir() else []


# ============================================================
# MEDIA STORAGE — LOCAL / AMAZON S3
# ============================================================

USE_S3 = env.bool("USE_S3", default=False)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if IS_PRODUCTION and not USE_S3:
    raise ImproperlyConfigured(
        "USE_S3 must be enabled for production media storage."
    )

if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID").strip()
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY").strip()
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME").strip()
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="eu-west-3").strip()

    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "location": "media",
            "default_acl": None,
            "file_overwrite": False,
            "querystring_auth": True,
            "querystring_expire": 3600,
            "object_parameters": {
                "CacheControl": "private, max-age=3600",
            },
        },
    }

    # MEDIA_URL = (
    #     f"https://{AWS_STORAGE_BUCKET_NAME}.s3."
    #     f"{AWS_S3_REGION_NAME}.amazonaws.com/media/"
    # )


# ============================================================
# EMAIL — DJANGO SMTP
# ============================================================

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

EMAIL_HOST = env("EMAIL_HOST", default="smtp-relay.brevo.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)

EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = False

EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

EMAIL_TIMEOUT = 20

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="Saveurs Africans Lounge <contact@saveursafricanslounge.com>",
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMIN_EMAIL = env(
    "ADMIN_EMAIL",
    default="contact@saveursafricanslounge.com",
)


# ============================================================
# BREVO — TRANSACTIONAL NOTIFICATIONS
# ============================================================

BREVO_API_KEY = env("BREVO_API_KEY", default="")

BREVO_EMAIL_ENABLED = env.bool(
    "BREVO_EMAIL_ENABLED",
    default=False,
)

BREVO_SENDER_NAME = env(
    "BREVO_SENDER_NAME",
    default="Saveurs Africans Lounge",
)

BREVO_SENDER_EMAIL = env(
    "BREVO_SENDER_EMAIL",
    default="contact@saveursafricanslounge.com",
)

OWNER_NOTIFICATION_EMAIL = env(
    "OWNER_NOTIFICATION_EMAIL",
    default="contact@saveursafricanslounge.com",
)

OWNER_NOTIFICATION_PHONE = env(
    "OWNER_NOTIFICATION_PHONE",
    default="",
)

BREVO_SMS_ENABLED = env.bool(
    "BREVO_SMS_ENABLED",
    default=False,
)

BREVO_SMS_SENDER = env(
    "BREVO_SMS_SENDER",
    default="SaveursAL",
)


# ============================================================
# STRIPE — PAYMENTS
# ============================================================

STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

STRIPE_LIVE_MODE = env.bool(
    "STRIPE_LIVE_MODE",
    default=False,
)

if STRIPE_LIVE_MODE:
    if not STRIPE_PUBLIC_KEY.startswith("pk_live_"):
        raise ImproperlyConfigured(
            "STRIPE_LIVE_MODE=True requires a live publishable key."
        )

    if not STRIPE_SECRET_KEY.startswith("sk_live_"):
        raise ImproperlyConfigured(
            "STRIPE_LIVE_MODE=True requires a live secret key."
        )
else:
    if STRIPE_PUBLIC_KEY and not STRIPE_PUBLIC_KEY.startswith("pk_test_"):
        raise ImproperlyConfigured(
            "STRIPE_LIVE_MODE=False requires a test publishable key."
        )

    if STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith("sk_test_"):
        raise ImproperlyConfigured(
            "STRIPE_LIVE_MODE=False requires a test secret key."
        )


# ============================================================
# CRISPY FORMS
# ============================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# LOGGING — RAILWAY
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}