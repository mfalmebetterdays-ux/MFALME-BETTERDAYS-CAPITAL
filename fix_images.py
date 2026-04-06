import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

from django.conf import settings
from myapp.models import Course, TrainingVideo, PDF

S3_BASE = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/'

for model, field in [(Course, 'thumbnail'), (TrainingVideo, 'thumbnail'), (PDF, 'cover_image')]:
    for obj in model.objects.all():
        file_field = getattr(obj, field)
        if file_field and file_field.name and not file_field.name.startswith('http'):
            old_path = file_field.name
            new_path = S3_BASE + old_path
            setattr(obj, field, new_path)
            obj.save(update_fields=[field])
            print(f"✅ Fixed {model.__name__} {obj.id}: {old_path}")

print("🎉 All images fixed!")