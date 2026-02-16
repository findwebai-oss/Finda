# import os
# from pathlib import Path
# from dotenv import load_dotenv

# BASE_DIR = Path(__file__).resolve().parent.parent

# # Load .env only if exists (for local dev)
# env_file = BASE_DIR / ".env"
# if env_file.exists():
#     load_dotenv(env_file)

# # =====================
# # SECURITY
# # =====================
# SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# DEBUG = os.getenv("DEBUG", "False") == "True"

# ALLOWED_HOSTS = [
#     "finda.to",
#     "www.finda.to",
#     "finda-1cjt.onrender.com",
#     "localhost",
#     "127.0.0.1",
# ]

# USE_X_FORWARDED_HOST = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# CSRF_TRUSTED_ORIGINS = [
#     "https://finda.onrender.com",
# ]

# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# # =====================
# # APPLICATIONS
# # =====================
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',

#     'core',
#     'flights',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware', 
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'finda.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / "templates"],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'finda.wsgi.application'

# # =====================
# # DATABASE
# # =====================
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# # =====================
# # PASSWORD VALIDATION
# # =====================
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# # =====================
# # INTERNATIONALIZATION
# # =====================
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'Europe/Istanbul'
# USE_I18N = True
# USE_TZ = True

# # =====================
# # STATIC FILES
# # =====================
# STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# # Whitenoise sıkıştırma ve cache
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # =====================
# # API KEYS (ENV)
# # =====================
# def get_env(key: str) -> str:
#     """Env variable al, None olsa bile güvenli string dön."""
#     return (os.getenv(key) or "").strip()

# GROQ_API_KEY = get_env("GROQ_API_KEY")
# GEMINI_API_KEY = get_env("GEMINI_API_KEY")
# OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
# AMADEUS_API_KEY = get_env("AMADEUS_API_KEY")
# AMADEUS_API_SECRET = get_env("AMADEUS_API_SECRET")
# SERP_API_KEY = get_env("SERP_API_KEY")
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env only if exists (for local dev)
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

# =====================
# SECURITY
# =====================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")

DEBUG = os.getenv("DEBUG", "").lower() == "true"

ALLOWED_HOSTS = [
    "finda.to",
    "www.finda.to",
    "finda-1cjt.onrender.com",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://finda-1cjt.onrender.com",
    "https://finda.to",
    "https://www.finda.to",
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# =====================
# APPLICATIONS
# =====================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "core",
    "flights",
]

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

ROOT_URLCONF = "finda.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finda.wsgi.application"

# =====================
# DATABASE
# =====================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =====================
# PASSWORD VALIDATION
# =====================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================
# INTERNATIONALIZATION
# =====================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# =====================
# STATIC FILES
# =====================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================
# API KEYS (ENV)
# =====================

def get_env(key: str) -> str:
    return (os.getenv(key) or "").strip()

GROQ_API_KEY = get_env("GROQ_API_KEY")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
AMADEUS_API_KEY = get_env("AMADEUS_API_KEY")
AMADEUS_API_SECRET = get_env("AMADEUS_API_SECRET")
SERP_API_KEY = get_env("SERP_API_KEY")
