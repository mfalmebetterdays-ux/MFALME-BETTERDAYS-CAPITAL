"""
WSGI config for dict project.
Production-ready WSGI configuration with error logging and WhiteNoise.
"""

import os
import sys
import traceback

# Print startup banner
print("=" * 60)
print("🚀 WSGI: Initializing MFALME BETTERDAYS CAPITAL")
print("=" * 60)

# Add the project directory to Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)
    print(f"📂 Added to Python path: {path}")

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
print(f"⚙️  Using settings module: {os.environ['DJANGO_SETTINGS_MODULE']}")

# Initialize Django application
try:
    print("🔄 Loading Django WSGI application...")
    from django.core.wsgi import get_wsgi_application
    django_application = get_wsgi_application()
    print("✅ Django WSGI application loaded successfully")
    
    # Try to initialize Django fully
    import django
    django.setup()
    print("✅ Django setup complete")
    
    # Test database connection (optional - comment out if causing issues)
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as db_error:
        print(f"⚠️ Database connection warning: {db_error}")
        print("⚠️ App will continue, but database features may fail")
    
except Exception as e:
    print(f"❌ CRITICAL ERROR loading Django: {e}")
    traceback.print_exc()
    print("=" * 60)
    print("💡 Application may not function correctly!")
    print("=" * 60)
    # Re-raise in production to prevent startup with broken Django
    if not os.environ.get('DEBUG') == 'True':
        raise
    django_application = None

# Wrap with WhiteNoise for static files
print("📁 Configuring WhiteNoise for static files...")
try:
    from whitenoise import WhiteNoise
    
    # Check if static directories exist
    static_root = os.path.join(path, 'staticfiles')
    static_dir = os.path.join(path, 'static')
    
    print(f"   Static root: {static_root}")
    print(f"   Static dir: {static_dir}")
    
    # Create WhiteNoise application
    application = WhiteNoise(django_application, root=static_root)
    
    # Add static files directory if it exists
    if os.path.exists(static_dir):
        application.add_files(static_dir, prefix='static/')
        print(f"   ✅ Added static directory: {static_dir}")
    else:
        print(f"   ⚠️ Static directory not found: {static_dir}")
    
    # Configure WhiteNoise
    application.max_age = 31536000  # 1 year cache
    print("✅ WhiteNoise configured successfully")
    
except Exception as e:
    print(f"❌ Error configuring WhiteNoise: {e}")
    traceback.print_exc()
    # Fall back to Django application without WhiteNoise
    application = django_application
    print("⚠️ Falling back to Django application without WhiteNoise")

print("=" * 60)
print("✅ WSGI fully initialized and ready to accept requests")
print("=" * 60)

# For debugging - print environment info (remove in production)
if os.environ.get('DEBUG') == 'True':
    print("\n🔧 Environment Variables (safe ones only):")
    safe_vars = ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_SERVICE_ID', 
                 'RAILWAY_PUBLIC_DOMAIN', 'DATABASE_URL']
    for var in safe_vars:
        if var in os.environ:
            print(f"   {var}: {os.environ[var][:50]}...")
    print("=" * 60)