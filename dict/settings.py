"""
Django settings for dict project - RAILWAY PRODUCTION FIXED
Production-ready settings for MFALME BETTERDAYS CAPITAL
"""

import os
import sys
from pathlib import Path
import dj_database_url
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== DEBUG SETTING - MUST BE DEFINED FIRST =====
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ===== SECURITY SETTINGS =====
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# Handle missing SECRET_KEY for both local and production
if not SECRET_KEY:
    # Check if we're running locally (manage.py runserver)
    import sys
    is_local = 'runserver' in sys.argv or 'manage.py' in sys.argv
    
    if DEBUG or is_local:
        print("⚠️ WARNING: Using fallback SECRET_KEY for local development")
        SECRET_KEY = 'django-insecure-dev-key-do-not-use-in-production-7x9p2m4k8j3h5g1f'
    else:
        print("❌ CRITICAL: SECRET_KEY environment variable not set in production!")
        # In production, we should fail if no SECRET_KEY
        raise ValueError("SECRET_KEY must be set in production environment")

# Print mode
if DEBUG:
    print("🔧 Running in DEBUG mode")
else:
    print("🚀 Running in PRODUCTION mode")

# ===== SENSITIVE DATA - MUST BE ENVIRONMENT VARIABLES =====
# Email Configuration - MOVED TO ENVIRONMENT VARIABLES
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'mfalmebetterdays@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # MUST be set in Railway
if not EMAIL_HOST_PASSWORD and not DEBUG:
    print("❌ CRITICAL: EMAIL_HOST_PASSWORD environment variable not set!")

# ===== SASA PAY CONFIGURATION =====
# For testing, use sandbox. For production, change to 'live'
SASAPAY_ENVIRONMENT = os.environ.get('SASAPAY_ENVIRONMENT', 'sandbox')  # Default to sandbox for testing

SASAPAY_CONFIG = {
    'CLIENT_ID': os.environ.get('SASAPAY_CLIENT_ID', 'I4w49w1vftEVXTkMLwHQLr0DxdeXQYh34tYVFi5A'),
    'CLIENT_SECRET': os.environ.get('SASAPAY_CLIENT_SECRET', 'AfnotJReSgwaICxM6meV9IPbciQyOzuRLPLFyOmjzRzdXGZcptp5rrurstk8FAi5G8hcXP33tPiikjwEOR3CSrLlkeJs3b8G3feUq8QHKf0sJtiiS65BL6QCPe6AxC1X'),
    'ENVIRONMENT': SASAPAY_ENVIRONMENT,
    'CALLBACK_URL': os.environ.get('SASAPAY_CALLBACK_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/callback/'),
    'IPN_URL': os.environ.get('SASAPAY_IPN_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/sasapay/ipn/'),
}

# SasaPay API Endpoints - Using correct endpoints
if SASAPAY_ENVIRONMENT == 'sandbox':
    SASAPAY_API_URL = 'https://sandbox.sasapay.com/api/v1'
    SASAPAY_CHECKOUT_URL = 'https://sandbox.sasapay.com/checkout'
    SASAPAY_AUTH_URL = 'https://sandbox.sasapay.com/api/v1/oauth/token'
else:
    SASAPAY_API_URL = 'https://api.sasapay.com/api/v1'
    SASAPAY_CHECKOUT_URL = 'https://checkout.sasapay.com'
    SASAPAY_AUTH_URL = 'https://api.sasapay.com/api/v1/oauth/token'

USD_TO_KES_RATE = int(os.environ.get('USD_TO_KES_RATE', 129))

# ===== PAYSTACK CONFIGURATION =====
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')

# ===== PESAPAL CONFIGURATION =====
PESAPAL_CONFIG = {
    'CONSUMER_KEY': os.environ.get('PESAPAL_CONSUMER_KEY', ''),
    'CONSUMER_SECRET': os.environ.get('PESAPAL_CONSUMER_SECRET', ''),
    'ENVIRONMENT': os.environ.get('PESAPAL_ENVIRONMENT', 'sandbox'),
    'CALLBACK_URL': os.environ.get('PESAPAL_CALLBACK_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/pesapal/callback/'),
    'IPN_URL': os.environ.get('PESAPAL_IPN_URL', 'https://mfalme-betterdays-capital-production.up.railway.app/pesapal/ipn/'),
}

# ===== HOSTS/ORIGINS =====
ALLOWED_HOSTS = [
    'mfalmebetterdayscapital.com',
    'www.mfalmebetterdayscapital.com',
    '.railway.app',
    '.up.railway.app',
    'localhost',
    '127.0.0.1',
    '[::1]',
]

# Add Railway public domain if available
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
    # Also add without https:// if present
    if railway_domain.startswith('https://'):
        ALLOWED_HOSTS.append(railway_domain.replace('https://', ''))

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://mfalmebetterdayscapital.com',
    'https://www.mfalmebetterdayscapital.com',
]

# Add current domain to CSRF trusted origins
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

# ===== DATABASE CONFIGURATION - POSTGRESQL DIRECT CONNECTION =====
# NEW DATABASE URL - UPDATED
DATABASE_URL = "postgresql://postgres:LJzpCEAuJalpOHrSxpTrsWkFjkztJhHj@mainline.proxy.rlwy.net:49307/railway"

# Parse the database URL
db_config = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)

# Configure database with proper SSL settings
DATABASES = {
    'default': {
        **db_config,
        'OPTIONS': {
            'sslmode': 'require',  # Railway requires SSL
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,  # Keep connections alive
        'CONN_HEALTH_CHECKS': True,  # Check connection health
    }
}

print("✅ PostgreSQL database configured with direct connection")
print(f"📊 Database Host: mainline.proxy.rlwy.net:49307")
print(f"📊 Database Name: railway")
print(f"📊 Database User: postgres")

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
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

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
DEFAULT_FROM_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
SERVER_EMAIL = f'MFALME BETTERDAYS CAPITAL <{EMAIL_HOST_USER}>'
ADMIN_EMAILS = [EMAIL_HOST_USER]

# Email timeouts
EMAIL_TIMEOUT = 30
EMAIL_CONNECTION_TIMEOUT = 30

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
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
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
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
}

# Create logs directory if it doesn't exist
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# ===== CUSTOM SETTINGS =====
# Site settings
SITE_NAME = "MFALME BETTERDAYS CAPITAL"
SITE_URL = os.environ.get('SITE_URL', 'https://mfalmebetterdayscapital.com')
SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE', '+254 706 286 667')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@mfalmebetterdayscapital.com')

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

# ===== HEALTH CHECK CONFIGURATION =====
HEALTH_CHECK_PATHS = ['/', '/health/', '/healthcheck/']

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
    startup_messages.append(f"🗄️  Database: PostgreSQL (configured directly)")
    startup_messages.append(f"   Host: mainline.proxy.rlwy.net:49307")
    startup_messages.append(f"   Database: railway")
    startup_messages.append(f"   User: postgres")
    
    # Test database connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        startup_messages.append("   ✅ Connection test: SUCCESS")
    except Exception as e:
        startup_messages.append(f"   ❌ Connection test: FAILED - {e}")
    
    # Email
    if EMAIL_HOST_PASSWORD:
        startup_messages.append(f"📧 Email: ✅ Configured ({EMAIL_HOST_USER})")
    else:
        startup_messages.append(f"📧 Email: ⚠️ Password missing - emails will fail")
    
    # SasaPay
    sasapay_status = "✅ Configured" if SASAPAY_CONFIG['CLIENT_ID'] and SASAPAY_CONFIG['CLIENT_SECRET'] else "⚠️ Keys missing"
    startup_messages.append(f"💳 SasaPay: {sasapay_status} ({SASAPAY_ENVIRONMENT})")
    startup_messages.append(f"   Auth URL: {SASAPAY_AUTH_URL}")
    
    # Paystack
    paystack_status = "✅ Configured" if PAYSTACK_PUBLIC_KEY else "⚠️ Keys missing"
    startup_messages.append(f"💳 Paystack: {paystack_status}")
    
    # Static files
    static_exists = os.path.exists(os.path.join(BASE_DIR, 'static'))
    startup_messages.append(f"📁 Static Files: {'✅ Found' if static_exists else 'ℹ️ Not used'}")
    
    # Custom User Model
    startup_messages.append(f"👤 Custom User Model: {AUTH_USER_MODEL}")
    
    # Session Settings
    startup_messages.append(f"🍪 Session Engine: {SESSION_ENGINE}")
    
    startup_messages.append("=" * 60)
    
    # Print all startup messages
    for msg in startup_messages:
        print(msg)

# ===== DEPLOYMENT SPECIFIC SETTINGS =====
# Railway-specific optimizations
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'):
    # Ensure static files are collected
    WHITENOISE_ROOT = STATIC_ROOT
    
    # Optimize for Railway's ephemeral filesystem
    FILE_UPLOAD_TEMP_DIR = '/tmp'
    
    # Database connection pooling for Railway
    DATABASES['default']['CONN_MAX_AGE'] = 180
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
        
    print("🚂 Railway environment detected - optimizations applied")

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
    if DEBUG:
        print("⚠️ WARNING: Using fallback SECRET_KEY in development")
    else:
        print("⚠️ CRITICAL WARNING: Using default/insecure SECRET_KEY in production!")

if not EMAIL_HOST_PASSWORD and not DEBUG:
    print("⚠️ CRITICAL WARNING: EMAIL_HOST_PASSWORD not set - email features will fail!")

if not SASAPAY_CONFIG['CLIENT_ID'] or not SASAPAY_CONFIG['CLIENT_SECRET']:
    print("⚠️ WARNING: SasaPay credentials not fully configured!")

if DEBUG and 'railway' in str(ALLOWED_HOSTS).lower():
    print("⚠️ WARNING: DEBUG=True in production-like environment!")

# Ensure critical directories exist
for directory in ['staticfiles', 'media', 'logs']:
    dir_path = os.path.join(BASE_DIR, directory)
    os.makedirs(dir_path, exist_ok=True)

# Run startup checks if this is a web process
if 'gunicorn' in sys.argv or 'runserver' in sys.argv:
    startup_checks()

print("✅ Settings loaded successfully!")