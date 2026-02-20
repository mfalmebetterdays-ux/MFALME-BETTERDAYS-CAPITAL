from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [
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