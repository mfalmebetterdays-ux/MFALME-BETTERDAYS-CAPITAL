import django
import os
import sys

print(f"Python: {sys.version}")
print(f"Django: {django.__version__}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
