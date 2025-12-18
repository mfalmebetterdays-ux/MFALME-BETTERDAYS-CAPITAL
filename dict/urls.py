# dict/urls.py
from django.contrib import admin
from django.urls import path
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Basic pages
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Auth
    path('login/', views.login_page, name='login_page'),
    path('login_user/', views.login_user, name='login_user'),
    path('register/', views.register_page, name='register_page'),
    path('create_account/', views.create_account, name='create_account'),
    path('logout/', views.logout_user, name='logout'),
    
    # Verification
    path('verify-account/', views.verify_account_page, name='verify_account_page'),
    path('verify-account/process/', views.verify_account_process, name='verify_account_process'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Other pages
    path('services/', views.services, name='services'),
    path('contact/', views.contact_page, name='contact'),
    path('about/', views.about, name='about'),
    path('partnership/', views.partnership, name='partnership'),
]