from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse
from . import views
from . import admin_views  
from . import s3_views 
from .views import (
    # Course progress APIs
    api_mark_lesson_complete,
    api_course_progress,
    api_course_next_lesson,
    api_course_reset_progress,
    # Payment views
    payment_pending,
    paystack_initiate_payment,
    paystack_mpesa_stk_push,
    paystack_verify_payment,
    paystack_webhook,
    # Book endpoints
    api_create_book_order,
    get_books,
    api_books,
    api_create_book,
    api_update_book,
    api_delete_book,
    api_book_orders,
    api_update_book_order_status,
    payment_book,
    book_download,
    # Ticket endpoint - ADDED
    api_create_ticket_order,
    # Merchandise endpoints
    get_merchandise,
    create_merchandise,
    update_merchandise,
    delete_merchandise,
    get_merchandise_orders,
    update_merchandise_order_status,
    # Event endpoints
    get_events,
    get_event_detail,
    update_event,
    get_tickets,
    get_ticket_detail,
    resend_ticket_email,
    mark_ticket_checked_in,
    # Free event registration
    api_free_ticket_registration,
    get_event_details,
    get_event_tickets_admin,
    check_in_ticket,
    # Order endpoints
    create_order,
    api_create_education_order,
    api_create_merchandise_order,
    payment_merchandise,
    # User API endpoints
    api_check_email,
    api_check_username,
    api_user_profile,
    api_user_stats,
    api_user_activities,
    api_user_notifications,
    api_mark_notification_read,
    api_mark_all_notifications_read,
    api_user_courses,
    api_user_videos,
    api_user_pdfs,
    api_course_enroll,
    api_watchlist,
    api_watchlist_count,
    api_watchlist_check,
    api_watchlist_add,
    api_watchlist_remove,
    api_user_communities,
    api_institute_eligibility,
    api_institute_apply,
    api_profile_update,
    api_password_change,
    api_user_orders,
    api_user_tickets,
    api_create_ticket,
    api_ticket_detail,
    api_ticket_reply,
    api_pdf_view,
    api_get_packages,
    api_unlock_video,
    api_send_support,
    api_update_settings,
    api_public_videos,
    api_public_pdfs,
    api_public_blogs,
    api_public_testimonials,
    api_public_faqs,
    api_public_courses,
    api_public_community_tiers,
    api_blog_detail,
    api_community_join,
    # Form submissions
    contact_form_submit,
    submit_partnership_application,
    # Payment initialization
    initialize_package_payment,
    api_create_order as api_create_order_view,
    education_payment,
    initiate_payment,
    process_payment,
    verify_payment,
    payment_failed,
    pay_without_login,
    verify_guest_payment,
    initiate_package_payment,
    initiate_education_payment,
    initiate_partnership_payment,
    initiate_custom_payment,
    payment_video,
    initiate_video_payment,
    initiate_course_payment,
    initiate_mentorship_payment,
)

urlpatterns = [
    # ==================== TEST ENDPOINTS ====================
    path('api/test/', lambda request: JsonResponse({'status': 'API working', 'message': 'Server is responding'}), name='api_test'),
    
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

    # ==================== ADMIN DATA EXPORTS ====================
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
    path('watch/<int:video_id>/', views.watch_video, name='watch_video'),
    path('pdf/<int:pdf_id>/view/', views.view_pdf, name='view_pdf'),
    path('pdf/<int:pdf_id>/download/', views.download_pdf, name='download_pdf'),
    path('course/<int:course_id>/', views.view_course, name='view_course'),
    path('course/<int:course_id>/complete/<str:lesson_type>/<int:lesson_id>/', 
         views.mark_lesson_complete, name='mark_lesson_complete'),
    path('api/initialize-payment/', views.initialize_package_payment, name='initialize_payment'),
    path('api/create-order/', views.api_create_order, name='api_create_order'),
    path('payment/success/<str:reference>/', views.payment_success, name='payment_success'),
    path('education/pay/', views.education_payment, name='education_payment'),
    path('api/create-education-order/', api_create_education_order, name='api_create_education_order'),

    # ==================== S3 UPLOAD ENDPOINTS ====================
    path('admin/api/get-s3-presigned-url/', s3_views.get_s3_presigned_url, name='get_s3_presigned_url'),
    path('admin/api/initiate-multipart-upload/', s3_views.initiate_multipart_upload, name='initiate_multipart_upload'),
    path('admin/api/complete-multipart-upload/', s3_views.complete_multipart_upload, name='complete_multipart_upload'),
    path('admin/api/abort-multipart-upload/', s3_views.abort_multipart_upload, name='abort_multipart_upload'),
    path('admin/api/test-s3-upload/', s3_views.test_s3_upload_direct, name='test_s3_upload'),
    
    # ==================== SUPPORT TICKETS ====================
    path('support/tickets/', views.support_tickets, name='support_tickets'),
    path('support/tickets/create/', views.create_ticket, name='create_ticket'),
    path('support/tickets/<int:ticket_id>/', views.view_ticket, name='view_ticket'),
    path('support/tickets/<int:ticket_id>/close/', views.close_ticket, name='close_ticket'),

    # ==================== PAYSTACK PAYMENT ROUTES ====================
    path('paystack/initiate/', paystack_initiate_payment, name='paystack_initiate'),
    path('paystack/mpesa/', paystack_mpesa_stk_push, name='paystack_mpesa'),
    path('paystack/verify/<str:reference>/', paystack_verify_payment, name='paystack_verify'),
    path('paystack/webhook/', paystack_webhook, name='paystack_webhook'),
    
    # ==================== PAYMENT ROUTES ====================
    path('payment/initiate/', initiate_payment, name='initiate_payment'),
    path('payment/process/', process_payment, name='process_payment'),
    path('payment/verify/<str:reference>/', verify_payment, name='verify_payment'),
    path('payment/failed/', payment_failed, name='payment_failed'),
    path('payment/pending/<str:reference>/', payment_pending, name='payment_pending'),
    path('pay-without-login/', pay_without_login, name='pay_without_login'),
    path('payment/guest-verify/<str:reference>/', verify_guest_payment, name='verify_guest_payment'),
    path('payment/package/<str:package_type>/<int:amount>/', initiate_package_payment, name='initiate_package_payment'),
    path('payment/education/<str:program_type>/<str:duration>/', initiate_education_payment, name='initiate_education_payment'),
    path('payment/partnership/<str:tier>/', initiate_partnership_payment, name='initiate_partnership_payment'),
    path('payment/custom/', initiate_custom_payment, name='initiate_custom_payment'),
    path('payment/video/<int:video_id>/', payment_video, name='payment_video'),
    path('initiate-video-payment/', initiate_video_payment, name='initiate_video_payment'),
    path('initiate-course-payment/', initiate_course_payment, name='initiate_course_payment'),
    path('initiate-mentorship-payment/', initiate_mentorship_payment, name='initiate_mentorship_payment'),
    
    # ==================== USER API ENDPOINTS ====================
    path('api/check-email/', api_check_email, name='api_check_email'),
    path('api/check-username/', api_check_username, name='api_check_username'),
    path('api/user/profile/', api_user_profile, name='api_user_profile'),
    path('api/user/stats/', api_user_stats, name='api_user_stats'),
    path('api/user/activities/', api_user_activities, name='api_user_activities'),
    path('api/user/notifications/', api_user_notifications, name='api_user_notifications'),
    path('api/notifications/<int:notification_id>/read/', api_mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/read-all/', api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    
    # ==================== DASHBOARD API ENDPOINTS ====================
    path('api/user/courses/', api_user_courses, name='api_user_courses'),
    path('api/user/videos/', api_user_videos, name='api_user_videos'),
    path('api/user/pdfs/', api_user_pdfs, name='api_user_pdfs'),
    path('api/user/courses/enroll/', api_course_enroll, name='api_course_enroll'),
    path('api/user/watchlist/', api_watchlist, name='api_watchlist'),
    path('api/user/watchlist/count/', api_watchlist_count, name='api_watchlist_count'),
    path('api/user/watchlist/check/', api_watchlist_check, name='api_watchlist_check'),
    path('api/user/watchlist/add/', api_watchlist_add, name='api_watchlist_add'),
    path('api/user/watchlist/remove/', api_watchlist_remove, name='api_watchlist_remove'),
    path('api/user/communities/', api_user_communities, name='api_user_communities'),
    path('api/user/institute/eligibility/', api_institute_eligibility, name='api_institute_eligibility'),
    path('api/user/institute/apply/', api_institute_apply, name='api_institute_apply'),
    path('api/user/profile/update/', api_profile_update, name='api_profile_update'),
    path('api/user/password/change/', api_password_change, name='api_password_change'),
    path('api/user/orders/', api_user_orders, name='api_user_orders'),
    path('api/user/orders/create/', api_create_order_view, name='api_create_order'),
    path('api/user/tickets/', api_user_tickets, name='api_user_tickets'),
    path('api/user/tickets/create/', api_create_ticket, name='api_create_ticket'),
    path('api/user/tickets/<int:ticket_id>/', api_ticket_detail, name='api_ticket_detail'),
    path('api/user/tickets/<int:ticket_id>/reply/', api_ticket_reply, name='api_ticket_reply'),
    
    # ==================== PDF API ENDPOINTS ====================
    path('api/user/pdfs/<int:pdf_id>/view/', api_pdf_view, name='api_pdf_view'),
    
    # ==================== CONTENT API ENDPOINTS ====================
    path('api/user/packages/', api_get_packages, name='api_get_packages'),
    path('api/unlock-video/', api_unlock_video, name='api_unlock_video'),
    path('api/send-support/', api_send_support, name='api_send_support'),
    path('api/update-settings/', api_update_settings, name='api_update_settings'),
    
    # ==================== PUBLIC API ENDPOINTS ====================
    path('api/public/videos/', api_public_videos, name='api_public_videos'),
    path('api/public/pdfs/', api_public_pdfs, name='api_public_pdfs'),
    path('api/public/blogs/', api_public_blogs, name='api_public_blogs'),
    path('api/public/testimonials/', api_public_testimonials, name='api_public_testimonials'),
    path('api/public/faqs/', api_public_faqs, name='api_public_faqs'),
    path('api/public/courses/', api_public_courses, name='api_public_courses'),
    path('api/public/community/tiers/', api_public_community_tiers, name='api_public_community_tiers'),
    path('api/blogs/<int:blog_id>/', api_blog_detail, name='api_blog_detail'),
    
    # ==================== FORM SUBMISSIONS ====================
    path('contact/submit/', contact_form_submit, name='contact_submit'),
    path('apply-partnership/', submit_partnership_application, name='submit_partnership_application'),
    
    # ==================== ADMIN AUTHENTICATION ====================
    path('admin/login/', admin_views.admin_login_view, name='admin_login'),
    path('admin/logout/', admin_views.admin_logout_view, name='admin_logout'),
    path('admin/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_alt'),
    path('admin/debug-courses-api/', admin_views.debug_courses_api, name='debug_courses_api'),
    path('admin/test-course-simple/', admin_views.test_course_simple, name='test_course_simple'),
    path('admin/debug-session/', admin_views.debug_session, name='debug_session'),
    path('admin/clear-session/', admin_views.clear_session, name='clear_session'),
    path('admin/test-access/', admin_views.test_admin_access, name='test_admin_access'),
    path('admin/debug-media/', admin_views.debug_media, name='debug_media'),
    
    # ==================== ADMIN API ====================
    path('admin/api/dashboard-stats/', admin_views.admin_api_dashboard_stats, name='admin_api_dashboard_stats'),
    path('admin/api/activities/', admin_views.admin_api_activities, name='admin_api_activities'),
    path('admin/api/users/', admin_views.admin_api_users, name='admin_api_users'),
    path('admin/api/users/<int:user_id>/', admin_views.admin_api_user_detail, name='admin_api_user_detail'),
    path('admin/api/users/create/', admin_views.admin_api_user_create, name='admin_api_user_create'),
    path('admin/api/users/<int:user_id>/update/', admin_views.admin_api_user_update, name='admin_api_user_update'),
    path('admin/api/users/<int:user_id>/delete/', admin_views.admin_api_user_delete, name='admin_api_user_delete'),
    path('admin/api/users/<int:user_id>/activate/', admin_views.admin_api_user_activate, name='admin_api_user_activate'),
    path('admin/api/users/export/', admin_views.admin_api_users_export, name='admin_api_users_export'),
    path('admin/api/courses/', admin_views.admin_api_courses, name='admin_api_courses'),
    path('admin/api/courses/<int:course_id>/', admin_views.admin_api_course_detail, name='admin_api_course_detail'),
    path('admin/api/courses/create/', admin_views.admin_api_course_create, name='admin_api_course_create'),
    path('admin/api/courses/<int:course_id>/update/', admin_views.admin_api_course_update, name='admin_api_course_update'),
    path('admin/api/courses/<int:course_id>/delete/', admin_views.admin_api_course_delete, name='admin_api_course_delete'),
    path('admin/api/courses/<int:course_id>/stats/', admin_views.admin_api_course_stats, name='admin_api_course_stats'),
    path('admin/api/courses/<int:course_id>/enrollments/', admin_views.admin_api_course_enrollments, name='admin_api_course_enrollments'),
    path('admin/api/courses/export/', admin_views.admin_api_courses_export, name='admin_api_courses_export'),
    path('admin/api/videos/', admin_views.admin_api_videos, name='admin_api_videos'),
    path('admin/api/videos/<int:video_id>/', admin_views.admin_api_video_detail, name='admin_api_video_detail'),
    path('admin/api/videos/create/', admin_views.admin_api_video_create, name='admin_api_video_create'),
    path('admin/api/videos/<int:video_id>/update/', admin_views.admin_api_video_update, name='admin_api_video_update'),
    path('admin/api/videos/<int:video_id>/delete/', admin_views.admin_api_video_delete, name='admin_api_video_delete'),
    path('admin/api/videos/upload/', admin_views.admin_api_video_upload, name='admin_api_video_upload'),
    path('admin/api/videos/export/', admin_views.admin_api_videos_export, name='admin_api_videos_export'),
    path('admin/api/pdfs/', admin_views.admin_api_pdfs, name='admin_api_pdfs'),
    path('admin/api/pdfs/<int:pdf_id>/', admin_views.admin_api_pdf_detail, name='admin_api_pdf_detail'),
    path('admin/api/pdfs/create/', admin_views.admin_api_pdf_create, name='admin_api_pdf_create'),
    path('admin/api/pdfs/<int:pdf_id>/update/', admin_views.admin_api_pdf_update, name='admin_api_pdf_update'),
    path('admin/api/pdfs/<int:pdf_id>/delete/', admin_views.admin_api_pdf_delete, name='admin_api_pdf_delete'),
    path('admin/api/pdfs/upload/', admin_views.admin_api_pdf_upload, name='admin_api_pdf_upload'),
    path('admin/api/pdfs/<int:pdf_id>/fix-file/', admin_views.admin_api_pdf_fix_file, name='admin_api_pdf_fix_file'),
    path('admin/api/pdfs/<int:pdf_id>/debug/', admin_views.admin_api_pdf_debug, name='admin_api_pdf_debug'),
    path('admin/api/pdfs/export/', admin_views.admin_api_pdfs_export, name='admin_api_pdfs_export'),
    path('admin/api/packages/', admin_views.admin_api_packages, name='admin_api_packages'),
    path('admin/api/packages/<int:package_id>/', admin_views.admin_api_package_detail, name='admin_api_package_detail'),
    path('admin/api/packages/create/', admin_views.admin_api_package_create, name='admin_api_package_create'),
    path('admin/api/packages/<int:package_id>/update/', admin_views.admin_api_package_update, name='admin_api_package_update'),
    path('admin/api/packages/<int:package_id>/delete/', admin_views.admin_api_package_delete, name='admin_api_package_delete'),
    path('admin/api/packages/<int:package_id>/toggle-popular/', admin_views.admin_api_package_toggle_popular, name='admin_api_package_toggle_popular'),
    path('admin/api/packages/export/', admin_views.admin_api_packages_export, name='admin_api_packages_export'),
    path('admin/api/orders/', admin_views.admin_api_orders, name='admin_api_orders'),
    path('admin/api/orders/<str:order_id>/', admin_views.admin_api_order_detail, name='admin_api_order_detail'),
    path('admin/api/orders/export/', admin_views.admin_api_orders_export, name='admin_api_orders_export'),
    path('admin/api/partnerships/', admin_views.admin_api_partnerships, name='admin_api_partnerships'),
    path('admin/api/partnerships/<int:partnership_id>/update-status/', admin_views.admin_api_update_partnership_status, name='admin_api_update_partnership_status'),
    path('admin/api/partnerships/export/', admin_views.admin_api_partnerships_export, name='admin_api_partnerships_export'),
    path('admin/api/support/tickets/', admin_views.admin_api_support_tickets, name='admin_api_support_tickets'),
    path('admin/api/support/tickets/<int:ticket_id>/', admin_views.admin_api_ticket_detail, name='admin_api_ticket_detail'),
    path('admin/api/support/tickets/<int:ticket_id>/reply/', admin_views.admin_api_ticket_reply, name='admin_api_ticket_reply'),
    path('admin/api/support/tickets/<int:ticket_id>/update-status/', admin_views.admin_api_ticket_update_status, name='admin_api_ticket_update_status'),
    path('admin/api/blogs/', admin_views.admin_api_blogs, name='admin_api_blogs'),
    path('admin/api/blogs/<int:blog_id>/', admin_views.admin_api_blog_detail, name='admin_api_blog_detail'),
    path('admin/api/blogs/create/', admin_views.admin_api_blog_create, name='admin_api_blog_create'),
    path('admin/api/blogs/<int:blog_id>/update/', admin_views.admin_api_blog_update, name='admin_api_blog_update'),
    path('admin/api/blogs/<int:blog_id>/delete/', admin_views.admin_api_blog_delete, name='admin_api_blog_delete'),
    path('admin/api/blogs/export/', admin_views.admin_api_blogs_export, name='admin_api_blogs_export'),
    path('admin/api/reports/revenue/', admin_views.admin_api_revenue_report, name='admin_api_revenue_report'),
    path('admin/api/reports/users/', admin_views.admin_api_users_report, name='admin_api_users_report'),
    path('admin/api/reports/revenue/export/', admin_views.admin_api_revenue_export, name='admin_api_revenue_export'),
    path('admin/api/<str:item_type>/<int:item_id>/delete/', admin_views.admin_api_delete_item, name='admin_api_delete_item'),
    
    # ==================== COURSE PROGRESS APIS ====================
    path('api/course/lesson/complete/', api_mark_lesson_complete, name='api_mark_lesson_complete'),
    path('api/course/<int:course_id>/progress/', api_course_progress, name='api_course_progress'),
    path('api/course/<int:course_id>/next/', api_course_next_lesson, name='api_course_next_lesson'),
    path('api/course/<int:course_id>/reset/', api_course_reset_progress, name='api_course_reset_progress'),
    
    # ==================== TEST ENDPOINTS ====================
    path('test-emails/', views.test_all_emails, name='test_emails'),
    path('test-smtp/', views.test_smtp_connection, name='test_smtp'),
    path('emergency-email-fix/', views.emergency_email_fix, name='emergency_email_fix'),

    # ==================== MERCHANDISE API ====================
    path('api/merchandise/', get_merchandise, name='get_merchandise'),
    path('api/merchandise/create/', create_merchandise, name='create_merchandise'),
    path('api/merchandise/<int:id>/update/', update_merchandise, name='update_merchandise'),
    path('api/merchandise/<int:id>/delete/', delete_merchandise, name='delete_merchandise'),

    # ==================== MERCHANDISE ORDERS ====================
    path('api/merchandise-orders/', get_merchandise_orders, name='get_merchandise_orders'),
    path('api/merchandise-orders/<int:id>/update-status/', update_merchandise_order_status, name='update_merchandise_order_status'),

    # ==================== EVENT API ====================
    path('api/events/', get_events, name='get_events'),
    path('api/events/<int:id>/', get_event_detail, name='get_event_detail'),
    path('api/events/update/<int:id>/', update_event, name='update_event'),



    path('admin/tickets/', admin_views.admin_ticket_management, name='admin_ticket_management'),
    path('api/tickets/', admin_views.api_get_tickets, name='api_get_tickets'),
    path('api/tickets/export/', admin_views.api_export_tickets, name='api_export_tickets'),

    # ==================== TICKET API ====================
    path('api/tickets/', get_tickets, name='get_tickets'),
    path('api/tickets/<int:id>/', get_ticket_detail, name='get_ticket_detail'),
    path('api/tickets/<int:id>/resend/', resend_ticket_email, name='resend_ticket_email'),
    path('api/tickets/<int:id>/checkin/', mark_ticket_checked_in, name='mark_ticket_checked_in'),

    # ==================== ORDER CREATION ====================
    path('api/create-order/', create_order, name='create_order'),
    
    # ==================== TICKET ORDER CREATION - NOW ACTIVE FOR PAID TICKETS ====================
    path('api/create-ticket-order/', api_create_ticket_order, name='api_create_ticket_order'),
    path('payment/ticket/<str:reference>/', views.payment_ticket, name='payment_ticket'),
    
    # ==================== OTHER ORDER CREATION ====================
    path('api/create-merchandise-order/', api_create_merchandise_order, name='api_create_merchandise_order'),
    path('payment/merchandise/<str:reference>/', payment_merchandise, name='payment_merchandise'),

    # ==================== BOOK URLS ====================
    path('api/books/', api_books, name='api_books'),
    path('api/books/create/', api_create_book, name='api_create_book'),
    path('api/books/<int:book_id>/update/', api_update_book, name='api_update_book'),
    path('api/books/<int:book_id>/delete/', api_delete_book, name='api_delete_book'),
    path('api/book/orders/', api_book_orders, name='api_book_orders'),
    path('api/book/orders/<int:order_id>/update-status/', api_update_book_order_status, name='api_update_book_order_status'),
    path('api/get-books/', get_books, name='get_books'),
    path('api/create-book-order/', api_create_book_order, name='api_create_book_order'),
    path('payment/book/<str:reference>/', payment_book, name='payment_book'),
    path('book/download/<str:access_code>/', book_download, name='book_download'),
    
    # ==================== FREE EVENT REGISTRATION URLS ====================
    path('api/free-ticket-registration/', api_free_ticket_registration, name='free_ticket_registration'),
    path('api/event/details/', get_event_details, name='get_event_details'),
    path('api/admin/tickets/', get_event_tickets_admin, name='get_event_tickets_admin'),
    path('api/admin/tickets/<int:ticket_id>/checkin/', check_in_ticket, name='check_in_ticket'),
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