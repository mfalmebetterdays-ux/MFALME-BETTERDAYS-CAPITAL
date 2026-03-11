import boto3
import json
import uuid
import os
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from botocore.config import Config  # ← CRITICAL: Added missing import
from .admin_views import is_admin_authenticated

# ==================== S3 DIRECT UPLOAD VIEWS ====================

@csrf_exempt
def get_s3_presigned_url(request):
    """Generate presigned PUT URL for direct browser-to-S3 upload"""
    
    if not request.session.get('admin_authenticated'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        filetype = data.get('filetype')
        folder = data.get('folder', 'uploads')
        
        if not filename:
            return JsonResponse({'error': 'filename required'}, status=400)
        
        # Generate unique key with proper sanitization
        # Get extension safely
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
        else:
            ext = 'bin'
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        # Clean base name - remove special characters
        base_name = os.path.splitext(filename)[0]
        base_name = ''.join(c for c in base_name if c.isalnum() or c == ' ' or c == '-').strip()
        base_name = base_name.replace(' ', '_')[:50]
        
        # Construct S3 key
        key = f"{folder}/{timestamp}_{unique_id}_{base_name}.{ext}"
        
        print(f"🔑 Generating presigned URL for: {key}")
        print(f"   Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        print(f"   Region: {settings.AWS_S3_REGION_NAME}")
        
        # Create S3 client with proper config
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        )
        
        # Generate presigned PUT URL - NO ACL PARAMETER
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': key,
                'ContentType': filetype,
            },
            ExpiresIn=3600  # 1 hour for large files
        )
        
        # Generate public URL
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            public_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"
        else:
            public_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        
        print(f"✅ Presigned URL generated successfully")
        
        return JsonResponse({
            'success': True,
            'presigned_url': presigned_url,
            'key': key,
            'public_url': public_url,
            'method': 'put'
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
    except Exception as e:
        print(f"❌ Error generating presigned URL: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def initiate_multipart_upload(request):
    """For very large files > 100MB - use multipart upload"""
    
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        filetype = data.get('filetype')
        folder = data.get('folder', 'videos')
        
        if not filename:
            return JsonResponse({'error': 'filename required'}, status=400)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        # Clean base name
        base_name = os.path.splitext(filename)[0]
        base_name = ''.join(c for c in base_name if c.isalnum() or c in ' _-').strip()
        base_name = base_name.replace(' ', '_')[:50]
        ext = filename.split('.')[-1].lower() if '.' in filename else 'bin'
        
        key = f"{folder}/{timestamp}_{unique_id}_{base_name}.{ext}"
        
        print(f"🔑 Initiating multipart upload for: {key}")
        
        # Create S3 client with proper config
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        
        # Initiate multipart upload - NO ACL PARAMETER
        response = s3.create_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            ContentType=filetype,
        )
        
        upload_id = response['UploadId']
        
        # Build file URL
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"
        else:
            file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        
        print(f"✅ Multipart upload initiated with ID: {upload_id}")
        
        return JsonResponse({
            'success': True,
            'upload_id': upload_id,
            'key': key,
            'file_url': file_url,
            'bucket': settings.AWS_STORAGE_BUCKET_NAME
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
    except Exception as e:
        print(f"❌ Error initiating multipart upload: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def complete_multipart_upload(request):
    """Complete a multipart upload after all parts are uploaded"""
    
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        key = data.get('key')
        upload_id = data.get('upload_id')
        parts = data.get('parts', [])
        
        if not key or not upload_id:
            return JsonResponse({'error': 'key and upload_id required'}, status=400)
        
        print(f"🔑 Completing multipart upload: {key}, ID: {upload_id}")
        print(f"   Parts: {len(parts)}")
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        
        # Complete multipart upload
        response = s3.complete_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        # Build file URL
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"
        else:
            file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        
        print(f"✅ Multipart upload completed")
        
        return JsonResponse({
            'success': True,
            'location': response['Location'],
            'key': key,
            'file_url': file_url
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
    except Exception as e:
        print(f"❌ Error completing multipart upload: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def abort_multipart_upload(request):
    """Abort a multipart upload if cancelled"""
    
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        key = data.get('key')
        upload_id = data.get('upload_id')
        
        if not key or not upload_id:
            return JsonResponse({'error': 'key and upload_id required'}, status=400)
        
        print(f"🔴 Aborting multipart upload: {key}, ID: {upload_id}")
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        
        # Abort multipart upload
        s3.abort_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            UploadId=upload_id
        )
        
        print(f"✅ Multipart upload aborted")
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
    except Exception as e:
        print(f"❌ Error aborting multipart upload: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def test_s3_upload_direct(request):
    """Simple test to verify S3 upload works"""
    
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method == 'GET':
        # Build S3 info
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            sample_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/test-folder/sample.jpg"
        else:
            sample_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/test-folder/sample.jpg"
        
        return JsonResponse({
            'message': 'Send a POST request with a file to test S3 upload',
            'bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'region': settings.AWS_S3_REGION_NAME,
            'custom_domain': getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None),
            'sample_url': sample_url,
            'instructions': 'POST to this endpoint with a file field named "file"'
        })
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if not request.FILES.get('file'):
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    file = request.FILES['file']
    
    try:
        # Create unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        # Clean filename
        base_name = os.path.splitext(file.name)[0]
        base_name = ''.join(c for c in base_name if c.isalnum() or c in ' _-').strip()
        base_name = base_name.replace(' ', '_')[:50]
        ext = file.name.split('.')[-1].lower() if '.' in file.name else 'bin'
        
        key = f"test_uploads/{timestamp}_{unique_id}_{base_name}.{ext}"
        
        print(f"🔧 Testing S3 upload: {key}")
        print(f"   File size: {file.size} bytes")
        print(f"   Content type: {file.content_type}")
        
        # Upload directly to S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        
        s3.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            ExtraArgs={'ContentType': file.content_type}  # No ACL parameter
        )
        
        # Build file URL
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{key}"
        else:
            file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        
        print(f"✅ Test upload successful: {file_url}")
        
        return JsonResponse({
            'success': True,
            'key': key,
            'url': file_url,
            'message': 'File uploaded successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error in test upload: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)