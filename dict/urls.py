from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from myapp import views

# Health check function - defined here for reliability
def health_check(request):
    """
    Simple health check endpoint for Railway.
    Returns 200 OK if the app is running.
    """
    return HttpResponse("OK", status=200)

urlpatterns = [
    # HEALTH CHECK - MUST BE FIRST for Railway health checks
    path('health/', health_check, name='health_check'),
    path('', health_check, name='root_health'),  # Optional: root health check
    
    # NO DJANGO ADMIN HERE - JUST YOUR APP
    path('', include('myapp.urls')),
    
    # Error handlers
    path('404/', views.custom_404, name='404'),
    path('500/', views.custom_500, name='500'),
]

# Add media files support in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'myapp.views.custom_404'
handler500 = 'myapp.views.custom_500'