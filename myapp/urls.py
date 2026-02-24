from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views
from . import admin_views  # <-- ADD THIS LINE (it was missing)
from .views import (
    api_mark_lesson_complete,
    api_course_progress,
    api_course_next_lesson,
    api_course_reset_progress,
    pesapal_initiate_payment,
    pesapal_callback,
    pesapal_ipn,
    payment_pending,
    
)

urlpatterns = [
    # ==================== PUBLIC SITE PAGES ====================
    
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('payment/', views.payment, name='payment'),
    path('accounts/', views.accounts, name='accounts'),
    path('partnerships/', views.partnerships, name='partnerships'),
    path('education/', views.education, name='education'),
    path('mentoring/', views.mentoring, name='mentoring'),
    path('community/', views.community, name='community'),
    path('seminars/', views.seminars, name='seminars'),
    path('faqs/', views.faqs, name='faqs'),
    path('booking/', views.booking, name='booking'),
    path('test-sasapay/', views.test_sasapay_connection, name='test_sasapay'),
    
    # ==================== USER AUTHENTICATION ====================
    path('login/', views.login_page, name='login_page'),
    path('login-user/', views.login_user, name='login_user'),
    path('register/', views.register_user, name='register_user'),
    path('create-account/', views.register_user, name='create_account'),
    path('logout/', views.logout_user, name='logout'),
    
    # Email Verification
    path('verify-email/', views.verify_account_page, name='verify_account'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # ==================== USER DASHBOARD ====================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('change-password/', views.change_password, name='change_password'),
    
    # User Content
    path('my-videos/', views.my_videos, name='my_videos'),
    path('my-pdfs/', views.my_pdfs, name='my_pdfs'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('transactions/', views.transaction_history, name='transaction_history'),

    #=============ADMIN DATA==========================
    path('admin/api/users/export/', views.export_users, name='export_users'),
    path('admin/api/orders/export/', views.export_orders, name='export_orders'),
    path('admin/api/courses/export/', views.export_courses, name='export_courses'),
    path('admin/api/videos/export/', views.export_videos, name='export_videos'),
    path('admin/api/pdfs/export/', views.export_pdfs, name='export_pdfs'),
    path('admin/api/blogs/export/', views.export_blogs, name='export_blogs'),
    path('admin/api/packages/export/', views.export_packages, name='export_packages'),
    path('admin/api/partnerships/export/', views.export_partnerships, name='export_partnerships'),
    path('admin/api/reports/revenue/export/', views.export_revenue_report, name='export_revenue_report'),
    path('api/user/community/join/', views.api_community_join, name='api_community_join'),

    
    # ==================== CONTENT VIEWING ====================
    # Video viewing
    path('watch/<int:video_id>/', views.watch_video, name='watch_video'),
    
    # PDF viewing (NEW - view in browser instead of download)
    path('pdf/<int:pdf_id>/view/', views.view_pdf, name='view_pdf'),
    
    # Deprecated download endpoint - redirects to view
    path('pdf/<int:pdf_id>/download/', views.download_pdf, name='download_pdf'),
    
    # Course viewing
    path('course/<int:course_id>/', views.view_course, name='view_course'),
    path('course/<int:course_id>/complete/<str:lesson_type>/<int:lesson_id>/', 
         views.mark_lesson_complete, name='mark_lesson_complete'),
      path('api/initialize-payment/', views.initialize_package_payment, name='initialize_payment'),
       path('api/create-order/', views.api_create_order, name='api_create_order'),
    path('api/initialize-payment/', views.initialize_package_payment, name='initialize_payment'),
    path('api/create-order/', views.api_create_order, name='api_create_order'),
    path('payment/success/<str:reference>/', views.payment_success, name='payment_success'),
    path('sasapay/status/<str:reference>/', views.sasapay_status, name='sasapay_status'),
    path('education/pay/', views.education_payment, name='education_payment'),
    
    # ==================== SUPPORT TICKETS ====================
    path('support/tickets/', views.support_tickets, name='support_tickets'),
    path('support/tickets/create/', views.create_ticket, name='create_ticket'),
    path('support/tickets/<int:ticket_id>/', views.view_ticket, name='view_ticket'),
    path('support/tickets/<int:ticket_id>/close/', views.close_ticket, name='close_ticket'),
    
    # ==================== PAYMENT ROUTES ====================
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('payment/success/<str:reference>/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
    
    # Payment without login (guest)
    path('pay-without-login/', views.pay_without_login, name='pay_without_login'),
    path('payment/guest-verify/<str:reference>/', views.verify_guest_payment, name='verify_guest_payment'),
    
    # Package Payments
    path('payment/package/<str:package_type>/<int:amount>/', 
         views.initiate_package_payment, name='initiate_package_payment'),
    path('payment/education/<str:program_type>/<str:duration>/', 
         views.initiate_education_payment, name='initiate_education_payment'),
    path('payment/partnership/<str:tier>/', 
         views.initiate_partnership_payment, name='initiate_partnership_payment'),
    path('payment/custom/', views.initiate_custom_payment, name='initiate_custom_payment'),
    path('payment/video/<int:video_id>/', views.payment_video, name='payment_video'),
    path('initiate-video-payment/', views.initiate_video_payment, name='initiate_video_payment'),
    path('initiate-course-payment/', views.initiate_course_payment, name='initiate_course_payment'),
    path('initiate-mentorship-payment/', views.initiate_mentorship_payment, name='initiate_mentorship_payment'),
    
    # ==================== USER API ENDPOINTS ====================
    path('api/check-email/', views.api_check_email, name='api_check_email'),
    path('api/check-username/', views.api_check_username, name='api_check_username'),
    path('api/user/profile/', views.api_user_profile, name='api_user_profile'),
    path('api/user/stats/', views.api_user_stats, name='api_user_stats'),
    path('api/user/activities/', views.api_user_activities, name='api_user_activities'),
    path('api/user/notifications/', views.api_user_notifications, name='api_user_notifications'),
    path('api/notifications/<int:notification_id>/read/', 
         views.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/read-all/', 
         views.api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    
    # ==================== DASHBOARD API ENDPOINTS ====================
    path('api/user/courses/', views.api_user_courses, name='api_user_courses'),
    path('api/user/videos/', views.api_user_videos, name='api_user_videos'),
    path('api/user/pdfs/', views.api_user_pdfs, name='api_user_pdfs'),
    path('api/user/courses/enroll/', views.api_course_enroll, name='api_course_enroll'),
    path('api/user/watchlist/', views.api_watchlist, name='api_watchlist'),
    path('api/user/watchlist/count/', views.api_watchlist_count, name='api_watchlist_count'),
    path('api/user/watchlist/check/', views.api_watchlist_check, name='api_watchlist_check'),
    path('api/user/watchlist/add/', views.api_watchlist_add, name='api_watchlist_add'),
    path('api/user/watchlist/remove/', views.api_watchlist_remove, name='api_watchlist_remove'),
    path('api/user/communities/', views.api_user_communities, name='api_user_communities'),
    path('api/user/community/join/', views.api_community_join, name='api_community_join'),
    path('api/user/institute/eligibility/', views.api_institute_eligibility, name='api_institute_eligibility'),
    path('api/user/institute/apply/', views.api_institute_apply, name='api_institute_apply'),
    path('api/user/profile/update/', views.api_profile_update, name='api_profile_update'),
    path('api/user/password/change/', views.api_password_change, name='api_password_change'),
    path('api/user/orders/', views.api_user_orders, name='api_user_orders'),
    path('api/user/orders/create/', views.api_create_order, name='api_create_order'),
    path('api/user/tickets/', views.api_user_tickets, name='api_user_tickets'),
    path('api/user/tickets/create/', views.api_create_ticket, name='api_create_ticket'),
    path('api/user/tickets/<int:ticket_id>/', views.api_ticket_detail, name='api_ticket_detail'),
    path('api/user/tickets/<int:ticket_id>/reply/', views.api_ticket_reply, name='api_ticket_reply'),
    
    # ==================== PDF API ENDPOINTS (UPDATED) ====================
    # NEW: PDF viewing API endpoint (returns view URL) - THIS REPLACES THE DOWNLOAD ENDPOINT
    path('api/user/pdfs/<int:pdf_id>/view/', views.api_pdf_view, name='api_pdf_view'),
    
    # REMOVED: The download endpoint that was causing the error
    # The old line 'path('api/user/pdfs/<int:pdf_id>/download/', views.api_download_pdf, ...)' has been deleted
    
    # ==================== CONTENT API ENDPOINTS ====================
    path('api/user/packages/', views.api_get_packages, name='api_get_packages'),
    path('api/unlock-video/', views.api_unlock_video, name='api_unlock_video'),
    path('api/send-support/', views.api_send_support, name='api_send_support'),
    path('api/update-settings/', views.api_update_settings, name='api_update_settings'),
    
    # ==================== PUBLIC API ENDPOINTS ====================
    path('api/public/videos/', views.api_public_videos, name='api_public_videos'),
    path('api/public/pdfs/', views.api_public_pdfs, name='api_public_pdfs'),
    path('api/public/blogs/', views.api_public_blogs, name='api_public_blogs'),
    path('api/public/testimonials/', views.api_public_testimonials, name='api_public_testimonials'),
    path('api/public/faqs/', views.api_public_faqs, name='api_public_faqs'),
    path('api/public/courses/', views.api_public_courses, name='api_public_courses'),
    path('api/public/community/tiers/', views.api_public_community_tiers, name='api_public_community_tiers'),
    path('api/blogs/<int:blog_id>/', views.api_blog_detail, name='api_blog_detail'),
    
    # ==================== FORM SUBMISSIONS ====================
    path('contact/submit/', views.contact_form_submit, name='contact_submit'),
    path('apply-partnership/', views.submit_partnership_application, name='submit_partnership_application'),
    
    # ==================== ADMIN AUTHENTICATION ====================
    path('admin/login/', admin_views.admin_login_view, name='admin_login'),
    path('admin/logout/', admin_views.admin_logout_view, name='admin_logout'),
    
    # ==================== MAIN ADMIN DASHBOARD ====================
    path('admin/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_alt'),
    path('admin/debug-courses-api/', admin_views.debug_courses_api, name='debug_courses_api'),
    path('admin/test-course-simple/', admin_views.test_course_simple, name='test_course_simple'),
    
    # ==================== ADMIN API - DASHBOARD ====================
    path('admin/api/dashboard-stats/', admin_views.admin_api_dashboard_stats, 
         name='admin_api_dashboard_stats'),
    path('admin/api/activities/', admin_views.admin_api_activities, 
         name='admin_api_activities'),
    
    # ==================== ADMIN API - USER MANAGEMENT ====================
    path('admin/api/users/', admin_views.admin_api_users, name='admin_api_users'),
    path('admin/api/users/<int:user_id>/', admin_views.admin_api_user_detail, 
         name='admin_api_user_detail'),
    path('admin/api/users/create/', admin_views.admin_api_user_create, 
         name='admin_api_user_create'),
    path('admin/api/users/<int:user_id>/update/', admin_views.admin_api_user_update, 
         name='admin_api_user_update'),
    path('admin/api/users/<int:user_id>/delete/', admin_views.admin_api_user_delete, 
         name='admin_api_user_delete'),
    path('admin/api/users/<int:user_id>/activate/', admin_views.admin_api_user_activate, 
         name='admin_api_user_activate'),
    
    # ==================== ADMIN API - VIDEO MANAGEMENT ====================
    path('admin/api/videos/', admin_views.admin_api_videos, name='admin_api_videos'),
    path('admin/api/videos/<int:video_id>/', admin_views.admin_api_video_detail, 
         name='admin_api_video_detail'),
    path('admin/api/videos/create/', admin_views.admin_api_video_create, 
         name='admin_api_video_create'),
    path('admin/api/videos/<int:video_id>/update/', admin_views.admin_api_video_update, 
         name='admin_api_video_update'),
    path('admin/api/videos/<int:video_id>/delete/', admin_views.admin_api_video_delete, 
         name='admin_api_video_delete'),
    path('admin/api/videos/upload/', admin_views.admin_api_video_upload, 
         name='admin_api_video_upload'),
    
    # ==================== ADMIN API - PDF MANAGEMENT ====================
    path('admin/api/pdfs/', admin_views.admin_api_pdfs, name='admin_api_pdfs'),
    path('admin/api/pdfs/<int:pdf_id>/', admin_views.admin_api_pdf_detail, 
         name='admin_api_pdf_detail'),
    path('admin/api/pdfs/create/', admin_views.admin_api_pdf_create, 
         name='admin_api_pdf_create'),
    path('admin/api/pdfs/<int:pdf_id>/update/', admin_views.admin_api_pdf_update, 
         name='admin_api_pdf_update'),
    path('admin/api/pdfs/<int:pdf_id>/delete/', admin_views.admin_api_pdf_delete, 
         name='admin_api_pdf_delete'),
    path('admin/api/pdfs/upload/', admin_views.admin_api_pdf_upload, 
         name='admin_api_pdf_upload'),
    path('admin/api/pdfs/<int:pdf_id>/fix-file/', admin_views.admin_api_pdf_fix_file, 
         name='admin_api_pdf_fix_file'),
    path('admin/api/pdfs/<int:pdf_id>/debug/', admin_views.admin_api_pdf_debug, 
         name='admin_api_pdf_debug'),
    
    # ==================== ADMIN API - COURSE MANAGEMENT ====================
    path('admin/api/courses/', admin_views.admin_api_courses, name='admin_api_courses'),
    path('admin/api/courses/<int:course_id>/', admin_views.admin_api_course_detail, 
         name='admin_api_course_detail'),
    path('admin/api/courses/create/', admin_views.admin_api_course_create, 
         name='admin_api_course_create'),
    path('admin/api/courses/<int:course_id>/update/', admin_views.admin_api_course_update, 
         name='admin_api_course_update'),
    path('admin/api/courses/<int:course_id>/delete/', admin_views.admin_api_course_delete, 
         name='admin_api_course_delete'),
    
    # ==================== ADMIN API - PACKAGE MANAGEMENT ====================
    path('admin/api/packages/', admin_views.admin_api_packages, name='admin_api_packages'),
    path('admin/api/packages/create/', admin_views.admin_api_package_create, 
         name='admin_api_package_create'),
    path('admin/api/packages/<int:package_id>/update/', admin_views.admin_api_package_update, 
         name='admin_api_package_update'),
    
    # ==================== ADMIN API - ORDER MANAGEMENT ====================
    path('admin/api/orders/', admin_views.admin_api_orders, name='admin_api_orders'),
    
    # ==================== ADMIN API - PARTNERSHIP MANAGEMENT ====================
    path('admin/api/partnerships/', admin_views.admin_api_partnerships, 
         name='admin_api_partnerships'),
    path('admin/api/partnerships/<int:partnership_id>/update-status/', 
         admin_views.admin_api_update_partnership_status, 
         name='admin_api_update_partnership_status'),
    
    # ==================== ADMIN API - SUPPORT TICKETS ====================
    path('admin/api/support/tickets/', admin_views.admin_api_support_tickets, 
         name='admin_api_support_tickets'),
    path('admin/api/support/tickets/<int:ticket_id>/', 
         admin_views.admin_api_ticket_detail, name='admin_api_ticket_detail'),
    path('admin/api/support/tickets/<int:ticket_id>/reply/', 
         admin_views.admin_api_ticket_reply, name='admin_api_ticket_reply'),
    path('admin/api/support/tickets/<int:ticket_id>/update-status/', 
         admin_views.admin_api_ticket_update_status, name='admin_api_ticket_update_status'),
    
    # ==================== ADMIN API - BLOG MANAGEMENT ====================
    path('admin/api/blogs/', admin_views.admin_api_blogs, name='admin_api_blogs'),
    path('admin/api/blogs/create/', admin_views.admin_api_blog_create, 
         name='admin_api_blog_create'),
    path('admin/api/blogs/<int:blog_id>/update/', admin_views.admin_api_blog_update, 
         name='admin_api_blog_update'),
    
    # ==================== ADMIN API - REPORTS ====================
    path('admin/api/reports/revenue/', admin_views.admin_api_revenue_report, 
         name='admin_api_revenue_report'),
    path('admin/api/reports/users/', admin_views.admin_api_users_report, 
         name='admin_api_users_report'),
    
    # ==================== ADMIN API - DELETE ITEM ====================
    path('admin/api/<str:item_type>/<int:item_id>/delete/', 
         admin_views.admin_api_delete_item, name='admin_api_delete_item'),
    
    # ==================== COURSE PROGRESS APIS ====================
    path('api/course/lesson/complete/', api_mark_lesson_complete, name='api_mark_lesson_complete'),
    path('api/course/<int:course_id>/progress/', api_course_progress, name='api_course_progress'),
    path('api/course/<int:course_id>/next/', api_course_next_lesson, name='api_course_next_lesson'),
    path('api/course/<int:course_id>/reset/', api_course_reset_progress, name='api_course_reset_progress'),
    
    # ==================== TEST ENDPOINTS ====================
    path('test-emails/', views.test_all_emails, name='test_emails'),
    path('test-smtp/', views.test_smtp_connection, name='test_smtp'),
    path('emergency-email-fix/', views.emergency_email_fix, name='emergency_email_fix'),


    path('pesapal/initiate/', pesapal_initiate_payment, name='pesapal_initiate_payment'),
path('pesapal/callback/', pesapal_callback, name='pesapal_callback'),
path('pesapal/ipn/', pesapal_ipn, name='pesapal_ipn'),
path('payment/', views.payment, name='payment_page'),


 # SasaPay URLs - use views. prefix
    path('sasapay/process/', views.sasapay_process_payment, name='sasapay_process_payment'),
    path('sasapay/callback/', views.sasapay_callback, name='sasapay_callback'),
    path('sasapay/verify/', views.sasapay_verify, name='sasapay_verify'),
    path('sasapay/status/<str:reference>/', views.sasapay_status, name='sasapay_status'),
]

# ==================== MEDIA FILES SERVING ====================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files in all environments
urlpatterns += [
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]

# ==================== ERROR HANDLERS ====================
handler404 = 'myapp.views.custom_404'
handler500 = 'myapp.views.custom_500'