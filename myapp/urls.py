# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main Pages
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication URLs - Using views you likely have
    path('login/', views.login_page, name='login_page'),  # Changed from 'login'
    path('login_user/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout'),
    
    # Registration - check if you have these or use alternatives
    path('register/', views.register_page, name='register_page'),  # Changed from 'register'
    path('create-account/', views.create_account, name='create_account'),
    
    # Email Verification URLs
    path('verify-account/', views.verify_account_page, name='verify_account_page'),
    path('verify-account/process/', views.verify_account_process, name='verify_account_process'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    
]