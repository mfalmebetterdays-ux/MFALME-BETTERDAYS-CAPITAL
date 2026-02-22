from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Simple health check - ALWAYS returns 200
def health_check(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    # Health check - MUST be first
    path('health/', health_check, name='health_check'),
    
    # Include your app's URLs
    path('', include('myapp.urls')),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)