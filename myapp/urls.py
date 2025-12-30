# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main Pages
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication URLs
    path('login/', views.login_page, name='login_page'),
    path('login-user/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout'),
    
    # Registration URLs
    path('register/', views.register_page, name='register_page'),
    path('create-account/', views.create_account, name='create_account'),
    
    # Email Verification URLs
    path('verify-account/', views.verify_account_page, name='verify_account_page'),
    path('verify-account/process/', views.verify_account_process, name='verify_account_process'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Other Pages
    path('services/', views.services, name='services'),
    path('contact/', views.contact_page, name='contact'),
    path('about/', views.about, name='about'),
    path('partnership/', views.partnership, name='partnership'),
    path('education/', views.education, name='education'),
    
    # Payment URLs - FIXED
    path('payment/package/<str:package_type>/<int:amount>/', views.initiate_package_payment, name='initiate_package_payment'),
    path('payment/education/<str:program_type>/<str:duration>/', views.initiate_education_payment, name='initiate_education_payment'),
    path('payment/partnership/<str:tier>/', views.initiate_partnership_payment, name='initiate_partnership_payment'),
    path('payment/custom/', views.initiate_custom_payment, name='initiate_custom_payment'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment/history/', views.payment_history, name='payment_history'),
    
    # Paystack webhook
    path('payment/webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Booking/Contact Form
    path('booking/', views.booking, name='booking'),
    
    # Testing URLs
    path('test-emails/', views.test_email_system, name='test_email_system'),
    path('test-smtp/', views.test_smtp_connection, name='test_smtp'),
]