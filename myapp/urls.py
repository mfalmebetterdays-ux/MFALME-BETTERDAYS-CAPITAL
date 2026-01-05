# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    
    # Authentication
    path('login/', views.login_page, name='login_page'),
    path('login-user/', views.login_user, name='login_user'),
    path('register/', views.register_page, name='register_page'),
    path('create-account/', views.create_account, name='create_account'),
    path('verify-account/', views.verify_account_page, name='verify_account_page'),
    path('verify-account-process/', views.verify_account_process, name='verify_account_process'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('logout/', views.logout_user, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Payment without login
    path('pay-without-login/', views.pay_without_login, name='pay_without_login'),
    path('payment/guest-verify/<str:reference>/', views.verify_guest_payment, name='verify_guest_payment'),
    
    # Regular payments
    path('payment/package/<str:package_type>/<int:amount>/', views.initiate_package_payment, name='initiate_package_payment'),
    path('payment/education/<str:program_type>/<str:duration>/', views.initiate_education_payment, name='initiate_education_payment'),
    path('payment/partnership/<str:tier>/', views.initiate_partnership_payment, name='initiate_partnership_payment'),
    path('payment/custom/', views.initiate_custom_payment, name='initiate_custom_payment'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment/history/', views.payment_history, name='payment_history'),
    
    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    
    # Webhooks
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Pages
    path('services/', views.services, name='services'),
    path('contact/', views.contact_page, name='contact'),
    path('about/', views.about, name='about'),
    path('partnership/', views.partnership, name='partnership'),
    path('education/', views.education, name='education'),
    path('booking/', views.booking, name='booking'),
    
    # Testing
    path('test-emails/', views.test_all_emails, name='test_emails'),
    path('test-smtp/', views.test_smtp_connection, name='test_smtp'),
    path('emergency-email-fix/', views.emergency_email_fix, name='emergency_email_fix'),
    
    # API endpoints
    path('api/check-email/', views.api_check_email, name='api_check_email'),
    path('api/user-stats/', views.api_get_user_stats, name='api_get_user_stats'),

    # Dashboard API endpoints
    path('api/videos/', views.api_get_videos, name='api_get_videos'),
    path('api/unlock-video/', views.api_unlock_video, name='api_unlock_video'),
    path('api/send-support/', views.api_send_support, name='api_send_support'),
    path('api/update-settings/', views.api_update_settings, name='api_update_settings'),
    path('api/activities/', views.api_get_activities, name='api_get_activities'),
    
    # Payment for video
    path('payment/video/<int:video_id>/', views.payment_video, name='payment_video'),

    # Dashboard payment urls
    path('initiate-video-payment/', views.initiate_video_payment, name='initiate_video_payment'),
    path('initiate-course-payment/', views.initiate_course_payment, name='initiate_course_payment'),
    path('initiate-mentorship-payment/', views.initiate_mentorship_payment, name='initiate_mentorship_payment'),
    
    # Dashboard API endpoints
    path('api/videos/', views.api_get_videos, name='api_get_videos'),
    path('api/mentorship-programs/', views.api_get_mentorship_programs, name='api_get_mentorship_programs'),
    
    # Payment verification (use your existing verify_payment view)
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
]