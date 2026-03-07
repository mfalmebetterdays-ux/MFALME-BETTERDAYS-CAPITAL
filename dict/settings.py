"""
Django settings for dict project - MFALME BETTERDAYS CAPITAL
Production-ready settings with AWS S3 for media files
"""

import os
import sys
from pathlib import Path
import dj_database_url
import ssl
from datetime import datetime, timedelta
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================
# ENVIRONMENT DETECTION
# ================================================
IS_RAILWAY = os.environ.get('RAILWAY', 'false').lower() == 'true' or 'RAILWAY_ENVIRONMENT' in os.environ
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

print("\n" + "="*60)
print("🚀 MFALME BETTERDAYS CAPITAL - Starting Up")
print("="*60)
print(f"📦 Environment: {'Production' if not DEBUG else 'Development'}")
print(f"🔧 DEBUG: {DEBUG}")
print(f"🚂 Railway: {'Yes' if IS_RAILWAY else 'No'}")

# ================================================
# SECRET KEY
# ================================================
SECRET_KEY = os.environ.get('SECRET_KEY')

# Handle missing SECRET_KEY
if not SECRET_KEY:
    is_local = 'runserver' in sys.argv or 'manage.py' in sys.argv
    if DEBUG or is_local:
        print("⚠️ WARNING: Using fallback SECRET_KEY for local development")
        SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production-7x9p2m4k8j3h5g1f'
    else:
        print("❌ CRITICAL: SECRET_KEY environment variable not set in production!")
        raise ValueError("SECRET_KEY must be set in production environment")

# ================================================
# AWS S3 CONFIGURATION - EXACT SAME PATTERN AS LUMENDEO.TV
# ================================================

# AWS Credentials
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'AKIA3EQ3LS2YGTKNMLH7')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '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')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'aws-filez')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-north-1')

# CRITICAL: This tells Django to use S3 for file storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Make files publicly accessible
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # Cache for 24 hours
}

# Performance optimizations
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_USE_SSL = True
AWS_S3_VERIFY = True

# Reduce AWS SDK retries for faster failure detection
AWS_S3_MAX_ATTEMPTS = 3

# Multipart upload settings for large files
AWS_S3_MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB - use multipart for larger files
AWS_S3_MULTIPART_CHUNKSIZE = 50 * 1024 * 1024   # 50MB chunks for parallel upload

# Disable query string auth for public URLs (faster access)
AWS_QUERYSTRING_AUTH = False
AWS_QUERYSTRING_EXPIRE = 86400  # 24 hours

# Set DEFAULT_ACL based on bucket configuration
# If your bucket supports ACLs, use 'public-read'
# If your bucket doesn't support ACLs, set to None and use bucket policy
AWS_DEFAULT_ACL = 'public-read'  # Change to None if bucket doesn't support ACLs

# Direct S3 URL (no CloudFront)
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

# Media URL - use direct S3 URL
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# ================================================
# LOCAL MEDIA FALLBACK (for development)
# ================================================
if DEBUG and not IS_RAILWAY:
    # For local development, use local storage
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    
    # Create media directory
    try:
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        print(f"📁 Local media directory: {MEDIA_ROOT}")
    except:
        pass

print("\n" + "="*60)
print("☁️  AWS S3 CONFIGURATION")
print("="*60)
print(f"📦 Bucket: {AWS_STORAGE_BUCKET_NAME}")
print(f"📍 Region: {AWS_S3_REGION_NAME}")
print(f"🔑 Access Key: {'✅ Set' if AWS_ACCESS_KEY_ID else '❌ MISSING'}")
print(f"🔑 Secret Key: {'✅ Set' if AWS_SECRET_ACCESS_KEY else '❌ MISSING'}")
print(f"📡 Storage Backend: {DEFAULT_FILE_STORAGE}")
print(f"📡 Media URL: {MEDIA_URL}")
print(f"🔓 Public Access: {'✅ Enabled' if AWS_DEFAULT_ACL == 'public-read' else '⚠️ Using bucket policy'}")
print(f"⚡ Multipart threshold: 100MB")
print("="*60 + "\n")

# ================================================
# HOSTS & SECURITY
# ================================================
ALLOWED_HOSTS = [
    'mfalmebetterdayscapital.com',
    'www.mfalmebetterdayscapital.com',
    '.railway.app',
    '.up.railway.app',
    'localhost',
    '127.0.0.1',
    '[::1]',
]

railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
    if railway_domain.startswith('https://'):
        ALLOWED_HOSTS.append(railway_domain.replace('https://', ''))

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://mfalmebetterdayscapital.com',
    'https://www.mfalmebetterdayscapital.com',
]

if railway_domain:
    if not railway_domain.startswith('https://'):
        railway_domain = f'https://{railway_domain}'
    CSRF_TRUSTED_ORIGINS.append(railway_domain)

# Security settings for production
if not DEBUG and 'runserver' not in sys.argv:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    print("🔓 Running in HTTP mode (development)")

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
    'storages',  # Required for S3
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dict.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'template'),
        ],
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
DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:LJzpCEAuJalpOHrSxpTrsWkFjkztJhHj@mainline.proxy.rlwy.net:49307/railway")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
    # Add SSL options
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
        'connect_timeout': 10,
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'CONN_MAX_AGE': 60,
        }
    }

# ================================================
# PASSWORD VALIDATION
# ================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ================================================
# INTERNATIONALIZATION
# ================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ================================================
# STATIC FILES (WhiteNoise)
# ================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_AUTOREFRESH = DEBUG

# ================================================
# CUSTOM USER MODEL
# ================================================
AUTH_USER_MODEL = 'myapp.MfalmeUsers'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ================================================
# EMAIL CONFIGURATION
# ================================================
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'mfalmebetterdays@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'bccpooxkwxdassxh')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
SERVER_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
ADMIN_EMAILS = [EMAIL_HOST_USER, 'support@mfalmebetterdayscapital.com']
EMAIL_TIMEOUT = 30
EMAIL_CONNECTION_TIMEOUT = 30

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
# AUTHENTICATION
# ================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ================================================
# FILE UPLOAD SETTINGS
# ================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# ================================================
# CACHING
# ================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-mfalme-cache',
    }
}

if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    print("✅ Redis cache configured")

# ================================================
# LOGGING
# ================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'myapp': {'handlers': ['console', 'file'], 'level': 'DEBUG' if DEBUG else 'INFO'},
        'storages': {'handlers': ['console'], 'level': 'INFO'},
    },
    'root': {'handlers': ['console', 'file'], 'level': 'DEBUG' if DEBUG else 'INFO'},
}

log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# ================================================
# SITE SETTINGS
# ================================================
SITE_NAME = "MFALME BETTERDAYS CAPITAL"
SITE_URL = os.environ.get('SITE_URL', 'https://mfalmebetterdayscapital.com')
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '+254 706 286 667')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@mfalmebetterdayscapital.com')

MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']

EXCHANGE_RATE_API = 'https://api.frankfurter.app/latest?from=USD&to=KES'
DEFAULT_EXCHANGE_RATE = 160.0

VERIFICATION_CODE_EXPIRY_MINUTES = 30
VERIFICATION_CODE_LENGTH = 6
MAX_VERIFICATION_ATTEMPTS = 5

HEALTH_CHECK_PATHS = ['/', '/health/', '/healthcheck/']

# ================================================
# SASAPAY CONFIGURATION
# ================================================
SASAPAY_ENVIRONMENT = os.environ.get('SASAPAY_ENVIRONMENT', 'sandbox' if DEBUG else 'live')

SASAPAY_NETWORK_CODES = {
    'SASAPAY': '0',
    'MPESA': '63902',
    'AIRTEL': '63903',
    'TKASH': '63907',
}

SASAPAY_CONFIG = {
    'CLIENT_ID': os.environ.get('SASAPAY_CLIENT_ID', 'I4w49w1vftEVXTkMLwHQLr0DxdeXQYh34tYVFi5A'),
    'CLIENT_SECRET': os.environ.get('SASAPAY_CLIENT_SECRET', 'AfnotJReSgwaICxM6meV9IPbciQyOzuRLPLFyOmjzRzdXGZcptp5rrurstk8FAi5G8hcXP33tPiikjwEOR3CSrLlkeJs3b8G3feUq8QHKf0sJtiiS65BL6QCPe6AxC1X'),
    'ENVIRONMENT': SASAPAY_ENVIRONMENT,
    'MERCHANT_CODE': os.environ.get('SASAPAY_MERCHANT_CODE', '600980'),
    'CALLBACK_URL': os.environ.get('SASAPAY_CALLBACK_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/callback/'),
    'IPN_URL': os.environ.get('SASAPAY_IPN_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/ipn/'),
    'NETWORK_CODES': SASAPAY_NETWORK_CODES,
}

# SasaPay API Endpoints
if SASAPAY_ENVIRONMENT == 'sandbox':
    SASAPAY_BASE_URL = 'https://sandbox.sasapay.app'
    print("🔧 SasaPay: Using SANDBOX environment")
else:
    SASAPAY_BASE_URL = os.environ.get('SASAPAY_LIVE_URL', 'https://api.sasapay.app')
    print("💰 SasaPay: Using LIVE environment")

SASAPAY_API_URL = f'{SASAPAY_BASE_URL}/api/v1'
SASAPAY_AUTH_URL = f'{SASAPAY_BASE_URL}/api/v1/auth/token/'
SASAPAY_PAYMENTS_URL = f'{SASAPAY_BASE_URL}/api/v1/payments'
SASAPAY_REQUEST_PAYMENT_URL = f'{SASAPAY_PAYMENTS_URL}/request-payment/'
SASAPAY_PROCESS_PAYMENT_URL = f'{SASAPAY_PAYMENTS_URL}/process-payment/'
SASAPAY_CHECKOUT_URL = f'{SASAPAY_BASE_URL}/checkout'

SASAPAY_CONFIG.update({
    'BASE_URL': SASAPAY_BASE_URL,
    'API_URL': SASAPAY_API_URL,
    'AUTH_URL': SASAPAY_AUTH_URL,
    'PAYMENTS_URL': SASAPAY_PAYMENTS_URL,
    'REQUEST_PAYMENT_URL': SASAPAY_REQUEST_PAYMENT_URL,
    'PROCESS_PAYMENT_URL': SASAPAY_PROCESS_PAYMENT_URL,
    'CHECKOUT_URL': SASAPAY_CHECKOUT_URL,
})

USD_TO_KES_RATE = int(os.environ.get('USD_TO_KES_RATE', 129))

# ================================================
# PAYSTACK CONFIGURATION
# ================================================
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')

# ================================================
# PESAPAL CONFIGURATION
# ================================================
PESAPAL_CONFIG = {
    'CONSUMER_KEY': os.environ.get('PESAPAL_CONSUMER_KEY', ''),
    'CONSUMER_SECRET': os.environ.get('PESAPAL_CONSUMER_SECRET', ''),
    'ENVIRONMENT': os.environ.get('PESAPAL_ENVIRONMENT', 'sandbox'),
    'CALLBACK_URL': os.environ.get('PESAPAL_CALLBACK_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/pesapal/callback/'),
    'IPN_URL': os.environ.get('PESAPAL_IPN_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/pesapal/ipn/'),
}

# ================================================
# RAILWAY OPTIMIZATIONS
# ================================================
if IS_RAILWAY:
    WHITENOISE_ROOT = STATIC_ROOT
    FILE_UPLOAD_TEMP_DIR = '/tmp'
    if 'default' in DATABASES:
        DATABASES['default']['CONN_MAX_AGE'] = 180
    print("🚂 Railway optimizations applied")

# ================================================
# DEVELOPMENT SETTINGS
# ================================================
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    ALLOWED_HOSTS = ['*']
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("⚠️ DEBUG MODE: Emails printed to console")

# ================================================
# CRITICAL FIX: FORCE STORAGE BACKEND TO USE S3
# ================================================
print("\n" + "="*60)
print("🔧 APPLYING STORAGE BACKEND FIX")
print("="*60)

# Force reload the storage module to ensure S3 is used
if 'django.core.files.storage' in sys.modules:
    del sys.modules['django.core.files.storage']
    print("✅ Cleared cached storage module")

# Force S3 storage
try:
    from storages.backends.s3boto3 import S3Boto3Storage
    
    # Create instance with settings
    s3_storage = S3Boto3Storage()
    
    # Monkey patch the default_storage at module level
    import django.core.files.storage
    django.core.files.storage.default_storage = s3_storage
    
    # Also update the local reference
    from django.core.files.storage import default_storage
    default_storage = s3_storage
    
    print(f"✅ Successfully set storage to: {default_storage.__class__.__name__}")
    if hasattr(default_storage, 'bucket_name'):
        print(f"📦 Bucket: {default_storage.bucket_name}")
    
except Exception as e:
    print(f"❌ Failed to set S3 storage: {e}")
    import traceback
    traceback.print_exc()

print("="*60 + "\n")

# ================================================
# FINAL STORAGE VERIFICATION
# ================================================
print("📊 FINAL STORAGE CONFIGURATION:")
print(f"   DEFAULT_FILE_STORAGE setting: {DEFAULT_FILE_STORAGE}")

# Re-import to get the current state
from django.core.files.storage import default_storage as final_storage
print(f"   Actual storage class: {final_storage.__class__.__name__}")
print(f"   Actual storage module: {final_storage.__class__.__module__}")
if hasattr(final_storage, 'bucket_name'):
    print(f"   Bucket: {final_storage.bucket_name}")
print("="*60 + "\n")

# ================================================
# ENSURE DIRECTORIES EXIST
# ================================================
for directory in ['staticfiles', 'logs']:
    dir_path = os.path.join(BASE_DIR, directory)
    os.makedirs(dir_path, exist_ok=True)

# ================================================
# STARTUP COMPLETE
# ================================================
print("✅ Settings loaded successfully with AWS S3 integration!")
print("="*60 + "\n")