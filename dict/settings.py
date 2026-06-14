"""
Django settings for dict project - MFALME BETTERDAYS CAPITAL
"""

import os
import sys
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv 
import dj_database_url  # ← ADD THIS LINE - FIXES THE ERROR

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================
# LOAD ENVIRONMENT VARIABLES
# ================================================
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# ================================================
# ENVIRONMENT DETECTION
# ================================================
IS_RAILWAY = os.environ.get('RAILWAY', 'false').lower() == 'true' or 'RAILWAY_ENVIRONMENT' in os.environ
DEBUG = os.environ.get('DEBUG', 'True') == 'True'  # Changed to True by default

# ================================================
# SECRET KEY
# ================================================
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production'
    print("⚠️ WARNING: Using development SECRET_KEY")

# ================================================
# HTTPS CONFIGURATION - DISABLED FOR LOCAL DEV
# ================================================
# Simple: No HTTPS for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_PROXY_SSL_HEADER = None
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

print("🔓 HTTP mode - HTTPS disabled for local development")

# ================================================
# AWS S3 CONFIGURATION
# ================================================
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

if AWS_STORAGE_BUCKET_NAME and AWS_S3_REGION_NAME:
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
else:
    AWS_S3_CUSTOM_DOMAIN = None

AWS_CREDENTIALS_PRESENT = all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME])
USE_S3 = AWS_CREDENTIALS_PRESENT and not (DEBUG and not IS_RAILWAY)

if USE_S3:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_USE_SSL = True
    AWS_S3_VERIFY = True
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = 'public-read'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'
    os.makedirs(MEDIA_ROOT, exist_ok=True)

# ================================================
# HOSTS & SECURITY
# ================================================
ALLOWED_HOSTS = ['*']  # Allow all hosts for development

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://mfalmebetterdayscapital.com',
    'https://www.mfalmebetterdayscapital.com',
]

if IS_RAILWAY:
    ALLOWED_HOSTS.extend(['.railway.app', '.up.railway.app'])
    CSRF_TRUSTED_ORIGINS.extend(['https://*.railway.app', 'https://*.up.railway.app'])

# ================================================
# MIDDLEWARE
# ================================================
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ================================================
# APPLICATION DEFINITION
# ================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
    'whitenoise.runserver_nostatic',
    'storages',
]

ROOT_URLCONF = 'dict.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'template')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dict.wsgi.application'

# ================================================
# DATABASE CONFIGURATION
# ================================================
if IS_RAILWAY and os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    print("✅ Using PostgreSQL database (Production)")
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("✅ Using SQLite database (Local Development)")

# ================================================
# PASSWORD VALIDATION
# ================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ================================================
# INTERNATIONALIZATION
# ================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ================================================
# STATIC FILES
# ================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

# ================================================
# MEDIA FILES
# ================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
os.makedirs(MEDIA_ROOT, exist_ok=True)

# ================================================
# CUSTOM USER MODEL
# ================================================
AUTH_USER_MODEL = 'myapp.MfalmeUsers'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ================================================
# EMAIL CONFIGURATION
# ================================================
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
    ADMIN_EMAILS = ['mfalmebetterdays@gmail.com']
elif DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ADMIN_EMAILS = ['admin@example.com']
    print("📧 Using console email backend (development)")
else:
    ADMIN_EMAILS = []

# ================================================
# SESSION CONFIGURATION
# ================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_NAME = 'mfalme_session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True

# ================================================
# LOGIN/LOGOUT
# ================================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ================================================
# FILE UPLOAD
# ================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

# ================================================
# PAYSTACK
# ================================================
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
PAYSTACK_API_URL = 'https://api.paystack.co'

if PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY:
    print("✅ Paystack configured successfully")
else:
    print("⚠️ Paystack credentials not configured")

# ================================================
# USD TO KES
# ================================================
USD_TO_KES_RATE = int(os.environ.get('USD_TO_KES_RATE', 129))

# ================================================
# SITE SETTINGS
# ================================================
SITE_NAME = "MFALME BETTERDAYS CAPITAL"
SITE_URL = os.environ.get('SITE_URL', 'https://mfalmebetterdayscapital.com')
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '+254 706 286 667')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'mfalmebetterdays@gmail.com')

# ================================================
# VERIFICATION SETTINGS
# ================================================
VERIFICATION_CODE_EXPIRY_MINUTES = 30
VERIFICATION_CODE_LENGTH = 6
MAX_VERIFICATION_ATTEMPTS = 5

# ================================================
# LOGGING
# ================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '[{asctime}] {levelname} {module} {message}', 'style': '{'}},
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'myapp': {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'INFO'},
    },
}

# ================================================
# CREATE NECESSARY DIRECTORIES
# ================================================
for directory in ['staticfiles', 'media', 'logs']:
    os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)

# ================================================
# STARTUP VERIFICATION
# ================================================
print("\n" + "="*60)
print("🚀 MFALME BETTERDAYS CAPITAL - Configuration Loaded")
print("="*60)
print(f"📦 Environment: {'PRODUCTION' if not DEBUG else 'DEVELOPMENT'}")
print(f"🔒 HTTPS Mode: DISABLED (HTTP only)")
print(f"☁️  Storage: {'AWS S3' if USE_S3 else 'Local Filesystem'}")
print(f"📧 Email: {'✅ Configured' if EMAIL_HOST_USER else '⚠️ Not Configured'}")
print(f"💳 Paystack: {'✅ Configured' if PAYSTACK_PUBLIC_KEY else '⚠️ Not Configured'}")
print(f"💰 USD to KES: {USD_TO_KES_RATE}")
print(f"🚂 Railway: {'✅ Yes' if IS_RAILWAY else 'No'}")
print(f"🗄️  Database: {'PostgreSQL' if IS_RAILWAY and os.environ.get('DATABASE_URL') else 'SQLite'}")
print(f"📁 Static Root: {STATIC_ROOT}")
print(f"📁 Static Dirs: {STATICFILES_DIRS}")
print("="*60 + "\n")