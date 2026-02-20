"""
Django settings for dict project - RAILWAY PRODUCTION FIXED
Production-ready settings for MFALME BETTERDAYS CAPITAL
"""

import os
import sys
from pathlib import Path
import dj_database_url
from datetime import timedelta

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== SECURITY SETTINGS =====
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'






# ==================== SASAPAY CONFIGURATION ====================
SASAPAY_CONFIG = {
    'CLIENT_ID': 'I4w49w1vftEVXTkMLwHQLr0DxdeXQYh34tYVFi5A',  # Your sandbox client ID
    'CLIENT_SECRET': 'AfnotJReSgwaICxM6meV9IPbciQyOzuRLPLFyOmjzRzdXGZcptp5rrurstk8FAi5G8hcXP33tPiikjwEOR3CSrLlkeJs3b8G3feUq8QHKf0sJtiiS65BL6QCPe6AxC1X',  # Your sandbox secret
    'ENVIRONMENT': 'live',  # 'sandbox' or 'production'
    'CALLBACK_URL': 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/callback/',
    'IPN_URL': 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/ipn/',
}

# SasaPay API Endpoints
if SASAPAY_CONFIG['ENVIRONMENT'] == 'sandbox':
    SASAPAY_API_URL = 'https://sandbox.sasapay.com/api/v1'
    SASAPAY_CHECKOUT_URL = 'https://sandbox.sasapay.com/checkout'
else:
    SASAPAY_API_URL = 'https://api.sasapay.com/api/v1'
    SASAPAY_CHECKOUT_URL = 'https://checkout.sasapay.com'


USD_TO_KES_RATE = 129  

# Hosts/Origins
ALLOWED_HOSTS = [
    'mfalmebetterdayscapital.com',
    'www.mfalmebetterdayscapital.com',
    '.railway.app',
    '.up.railway.app',
    'localhost',
    '127.0.0.1',
    '[::1]',
]

# Add your custom domain when ready
if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('RAILWAY_PUBLIC_DOMAIN'))

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://mfalmebetterdayscapital.com',
    'https://www.mfalmebetterdayscapital.com',
]

# Security settings for production - FIXED: Only apply when NOT in development runserver
if not DEBUG and 'runserver' not in sys.argv:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Additional production security
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'
else:
    # Development settings - NO HTTPS redirects
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    print("🔓 Running in HTTP mode (development)")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',  # Your custom app
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be after SecurityMiddleware
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

# ===== DATABASE CONFIGURATION =====
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Railway PostgreSQL configuration
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
            engine='django.db.backends.postgresql'
        )
    }
    
    # PostgreSQL optimization for Railway
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }
    print("✅ PostgreSQL database configured via DATABASE_URL")
else:
    # Local development SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("⚠️ Using SQLite for local development")

# Database pool settings for production
if DATABASE_URL and not DEBUG:
    DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ===== STATIC FILES CONFIGURATION =====
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise settings
WHITENOISE_MAX_AGE = 31536000  # 1 year cache
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_AUTOREFRESH = DEBUG  # Auto-refresh in debug mode

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CUSTOM USER MODEL =====
AUTH_USER_MODEL = 'myapp.MfalmeUsers'

# ===== EMAIL CONFIGURATION =====
# Gmail SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'mfalmebetterdays@gmail.com'
EMAIL_HOST_PASSWORD = 'bccpooxkwxdassxh'
DEFAULT_FROM_EMAIL = 'MFALME BETTERDAYS CAPITAL <mfalmebetterdays@gmail.com>'
SERVER_EMAIL = 'MFALME BETTERDAYS CAPITAL <mfalmebetterdays@gmail.com>'
ADMIN_EMAILS = ['mfalmebetterdays@gmail.com']

# Email timeouts
EMAIL_TIMEOUT = 30
EMAIL_CONNECTION_TIMEOUT = 30

# ===== PAYSTACK INTEGRATION =====
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_live_fc4f550a27a942bc0f6ce014c57b1834c4b6195d')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_live_197cf61799bc7493f737268952280f5da78cc7a4')

# ===== SESSION CONFIGURATION =====
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_NAME = 'mfalme_session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True  # CRITICAL: Ensures session is saved on every request

# ===== AUTHENTICATION BACKENDS =====
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default backend
]

# ===== LOGIN/LOGOUT URLS =====
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ===== MEDIA FILES =====
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# ===== CACHING =====
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-mfalme-cache',
    }
}

# ===== LOGGING CONFIGURATION =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'myapp': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Changed to DEBUG to see all our print statements
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# ===== CUSTOM SETTINGS =====
# Site settings
SITE_NAME = "MFALME BETTERDAYS CAPITAL"
SITE_URL = "https://mfalmebetterdayscapital.com"
SUPPORT_PHONE = "+254 706 286 667"
SUPPORT_EMAIL = "support@mfalmebetterdayscapital.com"

# Application-specific settings
MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt']

# Exchange rate API (fallback)
EXCHANGE_RATE_API = 'https://api.frankfurter.app/latest?from=USD&to=KES'
DEFAULT_EXCHANGE_RATE = 160.0

# Verification settings
VERIFICATION_CODE_EXPIRY_MINUTES = 30
VERIFICATION_CODE_LENGTH = 6
MAX_VERIFICATION_ATTEMPTS = 5

# ===== STARTUP CHECKS =====
def startup_checks():
    """Perform startup checks and log configuration"""
    startup_messages = []
    
    # Log configuration
    startup_messages.append("=" * 60)
    startup_messages.append("🚀 MFALME BETTERDAYS CAPITAL - Starting Up")
    startup_messages.append("=" * 60)
    
    # Environment
    startup_messages.append(f"📦 Environment: {'Production' if not DEBUG else 'Development'}")
    startup_messages.append(f"🔧 DEBUG: {DEBUG}")
    startup_messages.append(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    
    # HTTPS Mode
    https_mode = SECURE_SSL_REDIRECT
    startup_messages.append(f"🔒 HTTPS Redirects: {'ENABLED' if https_mode else 'DISABLED'}")
    
    # Database
    db_engine = DATABASES['default']['ENGINE'].split('.')[-1]
    startup_messages.append(f"🗄️  Database: {db_engine}")
    
    # Email
    startup_messages.append(f"📧 Email: {EMAIL_HOST_USER}")
    startup_messages.append(f"📧 SMTP: {EMAIL_HOST}:{EMAIL_PORT}")
    startup_messages.append(f"📧 TLS: {EMAIL_USE_TLS}")
    
    # Paystack
    if PAYSTACK_SECRET_KEY and PAYSTACK_PUBLIC_KEY:
        startup_messages.append("💳 Paystack: ✅ Configured")
    else:
        startup_messages.append("💳 Paystack: ⚠️ Keys missing")
    
    # Static files
    static_exists = os.path.exists(os.path.join(BASE_DIR, 'static'))
    startup_messages.append(f"📁 Static Files: {'✅ Found' if static_exists else '❌ Missing'}")
    
    # Custom User Model
    startup_messages.append(f"👤 Custom User Model: {AUTH_USER_MODEL}")
    
    # Session Settings
    startup_messages.append(f"🍪 Session Engine: {SESSION_ENGINE}")
    startup_messages.append(f"🍪 Session Save Every Request: {SESSION_SAVE_EVERY_REQUEST}")
    
    # Login URLs
    startup_messages.append(f"🔐 Login URL: {LOGIN_URL}")
    startup_messages.append(f"🔐 Login Redirect: {LOGIN_REDIRECT_URL}")
    
    startup_messages.append("=" * 60)
    
    # Print all startup messages
    for msg in startup_messages:
        print(msg)

# Run startup checks
if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
    startup_checks()

# ===== DEPLOYMENT SPECIFIC SETTINGS =====
# Railway-specific optimizations
if 'RAILWAY_ENVIRONMENT' in os.environ:
    # Ensure static files are collected
    WHITENOISE_ROOT = STATIC_ROOT
    
    # Optimize for Railway's ephemeral filesystem
    FILE_UPLOAD_TEMP_DIR = '/tmp'
    
    # Database connection pooling for Railway
    if DATABASE_URL:
        DATABASES['default']['CONN_MAX_AGE'] = 180
        DATABASES['default']['CONN_HEALTH_CHECKS'] = True

# Skip startup database checks for gunicorn
if 'gunicorn' in sys.argv:
    import django.db.utils
    try:
        from django.db import connection
        connection.ensure_connection()
        print("✅ Database connection verified")
    except django.db.utils.OperationalError as e:
        print(f"⚠️ Database connection failed: {e}")
        # Don't crash - allow app to start and retry later

# ===== DEVELOPMENT SETTINGS =====
if DEBUG:
    # Development-specific settings
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    
    # Allow all hosts for development
    ALLOWED_HOSTS = ['*']
    
    # Debug toolbar (optional)
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    except ImportError:
        pass
    
    # Show emails in console during development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("⚠️ DEBUG MODE: Emails will be printed to console, not sent")

# ===== FINAL VALIDATION =====
# Validate critical settings
if not SECRET_KEY or SECRET_KEY == 'django-insecure-change-this-in-production':
    print("⚠️ WARNING: Using default/insecure SECRET_KEY in production!")

if DEBUG and 'railway' in ''.join(ALLOWED_HOSTS).lower():
    print("⚠️ WARNING: DEBUG=True in production-like environment!")

# Ensure critical directories exist
for directory in ['static', 'media', 'logs']:
    dir_path = os.path.join(BASE_DIR, directory)
    os.makedirs(dir_path, exist_ok=True)

print("✅ Settings loaded successfully!")