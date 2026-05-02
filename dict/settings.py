"""
Django settings for dict project - MFALME BETTERDAYS CAPITAL
Production-ready settings with AWS S3 for media files and automatic database failover
"""

import os
import sys
import time
import urllib.parse
from pathlib import Path
import dj_database_url
import ssl
from datetime import datetime, timedelta
from dotenv import load_dotenv 

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

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
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ================================================
# SECRET KEY - NO FALLBACK IN PRODUCTION!
# ================================================
SECRET_KEY = os.environ.get('SECRET_KEY')

# Handle missing SECRET_KEY safely
if not SECRET_KEY:
    is_local = 'runserver' in sys.argv or 'manage.py' in sys.argv
    if DEBUG or is_local:
        SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production'
        print("⚠️ WARNING: Using development SECRET_KEY - DO NOT USE IN PRODUCTION")
    else:
        print("❌ CRITICAL: SECRET_KEY environment variable not set in production!")
        raise ValueError("SECRET_KEY must be set in production environment")

# ================================================
# FORCE BOTH HTTP AND HTTPS - FIX THE REDIRECT LOOP
# ================================================
FORCE_HTTP_DEV = DEBUG and not IS_RAILWAY

if FORCE_HTTP_DEV:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_PROXY_SSL_HEADER = None
    SECURE_SSL_HOST = None
    SECURE_REDIRECT_EXEMPT = [r'^.*$']
    SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'
    
    print("🔓 HTTPS redirects DISABLED for local development")
    print("   Access your site at: http://127.0.0.1:8000")
else:
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

AWS_CREDENTIALS_PRESENT = all([
    AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY, 
    AWS_STORAGE_BUCKET_NAME, 
    AWS_S3_REGION_NAME
])

USE_S3 = AWS_CREDENTIALS_PRESENT and not (DEBUG and not IS_RAILWAY)

# ================================================
# STORAGE CONFIGURATION
# ================================================
if USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_USE_SSL = True
    AWS_S3_VERIFY = True
    AWS_S3_MAX_ATTEMPTS = 3
    AWS_S3_MULTIPART_THRESHOLD = 100 * 1024 * 1024
    AWS_S3_MULTIPART_CHUNKSIZE = 50 * 1024 * 1024
    AWS_QUERYSTRING_AUTH = False
    AWS_QUERYSTRING_EXPIRE = 86400
    AWS_DEFAULT_ACL = 'public-read'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'
    os.makedirs(MEDIA_ROOT, exist_ok=True)

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

if FORCE_HTTP_DEV:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '0.0.0.0'])

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

if FORCE_HTTP_DEV:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost',
        'http://127.0.0.1',
    ])

if railway_domain:
    if not railway_domain.startswith('https://'):
        railway_domain = f'https://{railway_domain}'
    CSRF_TRUSTED_ORIGINS.append(railway_domain)

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

if FORCE_HTTP_DEV:
    class GracefulHTTPMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response
        
        def __call__(self, request):
            if request.is_secure() and FORCE_HTTP_DEV:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"HTTPS request received but treating as HTTP: {request.path}")
                request._is_secure = False
            return self.get_response(request)
    
    MIDDLEWARE.insert(0, 'dict.settings.GracefulHTTPMiddleware')

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

if FORCE_HTTP_DEV:
    try:
        import sslserver
        INSTALLED_APPS.append('sslserver')
        print("🔐 django-sslserver available for HTTPS testing")
        print("   Run: python manage.py runsslserver to enable HTTPS")
    except ImportError:
        pass

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
PRIMARY_DATABASE_URL = os.environ.get('DATABASE_URL')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

if PRIMARY_DATABASE_URL:
    try:
        parsed_url = urllib.parse.urlparse(PRIMARY_DATABASE_URL)
        
        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_url.path[1:],
            'USER': parsed_url.username,
            'PASSWORD': parsed_url.password,
            'HOST': parsed_url.hostname,
            'PORT': parsed_url.port or '5432',
            'CONN_MAX_AGE': 180 if IS_RAILWAY else 60,
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'connect_timeout': 5,
                'sslmode': 'require' if IS_RAILWAY else 'prefer',
            }
        }
        
        import psycopg2
        try:
            conn = psycopg2.connect(
                dbname=db_config['NAME'],
                user=db_config['USER'],
                password=db_config['PASSWORD'],
                host=db_config['HOST'],
                port=db_config['PORT'],
                connect_timeout=3
            )
            conn.close()
            DATABASES['default'] = db_config
            print("✅ PostgreSQL database configured and connected")
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {e}")
            print("✅ Falling back to SQLite database")
    except Exception as e:
        print(f"⚠️ Error parsing DATABASE_URL: {e}")
        print("✅ Using SQLite database")

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
# STATIC FILES
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
# EMAIL CONFIGURATION - FIXED!
# ================================================
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
    SERVER_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
    
    # Only use working email addresses
    ADMIN_EMAILS = ['mfalmebetterdays@gmail.com']
    
    EMAIL_TIMEOUT = 30
    EMAIL_CONNECTION_TIMEOUT = 30
elif DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ADMIN_EMAILS = ['admin@example.com']
    print("📧 Using console email backend (development)")
else:
    print("⚠️ Email not configured - email functionality will fail!")
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
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
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

# ================================================
# SITE SETTINGS
# ================================================
SITE_NAME = "MFALME BETTERDAYS CAPITAL"
SITE_URL = os.environ.get('SITE_URL', 'https://mfalmebetterdayscapital.com')
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '+254 706 286 667')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'mfalmebetterdays@gmail.com')

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
SASAPAY_CLIENT_ID = os.environ.get('SASAPAY_CLIENT_ID')
SASAPAY_CLIENT_SECRET = os.environ.get('SASAPAY_CLIENT_SECRET')
SASAPAY_MERCHANT_CODE = os.environ.get('SASAPAY_MERCHANT_CODE', '600980')
SASAPAY_TEST_MODE = os.environ.get('SASAPAY_TEST_MODE', 'False') == 'True'

SASAPAY_NETWORK_CODES = {
    'SASAPAY': '0',
    'MPESA': '63902',
    'AIRTEL': '63903',
    'TKASH': '63907',
}

if SASAPAY_CLIENT_ID and SASAPAY_CLIENT_SECRET:
    SASAPAY_CONFIG = {
        'CLIENT_ID': SASAPAY_CLIENT_ID,
        'CLIENT_SECRET': SASAPAY_CLIENT_SECRET,
        'ENVIRONMENT': SASAPAY_ENVIRONMENT,
        'MERCHANT_CODE': SASAPAY_MERCHANT_CODE,
        'CALLBACK_URL': os.environ.get('SASAPAY_CALLBACK_URL', f'{SITE_URL}/sasapay/callback/'),
        'IPN_URL': os.environ.get('SASAPAY_IPN_URL', f'{SITE_URL}/sasapay/ipn/'),
        'NETWORK_CODES': SASAPAY_NETWORK_CODES,
    }

    if SASAPAY_ENVIRONMENT == 'sandbox':
        SASAPAY_BASE_URL = 'https://sandbox.sasapay.app'
    else:
        SASAPAY_BASE_URL = os.environ.get('SASAPAY_LIVE_URL', 'https://api.sasapay.app')

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
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')

# ================================================
# PESAPAL CONFIGURATION
# ================================================
PESAPAL_CONFIG = {
    'CONSUMER_KEY': os.environ.get('PESAPAL_CONSUMER_KEY'),
    'CONSUMER_SECRET': os.environ.get('PESAPAL_CONSUMER_SECRET'),
    'ENVIRONMENT': os.environ.get('PESAPAL_ENVIRONMENT', 'sandbox'),
    'CALLBACK_URL': os.environ.get('PESAPAL_CALLBACK_URL', f'{SITE_URL}/pesapal/callback/'),
    'IPN_URL': os.environ.get('PESAPAL_IPN_URL', f'{SITE_URL}/pesapal/ipn/'),
}

# ================================================
# RAILWAY OPTIMIZATIONS
# ================================================
if IS_RAILWAY:
    WHITENOISE_ROOT = STATIC_ROOT
    FILE_UPLOAD_TEMP_DIR = '/tmp'
    if 'default' in DATABASES:
        DATABASES['default']['CONN_MAX_AGE'] = 180

# ================================================
# DEVELOPMENT SETTINGS
# ================================================
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    ALLOWED_HOSTS = ['*']
    
    os.makedirs(os.path.join(BASE_DIR, 'staticfiles'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'media'), exist_ok=True)

# ================================================
# DATABASE INITIALIZATION
# ================================================

def initialize_database():
    if 'default' not in DATABASES:
        return
    
    if DATABASES['default'].get('ENGINE') == 'django.db.backends.postgresql':
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                from django.db import connections
                connections['default'].ensure_connection()
                print(f"✅ PostgreSQL connected (attempt {attempt + 1})")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ PostgreSQL connection attempt {attempt + 1} failed: {e}")
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ PostgreSQL failed after {max_retries} attempts: {e}")
                    print("✅ Falling back to SQLite")
                    DATABASES['default'] = {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': BASE_DIR / 'db.sqlite3',
                        'CONN_MAX_AGE': 60,
                    }

def get_active_database():
    if 'default' in DATABASES:
        if DATABASES['default'].get('ENGINE') == 'django.db.backends.postgresql':
            try:
                from django.db import connections
                connections['default'].ensure_connection()
                return "PostgreSQL (Primary)"
            except:
                return "SQLite (Failover)"
        else:
            return "SQLite"
    return "Unknown"

# ================================================
# DEVELOPER TIPS
# ================================================
if FORCE_HTTP_DEV:
    print("\n" + "💡"*30)
    print("DEVELOPMENT MODE - HTTPS Redirects DISABLED")
    print("💡"*30)
    print("✅ Access your site at: http://127.0.0.1:8000")
    print("✅ If browser still forces HTTPS, clear HSTS:")
    print("   - Chrome: chrome://net-internals/#hsts")
    print("   - Edge: edge://net-internals/#hsts")
    print("   - Delete 'localhost' from domain policies")
    print("✅ Or use incognito/private window")
    print("🔐 To test HTTPS locally: pip install django-sslserver")
    print("   Then run: python manage.py runsslserver")
    print("💡"*30 + "\n")

# Run database initialization
if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
    initialize_database()

# ================================================
# FINAL VERIFICATION
# ================================================
print("\n" + "="*60)
print("🚀 MFALME BETTERDAYS CAPITAL - Configuration Loaded")
print("="*60)
print(f"📦 Environment: {'PRODUCTION' if not DEBUG else 'DEVELOPMENT'}")
print(f"🔒 HTTPS Mode: {'FORCED' if not FORCE_HTTP_DEV else 'DISABLED (HTTP only)'}")
print(f"📍 Timezone: Africa/Nairobi")
print(f"☁️  Storage: {'AWS S3' if USE_S3 else 'Local Filesystem'}")
print(f"📧 Email: {'✅ Configured' if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD else '⚠️ Not Configured'}")
print(f"💰 SasaPay: {'✅ Configured' if SASAPAY_CLIENT_ID and SASAPAY_CLIENT_SECRET else '⚠️ Not Configured'}")
print(f"💳 Paystack: {'✅ Configured' if PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY else '⚠️ Not Configured'}")
print(f"💱 USD to KES Rate: {USD_TO_KES_RATE}")
print(f"🚂 Railway: {'✅ Yes' if IS_RAILWAY else 'No'}")
print(f"🗄️  Database: {get_active_database()}")
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
print("✅ Settings loaded successfully!")
print("="*60 + "\n")