#!/usr/bin/env python
"""
Database connection check for Railway deployment
Run this before starting the application
"""
import os
import sys
import time
import django
from django.db import connection, connections
from django.db.utils import OperationalError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

def check_db():
    """Check if database is ready with retries"""
    max_retries = 30
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            # Try to connect to database
            connection.ensure_connection()
            print(f"✅ Database connection successful on attempt {i+1}")
            return True
        except OperationalError as e:
            if i < max_retries - 1:
                print(f"⏳ Database not ready (attempt {i+1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts")
                return False
    
    return False

if __name__ == "__main__":
    if check_db():
        sys.exit(0)
    else:
        sys.exit(1)