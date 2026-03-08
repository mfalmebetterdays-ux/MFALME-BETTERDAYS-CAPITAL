import boto3
import json
import uuid
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from .admin_views import is_admin_authenticated

# ==================== S3 DIRECT UPLOAD VIEWS ====================

@csrf_exempt
def get_s3_presigned_url(request):
    """Generate a presigned URL for direct browser-to-S3 upload"""
    
    # Check admin authentication
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        filetype = data.get('filetype')
        
        if not filename or not filetype:
            return JsonResponse({'error': 'filename and filetype required'}, status=400)
        
        # Generate unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_id = str(uuid.uuid4())
        key = f"videos/{unique_id}_{filename}"
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Generate presigned POST data
        presigned_post = s3.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Fields={
                'acl': 'public-read',
                'Content-Type': filetype
            },
            Conditions=[
                {'acl': 'public-read'},
                {'Content-Type': filetype},
                ["content-length-range", 1, 10737418240]  # 10GB max
            ],
            ExpiresIn=3600  # URL valid for 1 hour
        )
        
        # Return the presigned URL data
        return JsonResponse({
            'url': presigned_post['url'],
            'fields': presigned_post['fields'],
            'key': key,
            'file_url': f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        })
        
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
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
        
        if not filename:
            return JsonResponse({'error': 'filename required'}, status=400)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        key = f"videos/{unique_id}_{filename}"
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Initiate multipart upload
        response = s3.create_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            ContentType=filetype,
            ACL='public-read'
        )
        
        upload_id = response['UploadId']
        
        return JsonResponse({
            'upload_id': upload_id,
            'key': key,
            'bucket': settings.AWS_STORAGE_BUCKET_NAME
        })
        
    except Exception as e:
        print(f"Error initiating multipart upload: {e}")
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
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Complete multipart upload
        response = s3.complete_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        return JsonResponse({
            'success': True,
            'location': response['Location'],
            'key': key,
            'file_url': f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        })
        
    except Exception as e:
        print(f"Error completing multipart upload: {e}")
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
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Abort multipart upload
        s3.abort_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            UploadId=upload_id
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Error aborting multipart upload: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# Optional: For thumbnails and images
@csrf_exempt
def get_s3_presigned_url_image(request):
    """Generate presigned URL for image uploads (thumbnails, covers)"""
    
    if not is_admin_authenticated(request):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        filetype = data.get('filetype')
        folder = data.get('folder', 'thumbnails')
        
        if not filename or not filetype:
            return JsonResponse({'error': 'filename and filetype required'}, status=400)
        
        # Validate image types
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if filetype not in allowed_types:
            return JsonResponse({'error': 'Invalid image type'}, status=400)
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        key = f"{folder}/{unique_id}_{filename}"
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Generate presigned POST data (smaller size limit for images)
        presigned_post = s3.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Fields={
                'acl': 'public-read',
                'Content-Type': filetype
            },
            Conditions=[
                {'acl': 'public-read'},
                {'Content-Type': filetype},
                ["content-length-range", 1, 10485760]  # 10MB max for images
            ],
            ExpiresIn=3600
        )
        
        return JsonResponse({
            'url': presigned_post['url'],
            'fields': presigned_post['fields'],
            'key': key,
            'file_url': f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        })
        
    except Exception as e:
        print(f"Error generating presigned URL for image: {e}")
        return JsonResponse({'error': str(e)}, status=500)