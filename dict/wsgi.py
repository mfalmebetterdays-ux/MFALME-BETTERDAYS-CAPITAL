"""
WSGI config for dict project - PRODUCTION OPTIMIZED
"""

import os
import sys

# Minimal startup - only essential logs
print(f"🚀 WSGI: Starting MFALME BETTERDAYS CAPITAL")

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')

# Initialize Django application
try:
    from django.core.wsgi import get_wsgi_application
    from whitenoise import WhiteNoise
    
    # Get Django application
    django_app = get_wsgi_application()
    
    # Configure WhiteNoise for static files
    static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
    application = WhiteNoise(django_app, root=static_root)
    application.max_age = 31536000  # 1 year cache
    
    print("✅ WSGI ready")
    
except Exception as e:
    print(f"❌ WSGI ERROR: {e}")
    raise

# No debug info, no database checks, no fancy prints