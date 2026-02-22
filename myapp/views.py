from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template import Library
from django.db import connection
import logging
import json
import random
import string
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import base64
import urllib.parse
from .pesapal_utils import get_pesapal_iframe_url, query_pesapal_status

from .models import (
    MfalmeUsers, PaymentTransaction, Package,
    TrainingVideo, UserVideoAccess, Course, UserCourse, MentorshipProgram,
    SupportTicket, TicketReply, ActivityLog, PDF, Blog, VerificationCode,
    PartnershipProgram, UserPartnership, ContactSubmission, Notification,
    FAQ, Testimonial, CommunityTier, UserCommunityMembership, Statistic,
    EducationProgram, UserPDFAccess, Watchlist, InstituteApplication,
    CommunityJoinRequest
)

# ==================== TEMPLATE FILTERS ====================
register = Library()

@register.filter
def multiply(value, arg):
    """Simple multiplication filter for templates"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

# ==================== HELPER FUNCTIONS ====================

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def generate_reference():
    """Generate unique transaction reference"""
    return f"MBC{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def timesince(dt, default="just now"):
    """Return human readable time since"""
    if not dt:
        return default
    now = timezone.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds // 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"

def send_admin_notification_email(subject, template, context):
    """Send email to admin"""
    try:
        html_content = render_to_string(f'emails/{template}', context)
        text_content = f"New notification: {subject}"
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            settings.ADMIN_EMAILS
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Admin email error: {e}")
        return False

def send_user_notification_email(user, subject, template, context):
    """Send email to user"""
    try:
        html_content = render_to_string(f'emails/{template}', context)
        text_content = f"Notification: {subject}"
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"User email error: {e}")
        return False

# ==================== EMAIL FUNCTIONS ====================

def send_verification_email(user, code):
    """Send verification email using HTML template"""
    try:
        subject = 'Verify Your Account - Mfalme Betterdays Capital'
        
        html_content = render_to_string('emails/verification.html', {
            'username': user.username,
            'verification_code': code,
            'email': user.email,
            'expiry_minutes': 30,
            'year': timezone.now().year,
            'current_year': timezone.now().year
        })
        
        text_content = f"""
        Hello {user.username},
        
        Thank you for registering with Mfalme Betterdays Capital.
        
        Your verification code is: {code}
        
        This code will expire in 30 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Mfalme Betterdays Capital Team
        """
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print(f"✓ Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"✗ Verification email error: {e}")
        return False

def send_admin_notification(user):
    """Send admin notification when new user registers"""
    try:
        subject = '🔔 NEW USER REGISTRATION - Mfalme Betterdays Capital'
        
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        html_content = render_to_string('emails/admin_notification.html', {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'soldier_id': user.soldier_id,
            'date_joined': user.date_joined,
            'ip_address': user.registration_ip,
            'country': user.country or 'Not specified',
            'trading_experience': user.trading_experience,
            'user_id': user.id,
            'admin_url': f"{settings.SITE_URL}/admin/",
            'year': timezone.now().year,
            'current_year': timezone.now().year
        })
        
        text_content = f"""
        New User Registration Alert!
        
        Username: {user.username}
        Email: {user.email}
        Phone: {user.phone}
        Soldier ID: {user.soldier_id}
        Date: {user.date_joined}
        
        Login to admin panel to view details.
        """
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print(f"✓ Admin notification sent for {user.email}")
        return True
        
    except Exception as e:
        print(f"✗ Admin notification error: {e}")
        return False

def send_welcome_email(user):
    """Send welcome email after verification using HTML template"""
    try:
        subject = '🎉 Welcome to the Elite Circle - Mfalme Betterdays Capital!'
        
        html_content = render_to_string('emails/welcome.html', {
            'username': user.username,
            'soldier_id': user.soldier_id,
            'email': user.email,
            'phone': user.phone,
            'user_id': user.id,
            'signup_date': user.date_joined.strftime('%B %d, %Y'),
            'dashboard_url': f"{settings.SITE_URL}/dashboard/",
            'community_url': f"{settings.SITE_URL}/community/",
            'support_url': f"{settings.SITE_URL}/support/",
            'videos_url': f"{settings.SITE_URL}/my-videos/",
            'courses_url': f"{settings.SITE_URL}/my-courses/",
            'website_url': settings.SITE_URL,
            'year': timezone.now().year,
            'current_year': timezone.now().year
        })
        
        text_content = f"""
        Welcome to the Elite, {user.username}!
        
        Your account has been successfully verified.
        Your Soldier ID: {user.soldier_id}
        
        You now have access to:
        - Your personalized dashboard
        - Free trading resources
        - Community access
        
        Login here: {settings.SITE_URL}/login/
        
        To your success,
        The Mfalme Betterdays Capital Team
        """
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print(f"✓ Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"✗ Welcome email error: {e}")
        return False

def send_password_reset_email(user, code):
    """Send password reset email"""
    try:
        subject = 'Password Reset - Mfalme Betterdays Capital'
        
        html_content = render_to_string('emails/password_reset.html', {
            'username': user.username,
            'reset_code': code,
            'email': user.email,
            'expiry_minutes': 30,
            'year': timezone.now().year,
            'current_year': timezone.now().year
        })
        
        text_content = f"""
        Hello {user.username},
        
        You requested to reset your password.
        
        Your password reset code is: {code}
        
        This code will expire in 30 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Mfalme Betterdays Capital Team
        """
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return True
    except Exception as e:
        print(f"Password reset email error: {e}")
        return False

def send_community_application_email(user, community, request):
    """Send email to admin about community join request"""
    try:
        subject = f'🔔 NEW COMMUNITY JOIN REQUEST - {community.name}'
        
        html_content = render_to_string('emails/community_application.html', {
            'user': user,
            'community': community,
            'total_deposits': user.total_deposits,
            'trading_experience': user.trading_experience,
            'courses_completed': UserCourse.objects.filter(user=user).count(),
            'admin_url': f"{settings.SITE_URL}/admin/",
            'year': timezone.now().year
        })
        
        send_admin_notification_email(subject, 'community_application.html', {
            'user': user,
            'community': community,
            'total_deposits': user.total_deposits
        })
        return True
    except Exception as e:
        print(f"Community application email error: {e}")
        return False

def send_institute_application_email(application):
    """Send email to admin about institute application"""
    try:
        subject = '🔔 NEW INSTITUTE APPLICATION - Mfalme Betterdays Capital'
        
        send_admin_notification_email(subject, 'institute_application.html', {
            'application': application,
            'user': application.user,
            'admin_url': f"{settings.SITE_URL}/admin/"
        })
        return True
    except Exception as e:
        print(f"Institute application email error: {e}")
        return False

def send_ticket_notification_email(ticket, is_new=True):
    """Send email about support ticket"""
    try:
        if is_new:
            subject = f'🔔 NEW SUPPORT TICKET - #{ticket.ticket_number}'
            template = 'new_ticket_notification.html'
        else:
            subject = f'💬 TICKET REPLY - #{ticket.ticket_number}'
            template = 'ticket_reply_notification.html'
        
        send_admin_notification_email(subject, template, {
            'ticket': ticket,
            'user': ticket.user,
            'admin_url': f"{settings.SITE_URL}/admin/support/tickets/{ticket.id}/"
        })
        return True
    except Exception as e:
        print(f"Ticket notification email error: {e}")
        return False

# ==================== ACCESS CONTROL HELPER FUNCTIONS ====================

def check_video_access(user, video):
    """Check if user has access to a video"""
    if video.price == 0:  # Free video
        return True
    return UserVideoAccess.objects.filter(user=user, video=video).exists()

def check_pdf_access(user, pdf):
    """Check if user has access to a PDF"""
    if pdf.is_free:
        return True
    return UserPDFAccess.objects.filter(user=user, pdf=pdf).exists()

def check_course_access(user, course_id):
    """Check if user has active access to a course with expiration"""
    try:
        enrollment = UserCourse.objects.get(
            user=user, 
            course_id=course_id,
            is_active=True
        )
        
        # Check if access has expired
        if enrollment.is_access_expired():
            # Mark as inactive
            enrollment.is_active = False
            enrollment.save(update_fields=['is_active'])
            
            # Send notification
            Notification.objects.create(
                user=user,
                title='Course Access Expired',
                message=f'Your access to {enrollment.course.title} has expired. Renew now to continue learning.',
                notification_type='WARNING',
                related_object_type='course',
                related_object_id=course_id
            )
            
            # Log activity
            log_activity(
                user,
                'COURSE_ACCESS_EXPIRED',
                f'Access expired for course: {enrollment.course.title}'
            )
            
            return False, enrollment
        return True, enrollment
    except UserCourse.DoesNotExist:
        return False, None

def grant_video_access(user, video, payment=None):
    """Grant user access to a video"""
    access, created = UserVideoAccess.objects.get_or_create(
        user=user,
        video=video,
        defaults={'payment': payment}
    )
    if created:
        Notification.objects.create(
            user=user,
            title='Video Unlocked',
            message=f'You now have access to: {video.title}',
            notification_type='SUCCESS',
            related_object_type='video',
            related_object_id=video.id
        )
    return access

def grant_pdf_access(user, pdf, payment=None):
    """Grant user access to a PDF"""
    access, created = UserPDFAccess.objects.get_or_create(
        user=user,
        pdf=pdf,
        defaults={'payment': payment}
    )
    if created:
        Notification.objects.create(
            user=user,
            title='PDF Unlocked',
            message=f'You can now view: {pdf.title}',
            notification_type='SUCCESS',
            related_object_type='pdf',
            related_object_id=pdf.id
        )
    return access

def log_activity(user, action, description, request=None):
    """Create activity log entry"""
    return ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )

# ==================== USER AUTHENTICATION ====================

def login_page(request):
    """User login page - handles both login and registration"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    
    context = {
        'total_users': MfalmeUsers.objects.filter(account_status='active').count(),
        'total_videos': TrainingVideo.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'testimonials': Testimonial.objects.filter(is_active=True, is_featured=True)[:3],
        'stats': Statistic.objects.filter(is_active=True),
    }
    return render(request, 'login.html', context)

def login_user(request):
    """Handle user login"""
    if request.method != 'POST':
        return redirect('login_page')
    
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    remember = request.POST.get('remember') == 'on'
    
    print("\n" + "="*60)
    print("🔍 LOGIN ATTEMPT")
    print("="*60)
    print(f"📝 Email: {email}")
    
    if not email or not password:
        messages.error(request, 'Please fill in all fields')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(email=email)
        print(f"✅ User found: {user.username}")
        
        if not user.check_password(password):
            print("❌ Invalid password")
            messages.error(request, 'Invalid password')
            return redirect('login_page')
        
        if user.account_status != 'active':
            if user.account_status == 'pending':
                messages.warning(request, 'Please verify your account first. Check your inbox.')
            elif user.account_status == 'suspended':
                messages.error(request, 'Your account has been suspended. Contact support.')
            elif user.account_status == 'banned':
                messages.error(request, 'Your account has been banned.')
            else:
                messages.error(request, f'Account is {user.account_status}')
            return redirect('login_page')
        
        login(request, user)
        request.session.save()
        
        if not remember:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(1209600)
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        log_activity(user, 'LOGIN', f'Logged in from {get_client_ip(request)}', request)
        
        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
        
        if user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'No account found with this email')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Login error: {str(e)}')
        return redirect('login_page')

def register_user(request):
    """Handle user registration"""
    import sys
    print("\n" + "="*60)
    print("🔍 NEW REGISTRATION ATTEMPT")
    print("="*60)
    
    if request.method != 'POST':
        print("❌ Not a POST request, redirecting to login_page")
        return redirect('login_page')
    
    # Get form data
    email = request.POST.get('email', '').strip()
    username = request.POST.get('username', '').strip()
    phone = request.POST.get('phone', '').strip()
    password = request.POST.get('password', '')
    confirm_password = request.POST.get('confirm_password', '')
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    country = request.POST.get('country', '').strip()
    trading_experience = request.POST.get('trading_experience', 'Beginner')
    terms_accepted = request.POST.get('terms_accepted') == 'on'
    
    print(f"📝 Email: {email}")
    print(f"📝 Username: {username}")
    
    # Validation
    errors = []
    
    if not email:
        errors.append('Email is required')
    elif MfalmeUsers.objects.filter(email=email).exists():
        errors.append('Email already registered')
        print(f"❌ Email already exists: {email}")
    
    if not username:
        errors.append('Username is required')
    elif MfalmeUsers.objects.filter(username=username).exists():
        errors.append('Username already taken')
        print(f"❌ Username already exists: {username}")
    
    if not phone:
        errors.append('Phone number is required')
    
    if not password:
        errors.append('Password is required')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters')
    
    if password != confirm_password:
        errors.append('Passwords do not match')
        print(f"❌ Passwords do not match")
    
    if not terms_accepted:
        errors.append('You must accept the terms and conditions')
        print(f"❌ Terms not accepted")
    
    if errors:
        for error in errors:
            messages.error(request, error)
        request.session['form_data'] = {
            'email': email,
            'username': username,
            'phone': phone,
            'first_name': first_name,
            'last_name': last_name,
            'country': country,
            'trading_experience': trading_experience,
        }
        request.session.save()
        return redirect('login_page')
    
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        print(f"✅ Validation passed, creating user...")
        
        user = MfalmeUsers.objects.create_user(
            email=email,
            password=password,
            username=username,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            country=country,
            trading_experience=trading_experience,
            account_status='pending',
            email_verified=False,
            registration_ip=ip_address,
            user_agent=user_agent,
        )
        
        print(f"✅ User created with ID: {user.id}")
        
        verification_code = generate_verification_code()
        VerificationCode.objects.create(
            user=user,
            code=verification_code,
            code_type='account_verification',
            expires_at=timezone.now() + timedelta(minutes=30),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        print(f"✅ Verification code generated: {verification_code}")
        
        email_sent = send_verification_email(user, verification_code)
        admin_notified = send_admin_notification(user)
        
        Notification.objects.create(
            user=user,
            title='Welcome to the Elite!',
            message=f'Welcome {username}! Please verify your account to get started.',
            notification_type='SUCCESS',
        )
        
        log_activity(user, 'REGISTER', f'New registration from {ip_address}', request)
        
        if email_sent:
            messages.success(request, 'Registration successful! Please check your email for verification code.')
            request.session['verification_email'] = email
            request.session.save()
            return redirect('verify_account')
        else:
            messages.warning(request, 'Registration successful but verification email could not be sent. Contact support.')
            return redirect('login_page')
            
    except Exception as e:
        print(f"❌ Registration exception: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Registration failed: {str(e)}')
        return redirect('login_page')

def verify_account_page(request):
    """Account verification page"""
    import sys
    print("-" * 50)
    print("🔍 VERIFY ACCOUNT PAGE ACCESSED")
    
    email = request.session.get('verification_email', '')
    print(f"🔍 Email from session: '{email}'")
    
    if not email:
        print("❌ No email in session")
        messages.error(request, 'No verification session found. Please register again.')
        return redirect('login_page')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        print(f"🔍 POST request with code: '{code}'")
        
        if not code:
            messages.error(request, 'Please enter verification code')
            return render(request, 'verify_account.html', {'user_email': email})
        
        try:
            user = MfalmeUsers.objects.get(email=email)
            
            verification = VerificationCode.objects.filter(
                user=user,
                code_type='account_verification',
                is_used=False
            ).latest('created_at')
            
            if verification.code != code:
                messages.error(request, 'Invalid verification code')
            elif verification.is_expired():
                messages.error(request, 'Verification code has expired')
                verification.is_used = True
                verification.save()
            else:
                verification.is_used = True
                verification.used_at = timezone.now()
                verification.save()
                
                user.email_verified = True
                user.account_status = 'active'
                user.verified_at = timezone.now()
                user.save(update_fields=['email_verified', 'account_status', 'verified_at'])
                
                print(f"✅ User activated successfully!")
                
                welcome_sent = send_welcome_email(user)
                
                Notification.objects.create(
                    user=user,
                    title='Account Verified!',
                    message='Your account has been verified. You can now login.',
                    notification_type='SUCCESS',
                )
                
                log_activity(user, 'ACCOUNT_VERIFICATION', 'Account verified successfully', request)
                
                if welcome_sent:
                    messages.success(request, 'Account verified successfully! Check your email for welcome message.')
                else:
                    messages.success(request, 'Account verified successfully!')
                
                if 'verification_email' in request.session:
                    del request.session['verification_email']
                
                return redirect('login_page')
                
        except MfalmeUsers.DoesNotExist:
            messages.error(request, 'User not found')
        except VerificationCode.DoesNotExist:
            messages.error(request, 'No verification code found. Please request a new one.')
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'verify_account.html', {'user_email': email})

def resend_verification(request):
    """Resend verification code"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            email = data.get('email', '')
        else:
            email = request.POST.get('email', '')
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email required'})
        
        try:
            user = MfalmeUsers.objects.get(email=email)
            
            if user.email_verified:
                return JsonResponse({'success': False, 'error': 'Account already verified'})
            
            verification_code = generate_verification_code()
            VerificationCode.objects.create(
                user=user,
                code=verification_code,
                code_type='account_verification',
                expires_at=timezone.now() + timedelta(minutes=30),
                ip_address=get_client_ip(request),
            )
            
            email_sent = send_verification_email(user, verification_code)
            
            if email_sent:
                return JsonResponse({'success': True, 'message': 'New verification code sent'})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to send email'})
                
        except MfalmeUsers.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def forgot_password(request):
    """Forgot password page"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        try:
            user = MfalmeUsers.objects.get(email=email)
            
            reset_code = generate_verification_code()
            VerificationCode.objects.create(
                user=user,
                code=reset_code,
                code_type='password_reset',
                expires_at=timezone.now() + timedelta(minutes=30),
                ip_address=get_client_ip(request),
            )
            
            send_password_reset_email(user, reset_code)
            
            messages.success(request, 'Password reset code sent to your email')
            request.session['reset_email'] = email
            return redirect('reset_password')
            
        except MfalmeUsers.DoesNotExist:
            messages.error(request, 'No account found with this email')
    
    return render(request, 'forgot_password.html')

def reset_password(request):
    """Reset password page"""
    email = request.session.get('reset_email', '')
    if not email:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'reset_password.html', {'email': email})
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'reset_password.html', {'email': email})
        
        try:
            user = MfalmeUsers.objects.get(email=email)
            
            verification = VerificationCode.objects.filter(
                user=user,
                code=code,
                code_type='password_reset',
                is_used=False
            ).latest('created_at')
            
            if verification.is_expired():
                messages.error(request, 'Reset code has expired')
            else:
                user.set_password(password)
                user.password_changed_at = timezone.now()
                user.save(update_fields=['password', 'password_changed_at'])
                
                verification.is_used = True
                verification.used_at = timezone.now()
                verification.save()
                
                log_activity(user, 'PASSWORD_CHANGE', 'Password reset via email', request)
                
                Notification.objects.create(
                    user=user,
                    title='Password Changed',
                    message='Your password has been successfully reset.',
                    notification_type='SUCCESS',
                )
                
                messages.success(request, 'Password reset successful. You can now login.')
                
                if 'reset_email' in request.session:
                    del request.session['reset_email']
                
                return redirect('login_page')
                
        except MfalmeUsers.DoesNotExist:
            messages.error(request, 'User not found')
        except VerificationCode.DoesNotExist:
            messages.error(request, 'Invalid reset code')
    
    return render(request, 'reset_password.html', {'email': email})

def logout_user(request):
    """User logout"""
    if request.user.is_authenticated:
        log_activity(request.user, 'LOGOUT', 'User logged out', request)
        logout(request)
        messages.success(request, 'You have been logged out successfully')
    return redirect('index')

# ==================== USER DASHBOARD ====================

@login_required
def dashboard(request):
    """User dashboard - accessible to all authenticated users"""
    print("\n" + "="*60)
    print("🔍 DASHBOARD ACCESSED")
    
    if not request.user.is_authenticated:
        print("❌ User not authenticated")
        return redirect('login_page')
    
    user = request.user
    print(f"✅ Dashboard accessed by: {user.username}")
    
    context = {
        'user': user,
        'recent_videos': UserVideoAccess.objects.filter(user=user).select_related('video').order_by('-unlocked_at')[:5],
        'recent_pdfs': UserPDFAccess.objects.filter(user=user).select_related('pdf').order_by('-unlocked_at')[:5],
        'enrolled_courses': UserCourse.objects.filter(user=user, is_active=True).select_related('course')[:3],
        'recent_transactions': PaymentTransaction.objects.filter(user=user).order_by('-created_at')[:5],
        'notifications': Notification.objects.filter(user=user, is_read=False)[:10],
        'stats': {
            'videos_watched': UserVideoAccess.objects.filter(user=user).count(),
            'pdfs_viewed': UserPDFAccess.objects.filter(user=user, viewed=True).count(),
            'courses_enrolled': UserCourse.objects.filter(user=user, is_active=True).count(),
            'total_spent': float(PaymentTransaction.objects.filter(user=user, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
        },
        'recent_activities': ActivityLog.objects.filter(user=user).order_by('-created_at')[:10],
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    """User profile page"""
    return render(request, 'profile.html', {'user': request.user})

@login_required
def profile_update(request):
    """Update user profile"""
    if request.method == 'POST':
        user = request.user
        
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.country = request.POST.get('country', user.country)
        user.city = request.POST.get('city', user.city)
        user.address = request.POST.get('address', user.address)
        user.whatsapp_number = request.POST.get('whatsapp_number', user.whatsapp_number)
        user.telegram_username = request.POST.get('telegram_username', user.telegram_username)
        user.bio = request.POST.get('bio', user.bio)
        
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        
        log_activity(user, 'PROFILE_UPDATE', 'Updated profile information', request)
        messages.success(request, 'Profile updated successfully')
        
        return redirect('profile')
    
    return redirect('profile')

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        user = request.user
        current = request.POST.get('current_password', '')
        new = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')
        
        if not user.check_password(current):
            messages.error(request, 'Current password is incorrect')
        elif new != confirm:
            messages.error(request, 'New passwords do not match')
        elif len(new) < 8:
            messages.error(request, 'Password must be at least 8 characters')
        else:
            user.set_password(new)
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password', 'password_changed_at'])
            
            log_activity(user, 'PASSWORD_CHANGE', 'Password changed from profile', request)
            messages.success(request, 'Password changed successfully')
            
            # Re-authenticate to maintain session
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
    
    return redirect('profile')

# ==================== CONTENT VIEWING ====================

@login_required
def my_videos(request):
    """List user's videos"""
    user = request.user
    video_access = UserVideoAccess.objects.filter(user=user).select_related('video').order_by('-unlocked_at')
    
    free_videos = TrainingVideo.objects.filter(price=0, is_active=True).exclude(
        id__in=video_access.values_list('video_id', flat=True)
    )
    
    context = {
        'purchased_videos': video_access,
        'free_videos': free_videos,
        'total_videos': video_access.count() + free_videos.count(),
    }
    return render(request, 'my_videos.html', context)

@login_required
def my_pdfs(request):
    """List user's PDFs"""
    user = request.user
    pdf_access = UserPDFAccess.objects.filter(user=user).select_related('pdf').order_by('-unlocked_at')
    
    free_pdfs = PDF.objects.filter(is_free=True, is_active=True).exclude(
        id__in=pdf_access.values_list('pdf_id', flat=True)
    )
    
    context = {
        'purchased_pdfs': pdf_access,
        'free_pdfs': free_pdfs,
        'total_pdfs': pdf_access.count() + free_pdfs.count(),
    }
    return render(request, 'my_pdfs.html', context)

@login_required
def my_courses(request):
    """List user's courses - WITH EXPIRATION CHECK"""
    user = request.user
    courses = UserCourse.objects.filter(user=user).select_related('course').order_by('-enrolled_at')
    
    # Check for expired courses and update them
    for enrollment in courses:
        if enrollment.is_access_expired() and enrollment.is_active:
            enrollment.is_active = False
            enrollment.save(update_fields=['is_active'])
    
    # Refresh queryset after updates
    courses = UserCourse.objects.filter(user=user).select_related('course').order_by('-enrolled_at')
    
    context = {
        'courses': courses,
        'total_courses': courses.count(),
        'active_courses': courses.filter(is_active=True).count(),
        'expired_courses': courses.filter(is_active=False).count(),
    }
    return render(request, 'view_course.html', context)

@login_required
def transaction_history(request):
    """User transaction history"""
    user = request.user
    transactions = PaymentTransaction.objects.filter(user=user).order_by('-created_at')
    
    paginator = Paginator(transactions, 20)
    page = request.GET.get('page', 1)
    transactions_page = paginator.get_page(page)
    
    context = {
        'transactions': transactions_page,
        'total_count': transactions.count(),
        'total_spent': float(transactions.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
    }
    return render(request, 'transaction_history.html', context)

# ==================== WATCH VIDEO VIEW ====================

@login_required
def watch_video(request, video_id):
    """Watch a specific video - DOWNLOAD DISABLED"""
    try:
        video = get_object_or_404(TrainingVideo, id=video_id, is_active=True)
    except:
        messages.error(request, 'Video not found')
        return redirect('my_videos')
    
    user = request.user
    
    # Check if user has access
    has_access = check_video_access(user, video)
    
    if not has_access:
        messages.error(request, 'You do not have access to this video')
        return redirect('my_videos')
    
    # Increment view count
    video.view_count += 1
    video.save(update_fields=['view_count'])
    
    # Log activity
    log_activity(user, 'VIDEO_WATCH', f'Watched video: {video.title}', request)
    
    # Get related videos from same course
    related = TrainingVideo.objects.filter(
        course=video.course, 
        is_active=True
    ).exclude(id=video.id)[:5]
    
    # Prepare video URLs and check if files exist
    video_file_url = None
    if video.video_file:
        try:
            if video.video_file.storage.exists(video.video_file.name):
                video_file_url = video.video_file.url
            else:
                print(f"Video file missing: {video.video_file.name}")
        except Exception as e:
            print(f"Error accessing video file: {e}")
    
    thumbnail_url = None
    if video.thumbnail:
        try:
            if video.thumbnail.storage.exists(video.thumbnail.name):
                thumbnail_url = video.thumbnail.url
        except:
            pass
    
    # Get embed URL for YouTube/Vimeo
    embed_url = None
    if hasattr(video, 'video_type') and video.video_type == 'youtube' and hasattr(video, 'youtube_id') and video.youtube_id:
        embed_url = f"https://www.youtube.com/embed/{video.youtube_id}"
    elif hasattr(video, 'video_type') and video.video_type == 'vimeo' and hasattr(video, 'vimeo_id') and video.vimeo_id:
        embed_url = f"https://player.vimeo.com/video/{video.vimeo_id}"
    
    context = {
        'video': video,
        'video_file_url': video_file_url,
        'thumbnail_url': thumbnail_url,
        'related_videos': related,
        'has_video_file': video_file_url is not None,
        'video_url': video.video_url or '',
        'embed_code': video.embed_code or '',
        'youtube_id': getattr(video, 'youtube_id', ''),
        'vimeo_id': getattr(video, 'vimeo_id', ''),
        'video_type': getattr(video, 'video_type', ''),
        'embed_url': embed_url or '',
        'disable_downloads': True,  # Flag for template to hide download buttons
    }
    
    return render(request, 'watch_video.html', context)

# ==================== VIEW PDF (VIEW INSTEAD OF DOWNLOAD) ====================

@login_required
def view_pdf(request, pdf_id):
    """View PDF in browser instead of downloading"""
    try:
        pdf = get_object_or_404(PDF, id=pdf_id, is_active=True)
    except:
        messages.error(request, 'PDF not found')
        return redirect('my_pdfs')
    
    user = request.user
    
    # Check if user has access
    has_access = check_pdf_access(user, pdf)
    
    if not has_access:
        messages.error(request, 'You do not have access to this PDF')
        return redirect('my_pdfs')
    
    # Check if file exists
    if not pdf.pdf_file:
        messages.error(request, 'PDF file not found on server')
        return redirect('my_pdfs')
    
    try:
        # Update access record - track views instead of downloads
        access, created = UserPDFAccess.objects.get_or_create(user=user, pdf=pdf)
        access.viewed = True
        access.view_count += 1
        access.last_viewed = timezone.now()
        access.save(update_fields=['viewed', 'view_count', 'last_viewed'])
        
        # Update PDF view count
        pdf.views += 1
        pdf.save(update_fields=['views'])
        
        # Log activity
        log_activity(user, 'PDF_VIEWED', f'Viewed PDF: {pdf.title}', request)
        
        # Return the file for viewing (inline, not attachment)
        response = FileResponse(pdf.pdf_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pdf.pdf_file.name.split("/")[-1]}"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
        
    except Exception as e:
        messages.error(request, f'Error viewing PDF: {str(e)}')
        return redirect('my_pdfs')

# ==================== DEPRECATED DOWNLOAD PDF ====================

@login_required
def download_pdf(request, pdf_id):
    """DEPRECATED: Redirect to view instead of download"""
    messages.info(request, 'PDFs are now viewed in browser instead of downloaded.')
    return redirect('view_pdf', pdf_id=pdf_id)

# ==================== VIEW COURSE WITH EXPIRATION ====================

@login_required
def view_course(request, course_id):
    """View course details and content - WITH EXPIRATION CHECK"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    user = request.user
    
    # Check access with expiration
    has_access, enrollment = check_course_access(user, course_id)
    
    if not has_access or not enrollment:
        if enrollment and enrollment.is_access_expired():
            messages.error(request, 'Your course access has expired. Please renew to continue learning.')
        else:
            messages.error(request, 'You are not enrolled in this course')
        return redirect('my_courses')
    
    videos = TrainingVideo.objects.filter(course=course, is_active=True).order_by('order')
    pdfs = PDF.objects.filter(course=course, is_active=True).order_by('order')
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'videos': videos,
        'pdfs': pdfs,
        'progress': enrollment.progress,
        'completed_count': len(enrollment.completed_lessons) if enrollment.completed_lessons else 0,
        'total_lessons': videos.count() + pdfs.count(),
        'expires_in': enrollment.time_until_expiry(),
        'is_expired': enrollment.is_access_expired(),
    }
    return render(request, 'view_course.html', context)

@login_required
def mark_lesson_complete(request, course_id, lesson_type, lesson_id):
    """Mark a lesson as complete"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    
    # Check access with expiration
    has_access, enrollment = check_course_access(user, course_id)
    
    if not has_access or not enrollment:
        return JsonResponse({'error': 'Not enrolled or access expired'}, status=403)
    
    lesson_key = f"{lesson_type}_{lesson_id}"
    if not enrollment.completed_lessons:
        enrollment.completed_lessons = []
    
    if lesson_key not in enrollment.completed_lessons:
        enrollment.completed_lessons.append(lesson_key)
        
        total_lessons = TrainingVideo.objects.filter(course=course).count() + PDF.objects.filter(course=course).count()
        if total_lessons > 0:
            enrollment.progress = int((len(enrollment.completed_lessons) / total_lessons) * 100)
        
        enrollment.save()
        
        return JsonResponse({
            'success': True,
            'progress': enrollment.progress,
            'completed_count': len(enrollment.completed_lessons),
            'total_lessons': total_lessons,
        })
    
    return JsonResponse({'success': True})

# ==================== SUPPORT TICKETS ====================

@login_required
def support_tickets(request):
    """User support tickets"""
    user = request.user
    tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'open_count': tickets.filter(status='open').count(),
        'resolved_count': tickets.filter(status='resolved').count(),
    }
    return render(request, 'support_tickets.html', context)

@login_required
def create_ticket(request):
    """Create a support ticket"""
    if request.method == 'POST':
        user = request.user
        
        ticket = SupportTicket.objects.create(
            user=user,
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
            category=request.POST.get('category', 'general'),
            priority=request.POST.get('priority', 'medium'),
        )
        
        log_activity(user, 'SUPPORT_TICKET_CREATED', f'Created ticket: {ticket.subject[:50]}', request)
        
        messages.success(request, f'Ticket #{ticket.ticket_number} created successfully')
        return redirect('view_ticket', ticket_id=ticket.id)
    
    return render(request, 'create_ticket.html')

@login_required
def view_ticket(request, ticket_id):
    """View a specific ticket"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    replies = ticket.replies.all().order_by('created_at')
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            reply = TicketReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=message
            )
            ticket.status = 'waiting_reply'
            ticket.save(update_fields=['status'])
            messages.success(request, 'Reply added')
            return redirect('view_ticket', ticket_id=ticket.id)
    
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    return render(request, 'view_ticket.html', context)

@login_required
def close_ticket(request, ticket_id):
    """Close a ticket"""
    if request.method == 'POST':
        ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
        ticket.status = 'closed'
        ticket.closed_at = timezone.now()
        ticket.save(update_fields=['status', 'closed_at'])
        messages.success(request, 'Ticket closed')
    return redirect('view_ticket', ticket_id=ticket_id)

# ==================== API ENDPOINTS ====================

@login_required
def api_user_profile(request):
    """Get user profile (JSON)"""
    user = request.user
    return JsonResponse({
        'id': user.id,
        'soldier_id': user.soldier_id,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'elite_rank': user.elite_rank,
        'account_status': user.account_status,
        'email_verified': user.email_verified,
        'country': user.country,
        'city': user.city,
        'trading_experience': user.trading_experience,
        'account_balance': float(user.account_balance),
        'referral_code': user.referral_code,
        'referral_count': user.referral_count,
        'referral_earnings': float(user.referral_earnings),
        'date_joined': user.date_joined.strftime('%Y-%m-%d'),
        'profile_image': user.profile_image.url if user.profile_image else None,
        'total_deposits': float(user.total_deposits),
        'total_withdrawals': float(user.total_withdrawals),
        'total_profit': float(user.total_profit),
        'success_rate': user.success_rate,
    })

@login_required
def api_user_stats(request):
    """Get user statistics (JSON)"""
    user = request.user
    
    videos_watched = UserVideoAccess.objects.filter(user=user).count()
    pdfs_viewed = UserPDFAccess.objects.filter(user=user, viewed=True).count()
    courses_enrolled = UserCourse.objects.filter(user=user, is_active=True).count()
    watchlist_count = Watchlist.objects.filter(user=user).count()
    
    return JsonResponse({
        'videos_watched': videos_watched,
        'pdfs_viewed': pdfs_viewed,
        'courses_enrolled': courses_enrolled,
        'total_spent': float(PaymentTransaction.objects.filter(user=user, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
        'tickets_created': SupportTicket.objects.filter(user=user).count(),
        'open_tickets': SupportTicket.objects.filter(user=user, status='open').count(),
        'referral_earnings': float(user.referral_earnings),
        'success_rate': user.success_rate,
        'elite_rank': user.elite_rank,
        'watchlist_count': watchlist_count,
        'community_memberships': UserCommunityMembership.objects.filter(user=user, status='active').count(),
    })

@login_required
def api_user_activities(request):
    """Get user activities (JSON)"""
    limit = int(request.GET.get('limit', 10))
    activities = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:limit]
    
    data = []
    for act in activities:
        data.append({
            'id': act.id,
            'action': act.action,
            'description': act.description,
            'time': timesince(act.created_at),
            'created_at': act.created_at.isoformat(),
        })
    
    return JsonResponse(data, safe=False)

@login_required
def api_user_notifications(request):
    """Get user notifications (JSON)"""
    unread_only = request.GET.get('unread_only') == 'true'
    
    notifications = Notification.objects.filter(user=request.user)
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')[:20]
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'time': timesince(notif.created_at),
            'created_at': notif.created_at.isoformat(),
            'action_url': notif.action_url,
            'action_text': notif.action_text,
        })
    
    return JsonResponse({
        'notifications': data,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    })

@login_required
def api_mark_notification_read(request, notification_id):
    """Mark notification as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=['is_read', 'read_at'])
    
    return JsonResponse({'success': True})

@login_required
def api_mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return JsonResponse({'success': True})

# ==================== NEW API ENDPOINTS FOR DASHBOARD ====================

@login_required
def api_user_courses(request):
    """Get user's enrolled courses - WITH EXPIRATION"""
    user = request.user
    
    # Check for expired courses and update them
    expired = UserCourse.objects.filter(user=user, is_active=True)
    for enrollment in expired:
        if enrollment.is_access_expired():
            enrollment.is_active = False
            enrollment.save(update_fields=['is_active'])
    
    enrollments = UserCourse.objects.filter(user=user, is_active=True).select_related('course')
    
    data = []
    for enrollment in enrollments:
        course = enrollment.course
        data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'price': float(course.price),
            'progress': enrollment.progress,
            'thumbnail': course.thumbnail.url if course.thumbnail else None,
            'videos_count': course.video_count(),
            'pdfs_count': course.pdf_count(),
            'enrolled_at': enrollment.enrolled_at.strftime('%Y-%m-%d'),
            'access_expires_at': enrollment.access_expires_at.strftime('%Y-%m-%d %H:%M') if enrollment.access_expires_at else None,
            'expires_in': enrollment.time_until_expiry(),
            'is_expired': enrollment.is_access_expired(),
        })
    
    return JsonResponse(data, safe=False)

@login_required
def api_user_videos(request):
    """Get user's videos"""
    user = request.user
    
    # Get purchased videos
    purchased = UserVideoAccess.objects.filter(user=user).select_related('video')
    purchased_data = []
    for access in purchased:
        v = access.video
        purchased_data.append({
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'thumbnail': v.thumbnail.url if v.thumbnail else None,
            'category': v.category,
            'duration': v.duration,
            'price': float(v.price),
            'unlocked_at': access.unlocked_at.strftime('%Y-%m-%d'),
            'has_access': True,
            'is_free': v.price == 0,
            'view_count': v.view_count,
            'allow_download': v.allow_download,  # Add this flag for template
        })
    
    # Get free videos
    free = TrainingVideo.objects.filter(price=0, is_active=True).exclude(
        id__in=[a.video.id for a in purchased]
    )
    free_data = []
    for v in free:
        free_data.append({
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'thumbnail': v.thumbnail.url if v.thumbnail else None,
            'category': v.category,
            'duration': v.duration,
            'price': 0,
            'has_access': True,
            'is_free': True,
            'view_count': v.view_count,
            'allow_download': v.allow_download,  # Add this flag for template
        })
    
    return JsonResponse({
        'purchased': purchased_data,
        'free': free_data,
    })

@login_required
def api_user_pdfs(request):
    """Get user's PDFs - FOR VIEWING"""
    user = request.user
    
    # Get purchased PDFs
    purchased = UserPDFAccess.objects.filter(user=user).select_related('pdf')
    purchased_data = []
    for access in purchased:
        p = access.pdf
        purchased_data.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'cover_image': p.cover_image.url if p.cover_image else None,
            'pages': p.pages,
            'file_size': p.file_size,
            'category': p.category,
            'price': float(p.price),
            'unlocked_at': access.unlocked_at.strftime('%Y-%m-%d'),
            'has_access': True,
            'is_free': p.is_free,
            'viewed': access.viewed,
            'view_count': access.view_count,
            'last_viewed': access.last_viewed.strftime('%Y-%m-%d %H:%M') if access.last_viewed else None,
        })
    
    # Get free PDFs
    free = PDF.objects.filter(is_free=True, is_active=True).exclude(
        id__in=[a.pdf.id for a in purchased]
    )
    free_data = []
    for p in free:
        free_data.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'cover_image': p.cover_image.url if p.cover_image else None,
            'pages': p.pages,
            'file_size': p.file_size,
            'category': p.category,
            'price': 0,
            'has_access': True,
            'is_free': True,
            'viewed': False,
            'view_count': 0,
        })
    
    return JsonResponse({
        'purchased': purchased_data,
        'free': free_data,
    })

@login_required
@csrf_exempt
def api_course_enroll(request):
    """Enroll in a course"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    course_id = data.get('course_id')
    if not course_id:
        return JsonResponse({'error': 'Course ID required'}, status=400)
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)
    
    user = request.user
    
    # Check if already enrolled
    existing = UserCourse.objects.filter(user=user, course=course).first()
    if existing:
        if existing.is_access_expired():
            # Reactivate expired enrollment
            existing.access_expires_at = timezone.now() + timedelta(days=365)  # 1 YEAR
            existing.is_active = True
            existing.save()
            return JsonResponse({
                'success': True,
                'message': 'Course access renewed for 1 year',
                'course_id': course.id,
                'expires_in': existing.time_until_expiry()
            })
        return JsonResponse({'error': 'Already enrolled in this course'}, status=400)
    
    # If course is free, enroll directly
    if course.price == 0:
        enrollment = UserCourse.objects.create(
            user=user,
            course=course,
            purchase_type='1_month',
            access_expires_at=timezone.now() + timedelta(days=365)  # 1 YEAR
        )
        
        # Grant access to all videos and PDFs
        enrollment.get_video_access()
        enrollment.get_pdf_access()
        
        # Log activity
        log_activity(user, 'COURSE_ENROLLED', f'Enrolled in free course: {course.title}', request)
        
        # Create notification
        Notification.objects.create(
            user=user,
            title='Course Enrolled',
            message=f'You have successfully enrolled in {course.title} for 1 year',
            notification_type='SUCCESS',
            related_object_type='course',
            related_object_id=course.id
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully enrolled in course for 1 year',
            'course_id': course.id,
            'expires_in': enrollment.time_until_expiry()
        })
    else:
        # Paid course - redirect to payment
        return JsonResponse({
            'success': False,
            'requires_payment': True,
            'message': 'This course requires payment',
            'redirect_url': f'/payment/initiate/?type=course&id={course.id}'
        }, status=400)

@login_required
def api_watchlist_count(request):
    """Get watchlist count"""
    user = request.user
    count = Watchlist.objects.filter(user=user).count()
    return JsonResponse({'count': count})

@login_required
@csrf_exempt
def api_watchlist_check(request):
    """Check if item is in watchlist"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    content_type = data.get('type')
    content_id = data.get('id')
    
    if not content_type or not content_id:
        return JsonResponse({'error': 'Type and ID required'}, status=400)
    
    user = request.user
    exists = Watchlist.objects.filter(
        user=user,
        content_type=content_type,
        content_id=content_id
    ).exists()
    
    return JsonResponse({'in_watchlist': exists})

@login_required
@csrf_exempt
def api_watchlist_add(request):
    """Add item to watchlist"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    content_type = data.get('type')
    content_id = data.get('id')
    
    if not content_type or not content_id:
        return JsonResponse({'error': 'Type and ID required'}, status=400)
    
    valid_types = ['video', 'pdf', 'course', 'package']
    if content_type not in valid_types:
        return JsonResponse({'error': 'Invalid type'}, status=400)
    
    user = request.user
    
    # Check if already in watchlist
    existing = Watchlist.objects.filter(
        user=user,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if existing:
        return JsonResponse({'error': 'Item already in watchlist'}, status=400)
    
    # Verify item exists
    obj = None
    if content_type == 'video':
        obj = TrainingVideo.objects.filter(id=content_id).first()
    elif content_type == 'pdf':
        obj = PDF.objects.filter(id=content_id).first()
    elif content_type == 'course':
        obj = Course.objects.filter(id=content_id).first()
    elif content_type == 'package':
        obj = Package.objects.filter(id=content_id).first()
    
    if not obj:
        return JsonResponse({'error': 'Item not found'}, status=404)
    
    # Add to watchlist
    watchlist_item = Watchlist.objects.create(
        user=user,
        content_type=content_type,
        content_id=content_id
    )
    
    # Log activity
    log_activity(user, 'WATCHLIST_ADD', f'Added to watchlist: {obj.title}', request)
    
    return JsonResponse({
        'success': True,
        'id': watchlist_item.id,
        'message': 'Added to watchlist'
    })

@login_required
@csrf_exempt
def api_watchlist_remove(request):
    """Remove item from watchlist"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    content_type = data.get('type')
    content_id = data.get('id')
    
    if not content_type or not content_id:
        return JsonResponse({'error': 'Type and ID required'}, status=400)
    
    deleted = Watchlist.objects.filter(
        user=request.user,
        content_type=content_type,
        content_id=content_id
    ).delete()
    
    if deleted[0] > 0:
        return JsonResponse({'success': True, 'message': 'Removed from watchlist'})
    else:
        return JsonResponse({'error': 'Item not found in watchlist'}, status=404)

@login_required
def api_watchlist(request):
    """Get user's watchlist with item details"""
    user = request.user
    watchlist = Watchlist.objects.filter(user=user).order_by('-created_at')
    
    data = []
    for item in watchlist:
        content = item.get_content()
        if content:
            data.append({
                'id': item.id,
                'content_id': item.content_id,
                'type': item.content_type,
                'title': getattr(content, 'title', str(content)),
                'price': float(getattr(content, 'price', 0)),
                'added_at': item.created_at.strftime('%Y-%m-%d'),
            })
    
    return JsonResponse(data, safe=False)

@login_required
def api_user_communities(request):
    """Get user's community memberships"""
    user = request.user
    memberships = UserCommunityMembership.objects.filter(user=user).select_related('community')
    
    data = []
    for m in memberships:
        data.append({
            'id': m.id,
            'community_id': m.community.id,
            'community_name': m.community.name,
            'community_tier': m.community.tier,
            'status': m.status,
            'joined_at': m.joined_at.strftime('%Y-%m-%d'),
            'access_granted': m.access_granted,
            'discord_username': m.discord_username,
            'telegram_username': m.telegram_username,
        })
    
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def api_community_join(request):
    """Request to join a community tier"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    tier = data.get('tier')
    if not tier:
        return JsonResponse({'error': 'Tier required'}, status=400)
    
    try:
        community = CommunityTier.objects.get(tier=tier, is_active=True)
    except CommunityTier.DoesNotExist:
        return JsonResponse({'error': 'Community tier not found'}, status=404)
    
    user = request.user
    
    # Check if already a member
    existing = UserCommunityMembership.objects.filter(user=user, community=community).first()
    if existing:
        return JsonResponse({
            'error': f'You already have a {existing.status} membership for this community'
        }, status=400)
    
    # Check for pending request
    pending = CommunityJoinRequest.objects.filter(
        user=user, community=community, status='pending'
    ).exists()
    if pending:
        return JsonResponse({'error': 'You already have a pending request'}, status=400)
    
    # Check eligibility
    eligible, missing = community.check_user_eligibility(user)
    
    if not eligible and community.tier != 'citizens':
        return JsonResponse({
            'error': 'You do not meet the requirements',
            'missing': missing
        }, status=403)
    
    if community.tier == 'citizens':
        # Instant access for citizens
        membership = UserCommunityMembership.objects.create(
            user=user,
            community=community,
            status='active',
            access_granted=True,
            access_granted_at=timezone.now()
        )
        
        log_activity(user, 'COMMUNITY_JOINED', f'Joined {community.name}', request)
        
        return JsonResponse({
            'success': True,
            'status': 'active',
            'message': f'Welcome to {community.name}!'
        })
    else:
        # Create join request for paid tiers
        join_request = CommunityJoinRequest.objects.create(
            user=user,
            community=community,
            met_requirements=eligible,
            investment_at_request=user.total_deposits,
            courses_completed=list(UserCourse.objects.filter(user=user).values_list('course_id', flat=True))
        )
        
        # Send email to admin
        send_community_application_email(user, community, request)
        
        log_activity(user, 'COMMUNITY_REQUEST', f'Requested to join {community.name}', request)
        
        return JsonResponse({
            'success': True,
            'status': 'pending',
            'message': 'Your request has been submitted for review'
        })

@login_required
def api_institute_eligibility(request):
    """Check user's eligibility for Institute account"""
    user = request.user
    
    # Check requirements
    invest_met = user.total_deposits >= 250000
    ptm_course = UserCourse.objects.filter(
        user=user, 
        course__title__icontains='PTM'
    ).exists()
    
    # Account age in days
    account_age = (timezone.now() - user.date_joined).days
    age_met = account_age >= 30
    
    # Check for existing application
    existing_application = InstituteApplication.objects.filter(
        user=user, 
        status__in=['pending', 'approved']
    ).first()
    
    data = {
        'total_deposits': float(user.total_deposits),
        'has_ptm_course': ptm_course,
        'account_age_days': account_age,
        'meets_investment': invest_met,
        'meets_ptm': ptm_course,
        'meets_age': age_met,
        'eligible': invest_met and ptm_course and age_met,
        'has_application': existing_application is not None,
        'application_status': existing_application.status if existing_application else None
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
def api_institute_apply(request):
    """Submit institute application"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    
    # Check if already applied
    existing = InstituteApplication.objects.filter(
        user=user, 
        status__in=['pending', 'approved']
    ).first()
    if existing:
        return JsonResponse({
            'error': f'You already have a {existing.status} application'
        }, status=400)
    
    # Get form data
    amount = request.POST.get('amount')
    experience = request.POST.get('experience')
    notes = request.POST.get('notes', '')
    
    if not amount or not experience:
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    try:
        amount = Decimal(amount)
    except:
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    if amount < 250000:
        return JsonResponse({'error': 'Minimum investment is $250,000'}, status=400)
    
    proof_file = request.FILES.get('proof_of_funds')
    if not proof_file:
        return JsonResponse({'error': 'Proof of funds is required'}, status=400)
    
    # Create application
    application = InstituteApplication(
        user=user,
        investment_amount=amount,
        trading_experience=experience,
        notes=notes,
        proof_of_funds=proof_file
    )
    
    history_file = request.FILES.get('trading_history')
    if history_file:
        application.trading_history = history_file
    
    application.save()
    
    # Send email to admin
    send_institute_application_email(application)
    
    log_activity(user, 'INSTITUTE_APPLY', 'Submitted institute application', request)
    
    return JsonResponse({
        'success': True,
        'message': 'Application submitted successfully'
    })

@login_required
def api_get_packages(request):
    """Get available packages (JSON)"""
    packages = Package.objects.filter(is_active=True).order_by('order')
    data = []
    for pkg in packages:
        data.append({
            'id': pkg.id,
            'name': pkg.name,
            'package_type': pkg.package_type,
            'short_description': pkg.short_description,
            'price': float(pkg.price),
            'original_price': float(pkg.original_price) if pkg.original_price else None,
            'discount_percentage': pkg.discount_percentage,
            'features': pkg.features,
            'benefits': pkg.benefits,
            'duration_days': pkg.duration_days,
            'is_featured': pkg.is_featured,
            'is_popular': pkg.is_popular,
            'is_recurring': pkg.is_recurring,
        })
    return JsonResponse(data, safe=False)

@login_required
def api_unlock_video(request):
    """API to unlock/purchase video"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    video_id = data.get('video_id')
    video = get_object_or_404(TrainingVideo, id=video_id)
    
    # Convert USD to KES for storage
    amount_usd = video.price
    amount_kes = amount_usd * Decimal('129')
    
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        reference=generate_reference(),
        amount=amount_kes,  # Store KES
        currency='KES',
        payment_type='video_purchase',
        payment_method='paystack',
        description=f'Purchase video: {video.title}',
        metadata={
            'video_id': video.id, 
            'video_title': video.title,
            'amount_usd': float(amount_usd)
        },
        status='pending'
    )
    
    return JsonResponse({
        'success': True,
        'reference': transaction.reference,
        'amount': float(amount_kes),  # Return KES for Paystack
        'currency': 'KES',
        'authorization_url': f"/payment/verify/{transaction.reference}/"
    })

@login_required
def api_send_support(request):
    """API to send support message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    ticket = SupportTicket.objects.create(
        user=request.user,
        subject=data.get('subject', 'Support Request'),
        message=data.get('message', ''),
        category='support',
        priority='medium'
    )
    
    return JsonResponse({
        'success': True,
        'ticket_id': ticket.id,
        'ticket_number': ticket.ticket_number
    })

@login_required
def api_update_settings(request):
    """API to update user settings"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user
    
    if 'notifications' in data:
        user.notification_preferences = data['notifications']
    
    if 'privacy' in data:
        user.privacy_settings = data['privacy']
    
    user.save()
    
    return JsonResponse({'success': True})

@login_required
def api_user_orders(request):
    """Get user orders (JSON)"""
    user = request.user
    orders = PaymentTransaction.objects.filter(user=user).order_by('-created_at')[:20]
    
    data = []
    for order in orders:
        data.append({
            'reference': order.reference,
            'amount': float(order.amount),
            'currency': order.currency,
            'payment_type': order.payment_type,
            'payment_method': order.payment_method,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'paid_at': order.paid_at.strftime('%Y-%m-%d') if order.paid_at else None,
        })
    
    return JsonResponse(data, safe=False)

@login_required
def api_user_tickets(request):
    """Get user support tickets (JSON)"""
    user = request.user
    tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')[:20]
    
    data = []
    for ticket in tickets:
        data.append({
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'subject': ticket.subject,
            'category': ticket.category,
            'priority': ticket.priority,
            'status': ticket.status,
            'reply_count': ticket.reply_count,
            'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse(data, safe=False)

@login_required
def api_create_order(request):
    """Create a new order (JSON)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Get USD amount and convert to KES
    amount_usd = Decimal(str(data.get('amount', 0)))
    amount_kes = amount_usd * Decimal('129')
    
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        reference=generate_reference(),
        amount=amount_kes,  # Store KES
        currency='KES',
        payment_type=data.get('payment_type', 'other'),
        payment_method=data.get('payment_method', 'paystack'),
        description=data.get('description', ''),
        metadata={
            **data.get('metadata', {}),
            'amount_usd': float(amount_usd)
        },
        status='initiated',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return JsonResponse({
        'success': True,
        'reference': transaction.reference,
        'amount': float(amount_kes),  # Return KES for Paystack
        'currency': 'KES',
        'authorization_url': f"/payment/verify/{transaction.reference}/",
    })

@login_required
def api_create_ticket(request):
    """Create support ticket (JSON)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    ticket = SupportTicket.objects.create(
        user=request.user,
        subject=data.get('subject'),
        message=data.get('message'),
        category=data.get('category', 'general'),
        priority=data.get('priority', 'medium'),
    )
    
    # Send notification to admin
    send_ticket_notification_email(ticket, is_new=True)
    
    log_activity(request.user, 'SUPPORT_TICKET_CREATED', f'Created ticket: {ticket.subject[:50]}', request)
    
    return JsonResponse({
        'success': True,
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
    })

@login_required
def api_check_email(request):
    """Check if email exists (for registration)"""
    email = request.GET.get('email', '')
    exists = MfalmeUsers.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

@login_required
def api_check_username(request):
    """Check if username exists"""
    username = request.GET.get('username', '')
    exists = MfalmeUsers.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

@login_required
@csrf_exempt
def api_profile_update(request):
    """Update user profile (JSON)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    user = request.user
    
    # Update allowed fields
    allowed_fields = ['first_name', 'last_name', 'phone', 'country', 'city', 
                      'whatsapp_number', 'telegram_username', 'bio']
    
    changes = []
    for field in allowed_fields:
        if field in data:
            old_value = getattr(user, field)
            new_value = data[field]
            if str(old_value) != str(new_value):
                setattr(user, field, new_value)
                changes.append(field)
    
    if changes:
        user.save()
        log_activity(user, 'PROFILE_UPDATE', f'Updated profile fields: {", ".join(changes)}', request)
    
    return JsonResponse({
        'success': True,
        'updated_fields': changes
    })

@login_required
@csrf_exempt
def api_password_change(request):
    """Change user password (JSON)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    current = data.get('current_password')
    new = data.get('new_password')
    
    if not current or not new:
        return JsonResponse({'error': 'Current and new password required'}, status=400)
    
    user = request.user
    
    if not user.check_password(current):
        return JsonResponse({'error': 'Current password is incorrect'}, status=400)
    
    if len(new) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)
    
    user.set_password(new)
    user.password_changed_at = timezone.now()
    user.save(update_fields=['password', 'password_changed_at'])
    
    log_activity(user, 'PASSWORD_CHANGE', 'Password changed', request)
    
    # Re-authenticate to maintain session
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, user)
    
    return JsonResponse({'success': True})

@login_required
def api_ticket_detail(request, ticket_id):
    """Get ticket details with replies"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    replies = ticket.replies.select_related('user').order_by('created_at')
    
    reply_data = []
    for reply in replies:
        reply_data.append({
            'id': reply.id,
            'message': reply.message,
            'is_admin': reply.user.is_staff,
            'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            'time_ago': timesince(reply.created_at),
        })
    
    data = {
        'id': ticket.id,
        'ticket_number': ticket.ticket_number,
        'subject': ticket.subject,
        'message': ticket.message,
        'category': ticket.category,
        'priority': ticket.priority,
        'status': ticket.status,
        'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
        'replies': reply_data,
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
def api_ticket_reply(request, ticket_id):
    """Reply to a ticket"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    message = data.get('message')
    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    
    reply = TicketReply.objects.create(
        ticket=ticket,
        user=request.user,
        message=message,
        is_internal=False
    )
    
    ticket.status = 'waiting_reply'
    ticket.reply_count += 1
    ticket.last_reply_at = timezone.now()
    ticket.save(update_fields=['status', 'reply_count', 'last_reply_at'])
    
    # Notify admin
    send_ticket_notification_email(ticket, is_new=False)
    
    return JsonResponse({
        'success': True,
        'id': reply.id,
        'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M')
    })

# ==================== PUBLIC API ENDPOINTS ====================

def api_public_videos(request):
    """Get all public videos with course information"""
    videos = TrainingVideo.objects.filter(is_active=True).select_related('course').order_by('-created_at')
    
    data = []
    for v in videos:
        data.append({
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'thumbnail': v.thumbnail.url if v.thumbnail else None,
            'category': v.category,
            'duration': v.duration,
            'price': float(v.price),
            'view_count': v.view_count,
            'course_id': v.course.id if v.course else None,
            'course_name': v.course.title if v.course else 'Standalone Video',
            'allow_download': v.allow_download,  # Add this flag
        })
    
    return JsonResponse(data, safe=False)

def api_public_pdfs(request):
    """Get all public PDFs with course information"""
    pdfs = PDF.objects.filter(is_active=True).select_related('course').order_by('-created_at')
    
    data = []
    for p in pdfs:
        data.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'cover_image': p.cover_image.url if p.cover_image else None,
            'pages': p.pages,
            'file_size': p.file_size,
            'category': p.category,
            'price': float(p.price),
            'is_free': p.is_free,
            'views': p.views,
            'course_id': p.course.id if p.course else None,
            'course_name': p.course.title if p.course else 'Standalone PDF',
        })
    
    return JsonResponse(data, safe=False)

def api_public_blogs(request):
    """Get published blogs (no login required)"""
    blogs = Blog.objects.filter(status='published').order_by('-published_at')[:10]
    
    data = []
    for blog in blogs:
        data.append({
            'id': blog.id,
            'title': blog.title,
            'slug': blog.slug,
            'excerpt': blog.excerpt,
            'author': blog.author.username if blog.author else 'Admin',
            'category': blog.category,
            'featured_image': blog.featured_image.url if blog.featured_image else None,
            'published_at': blog.published_at.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse(data, safe=False)

def api_public_testimonials(request):
    """Get testimonials (no login required)"""
    testimonials = Testimonial.objects.filter(is_active=True, is_featured=True)[:10]
    
    data = []
    for t in testimonials:
        data.append({
            'id': t.id,
            'name': t.name,
            'title': t.title,
            'company': t.company,
            'content': t.content,
            'rating': t.rating,
            'image': t.image.url if t.image else None,
            'program': t.program,
        })
    
    return JsonResponse(data, safe=False)

def api_public_faqs(request):
    """Get FAQs (no login required)"""
    category = request.GET.get('category', '')
    
    faqs = FAQ.objects.filter(is_active=True)
    if category:
        faqs = faqs.filter(category=category)
    
    faqs = faqs.order_by('category', 'order')[:50]
    
    data = []
    for faq in faqs:
        data.append({
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'category': faq.category,
        })
    
    return JsonResponse(data, safe=False)

def api_public_courses(request):
    """Get all active courses (public)"""
    courses = Course.objects.filter(is_active=True).order_by('-created_at')
    
    data = []
    for course in courses:
        data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'price': float(course.price),
            'thumbnail': course.thumbnail.url if course.thumbnail else None,
            'duration_weeks': course.duration_weeks,
            'videos_count': course.video_count(),
            'pdfs_count': course.pdf_count(),
            'category': 'Course',
        })
    
    return JsonResponse(data, safe=False)

def api_public_community_tiers(request):
    """Get all community tiers (public)"""
    tiers = CommunityTier.objects.filter(is_active=True).order_by('order')
    
    data = []
    for tier in tiers:
        data.append({
            'id': tier.id,
            'name': tier.name,
            'tier': tier.tier,
            'description': tier.description,
            'features': tier.features,
            'icon_class': tier.icon_class,
            'badge_text': tier.badge_text,
            'color_scheme': tier.color_scheme,
            'button_text': tier.button_text,
            'minimum_investment': float(tier.minimum_investment) if tier.minimum_investment else None,
            'requirements': tier.requirements,
        })
    
    return JsonResponse(data, safe=False)

def api_blog_detail(request, blog_id):
    """Get blog details (public)"""
    blog = get_object_or_404(Blog, id=blog_id, status='published')
    
    blog.views += 1
    blog.save(update_fields=['views'])
    
    data = {
        'id': blog.id,
        'title': blog.title,
        'slug': blog.slug,
        'content': blog.content,
        'excerpt': blog.excerpt,
        'author': blog.author.username if blog.author else 'Admin',
        'category': blog.category,
        'tags': blog.tags.split(',') if blog.tags else [],
        'featured_image': blog.featured_image.url if blog.featured_image else None,
        'views': blog.views,
        'read_time': blog.read_time,
        'published_at': blog.published_at.strftime('%Y-%m-%d') if blog.published_at else None,
        'meta_title': blog.meta_title,
        'meta_description': blog.meta_description,
    }
    
    return JsonResponse(data)

# ==================== PDF VIEWING API ENDPOINT ====================

@login_required
def api_pdf_view(request, pdf_id):
    """API endpoint to get PDF viewing URL - FOR VIEWING ONLY"""
    try:
        pdf = PDF.objects.get(id=pdf_id, is_active=True)
    except PDF.DoesNotExist:
        return JsonResponse({'error': 'PDF not found'}, status=404)
    
    user = request.user
    
    # Check access
    has_access = check_pdf_access(user, pdf)
    
    if not has_access:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if not pdf.pdf_file or not pdf.pdf_file.storage.exists(pdf.pdf_file.name):
        return JsonResponse({'error': 'PDF file not found'}, status=404)
    
    # Update access record
    access, created = UserPDFAccess.objects.get_or_create(
        user=user,
        pdf=pdf,
        defaults={'payment': None}
    )
    access.viewed = True
    access.view_count += 1
    access.last_viewed = timezone.now()
    access.save(update_fields=['viewed', 'view_count', 'last_viewed'])
    
    # Update PDF view count
    pdf.views += 1
    pdf.save(update_fields=['views'])
    
    # Log activity
    log_activity(
        user,
        'PDF_VIEWED',
        f'Viewed PDF: {pdf.title}',
        request
    )
    
    # Return the URL for viewing (inline, not attachment)
    return JsonResponse({
        'success': True,
        'view_url': pdf.pdf_file.url,
        'title': pdf.title,
        'pages': pdf.pages,
        'file_size': pdf.file_size
    })

# ==================== FIXED PAYMENT VIEWS ====================

@login_required
def initiate_payment(request):
    """Initiate payment page - NOW WITH USD -> KES CONVERSION"""
    package_type = request.GET.get('type')
    package_id = request.GET.get('id')
    
    context = {
        'package_type': package_type,
        'package_id': package_id,
        'user': request.user,
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
    }
    
    item = None
    amount_usd = 0
    amount_kes = 0
    title = ''
    
    if package_type == 'video' and package_id:
        try:
            item = TrainingVideo.objects.get(id=package_id)
            amount_usd = float(item.price)
            amount_kes = amount_usd * 129
            title = item.title
        except TrainingVideo.DoesNotExist:
            pass
    elif package_type == 'course' and package_id:
        try:
            item = Course.objects.get(id=package_id)
            amount_usd = float(item.price)
            amount_kes = amount_usd * 129
            title = item.title
        except Course.DoesNotExist:
            pass
    elif package_type == 'pdf' and package_id:
        try:
            item = PDF.objects.get(id=package_id)
            amount_usd = float(item.price)
            amount_kes = amount_usd * 129
            title = item.title
        except PDF.DoesNotExist:
            pass
    elif package_type == 'package' and package_id:
        try:
            item = Package.objects.get(id=package_id)
            amount_usd = float(item.price)
            amount_kes = amount_usd * 129
            title = item.name
        except Package.DoesNotExist:
            pass
    
    context['item'] = item
    context['amount'] = amount_usd
    context['amount_usd'] = amount_usd
    context['amount_kes'] = amount_kes
    context['title'] = title
    
    # Create transaction
    if item and amount_usd > 0:
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            reference=generate_reference(),
            amount=Decimal(str(amount_kes)),  # Store KES
            currency='KES',
            payment_type=f'{package_type}_purchase',
            payment_method='paystack',
            description=f'Purchase: {title}',
            metadata={
                'item_type': package_type,
                'item_id': package_id,
                'item_title': title,
                'amount_usd': amount_usd
            },
            status='initiated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        context['transaction'] = transaction
        context['reference'] = transaction.reference
    
    return render(request, 'payment/initiate_payment.html', context)

@login_required
def process_payment(request):
    """Process payment (AJAX) - NOW WITH USD -> KES CONVERSION"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Get USD amount from request
    amount_usd = Decimal(str(data.get('amount', 0)))
    
    # Convert to KES (multiply by 129)
    amount_kes = amount_usd * Decimal('129')
    
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        reference=generate_reference(),
        amount=amount_kes,  # Store KES
        currency='KES',
        payment_type=data.get('payment_type', 'other'),
        payment_method='paystack',
        description=data.get('description', ''),
        metadata={
            'item_type': data.get('item_type'),
            'item_id': data.get('item_id'),
            'item_name': data.get('item_name'),
            'amount_usd': float(amount_usd)
        },
        status='pending',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Return KES amount to frontend
    return JsonResponse({
        'success': True,
        'reference': transaction.reference,
        'amount': float(amount_kes),  # Send KES to Paystack
        'currency': 'KES',
        'email': request.user.email,
        'authorization_url': f"/payment/verify/{transaction.reference}/",
    })

def verify_payment(request, reference):
    """Verify payment after redirect"""
    transaction = get_object_or_404(PaymentTransaction, reference=reference)
    
    if transaction.status == 'pending':
        transaction.status = 'completed'
        transaction.paid_at = timezone.now()
        transaction.completed_at = timezone.now()
        transaction.save(update_fields=['status', 'paid_at', 'completed_at'])
        
        if transaction.user:
            user = transaction.user
            user.total_deposits += transaction.amount
            user.account_balance += transaction.amount
            user.save(update_fields=['total_deposits', 'account_balance'])
            
            metadata = transaction.metadata
            if metadata and metadata.get('item_type') == 'video':
                video_id = metadata.get('item_id')
                try:
                    video = TrainingVideo.objects.get(id=video_id)
                    grant_video_access(user, video, transaction)
                except TrainingVideo.DoesNotExist:
                    pass
            elif metadata and metadata.get('item_type') == 'course':
                course_id = metadata.get('item_id')
                try:
                    course = Course.objects.get(id=course_id)
                    enrollment = UserCourse.objects.create(
                        user=user,
                        course=course,
                        payment=transaction,
                        access_expires_at=timezone.now() + timedelta(days=365)  # 1 YEAR
                    )
                    enrollment.get_video_access()
                    enrollment.get_pdf_access()
                    
                    Notification.objects.create(
                        user=user,
                        title='Course Access Granted',
                        message=f'You now have 1 year access to {course.title}',
                        notification_type='SUCCESS',
                        related_object_type='course',
                        related_object_id=course.id
                    )
                except Course.DoesNotExist:
                    pass
            elif metadata and metadata.get('item_type') == 'pdf':
                pdf_id = metadata.get('item_id')
                try:
                    pdf = PDF.objects.get(id=pdf_id)
                    grant_pdf_access(user, pdf, transaction)
                except PDF.DoesNotExist:
                    pass
            elif metadata and metadata.get('item_type') == 'package':
                package_id = metadata.get('item_id')
                # Handle package purchase logic here
                pass
            
            # Get USD amount from metadata for display
            amount_usd = metadata.get('amount_usd', float(transaction.amount / Decimal('129'))) if metadata else float(transaction.amount / Decimal('129'))
            
            Notification.objects.create(
                user=user,
                title='Payment Successful',
                message=f'Your payment of ${amount_usd:.2f} was successful. Reference: {reference}',
                notification_type='SUCCESS',
                related_object_type='payment',
                related_object_id=transaction.id,
            )
            
            log_activity(user, 'PAYMENT_COMPLETED', f'Payment completed: ${amount_usd:.2f} (KES {transaction.amount})', request)
        
        messages.success(request, 'Payment successful!')
    
    return redirect('payment_success', reference=reference)

def payment_success(request, reference):
    """Payment success page"""
    transaction = get_object_or_404(PaymentTransaction, reference=reference)
    # Calculate USD amount for display
    amount_usd = float(transaction.amount / Decimal('129'))
    
    # Get item details from metadata
    item_name = 'Purchase'
    item_type = ''
    item_id = ''
    if transaction.metadata:
        item_name = transaction.metadata.get('item_title', transaction.metadata.get('item_name', 'Purchase'))
        item_type = transaction.metadata.get('item_type', '')
        item_id = transaction.metadata.get('item_id', '')
    
    context = {
        'transaction': transaction,
        'amount_usd': amount_usd,
        'amount': amount_usd,
        'item_name': item_name,
        'item_type': item_type,
        'item_id': item_id,
        'order_id': reference,
        'payment_date': transaction.paid_at.strftime('%B %d, %Y') if transaction.paid_at else timezone.now().strftime('%B %d, %Y'),
    }
    
    return render(request, 'payment/success.html', context)

def payment_failed(request):
    """Payment failed page"""
    error_message = request.GET.get('message', 'Your payment could not be processed.')
    
    context = {
        'error_message': error_message,
    }
    
    return render(request, 'payment/failed.html', context)

@csrf_exempt
def paystack_webhook(request):
    """Paystack webhook endpoint - NOW HANDLES KES"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    
    paystack_signature = request.headers.get('X-Paystack-Signature')
    if not paystack_signature:
        return JsonResponse({'status': 'error'}, status=400)
    
    try:
        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})
        
        if event == 'charge.success':
            reference = data.get('reference')
            amount_kes = Decimal(str(data.get('amount', 0))) / 100  # Convert from cents
            
            try:
                transaction = PaymentTransaction.objects.get(reference=reference)
                if transaction.status == 'pending':
                    # Verify amount matches (within small tolerance)
                    if abs(transaction.amount - amount_kes) < Decimal('1'):
                        transaction.status = 'completed'
                        transaction.paid_at = timezone.now()
                        transaction.completed_at = timezone.now()
                        transaction.paystack_data = data
                        transaction.save()
                        
                        user = transaction.user
                        if user:
                            user.total_deposits += transaction.amount
                            user.account_balance += transaction.amount
                            user.save()
                            
                            metadata = transaction.metadata
                            if metadata and metadata.get('item_type') == 'video':
                                video_id = metadata.get('item_id')
                                try:
                                    video = TrainingVideo.objects.get(id=video_id)
                                    grant_video_access(user, video, transaction)
                                except TrainingVideo.DoesNotExist:
                                    pass
                            elif metadata and metadata.get('item_type') == 'course':
                                course_id = metadata.get('item_id')
                                try:
                                    course = Course.objects.get(id=course_id)
                                    enrollment = UserCourse.objects.create(
                                        user=user,
                                        course=course,
                                        payment=transaction
                                    )
                                    enrollment.get_video_access()
                                    enrollment.get_pdf_access()
                                except Course.DoesNotExist:
                                    pass
                            elif metadata and metadata.get('item_type') == 'pdf':
                                pdf_id = metadata.get('item_id')
                                try:
                                    pdf = PDF.objects.get(id=pdf_id)
                                    grant_pdf_access(user, pdf, transaction)
                                except PDF.DoesNotExist:
                                    pass
                            
                            amount_usd = metadata.get('amount_usd', float(amount_kes / Decimal('129'))) if metadata else float(amount_kes / Decimal('129'))
                            
                            Notification.objects.create(
                                user=user,
                                title='Payment Received',
                                message=f'Payment of ${amount_usd:.2f} confirmed.',
                                notification_type='SUCCESS',
                            )
            except PaymentTransaction.DoesNotExist:
                pass
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error'}, status=400)

# ==================== STATIC PAGES ====================

def index(request):
    """Home page"""
    context = {
        'featured_packages': Package.objects.filter(is_active=True, is_featured=True)[:3],
        'recent_blogs': Blog.objects.filter(status='published')[:3],
        'testimonials': Testimonial.objects.filter(is_active=True, is_featured=True)[:5],
        'stats': Statistic.objects.filter(is_active=True),
        'faqs': FAQ.objects.filter(is_active=True, is_featured=True)[:5],
        'total_users': MfalmeUsers.objects.filter(account_status='active').count(),
        'total_videos': TrainingVideo.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
    }
    return render(request, 'main/index.html', context)

def about(request):
    context = {
        'stats': Statistic.objects.filter(is_active=True),
        'testimonials': Testimonial.objects.filter(is_active=True)[:5],
    }
    return render(request, 'main/about.html', context)

def services(request):
    context = {
        'packages': Package.objects.filter(is_active=True),
        'education_programs': EducationProgram.objects.filter(is_active=True),
        'mentorship_programs': MentorshipProgram.objects.filter(is_available=True),
    }
    return render(request, 'main/services.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        submission = ContactSubmission.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        messages.success(request, 'Thank you for contacting us. We will get back to you soon.')
        return redirect('contact')
    
    context = {
        'faqs': FAQ.objects.filter(category='general', is_active=True)[:5],
    }
    return render(request, 'main/contact.html', context)

def payment(request):
    context = {
        'packages': Package.objects.filter(is_active=True),
        'payment_methods': ['Paystack', 'M-Pesa', 'Bitcoin', 'USDT', 'Bank Transfer'],
    }
    return render(request, 'main/payment.html', context)

def accounts(request):
    context = {
        'community_tiers': CommunityTier.objects.filter(is_active=True),
    }
    return render(request, 'main/accounts.html', context)

def partnerships(request):
    context = {
        'partnership_programs': PartnershipProgram.objects.filter(is_active=True),
        'active_partners': UserPartnership.objects.filter(status='active').count(),
        'total_investment': UserPartnership.objects.filter(status='active').aggregate(Sum('investment_amount'))['investment_amount__sum'] or 0,
    }
    return render(request, 'main/partnerships.html', context)

def education(request):
    context = {
        'programs': EducationProgram.objects.filter(is_active=True),
        'testimonials': Testimonial.objects.filter(program__in=['IPLT', 'PTM', 'POTM', 'PFTM'], is_active=True)[:5],
    }
    return render(request, 'main/education.html', context)

def mentoring(request):
    context = {
        'programs': MentorshipProgram.objects.filter(is_available=True),
        'mentors': MfalmeUsers.objects.filter(elite_rank__in=['Captain', 'Commander', 'General'], is_active=True)[:4],
    }
    return render(request, 'main/mentoring.html', context)

def community(request):
    context = {
        'tiers': CommunityTier.objects.filter(is_active=True),
        'member_count': UserCommunityMembership.objects.filter(status='active').count(),
    }
    return render(request, 'main/community.html', context)

def seminars(request):
    context = {
        'upcoming_seminars': [],
    }
    return render(request, 'main/seminars.html', context)

def faqs(request):
    category = request.GET.get('category', '')
    faqs = FAQ.objects.filter(is_active=True)
    if category:
        faqs = faqs.filter(category=category)
    faqs = faqs.order_by('category', 'order')
    
    categories = {}
    for faq in faqs:
        if faq.category not in categories:
            categories[faq.category] = []
        categories[faq.category].append(faq)
    
    context = {
        'categories': categories,
        'selected_category': category,
        'category_choices': FAQ.CATEGORY_CHOICES,
    }
    return render(request, 'main/faqs.html', context)

def booking(request):
    return render(request, 'main/booking.html', context)

# ==================== FORM SUBMISSIONS ====================

@csrf_exempt
def contact_form_submit(request):
    """Contact form submission (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False})
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})
    
    submission = ContactSubmission.objects.create(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        subject=data.get('subject', ''),
        message=data.get('message'),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return JsonResponse({'success': True})

@csrf_exempt
def submit_partnership_application(request):
    """Partnership application (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False})
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})
    
    submission = ContactSubmission.objects.create(
        name=data.get('company_name') or data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        subject='Partnership Application',
        message=json.dumps(data),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return JsonResponse({'success': True})

# ==================== TEST ENDPOINTS ====================

def test_all_emails(request):
    """Test email functionality"""
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    
    results = []
    
    code = generate_verification_code()
    result1 = send_verification_email(request.user, code)
    results.append(f"Verification email: {'✓' if result1 else '✗'}")
    
    result2 = send_password_reset_email(request.user, code)
    results.append(f"Password reset email: {'✓' if result2 else '✗'}")
    
    result3 = send_welcome_email(request.user)
    results.append(f"Welcome email: {'✓' if result3 else '✗'}")
    
    result4 = send_admin_notification(request.user)
    results.append(f"Admin notification: {'✓' if result4 else '✗'}")
    
    return HttpResponse('<br>'.join(results))

def test_smtp_connection(request):
    """Test SMTP connection"""
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    
    from django.core.mail import get_connection
    
    try:
        connection = get_connection()
        connection.open()
        connection.close()
        return HttpResponse('SMTP connection successful ✓')
    except Exception as e:
        return HttpResponse(f'SMTP connection failed: {str(e)}')

def emergency_email_fix(request):
    """Emergency email configuration fix"""
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    
    from django.conf import settings
    
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    code = generate_verification_code()
    result = send_verification_email(request.user, code)
    
    if result:
        return HttpResponse('Email sent to console. Check your terminal.')
    else:
        return HttpResponse('Email sending failed.')

# ========== PAYMENT VIEWS ==========

def pay_without_login(request):
    """Payment without login page"""
    context = {
        'packages': Package.objects.filter(is_active=True),
    }
    return render(request, 'payment/index.html', context)

def verify_guest_payment(request, reference):
    """Verify guest payment"""
    transaction = get_object_or_404(PaymentTransaction, reference=reference)
    
    context = {
        'transaction': transaction,
        'reference': reference,
    }
    
    return render(request, 'payment/verify.html', context)

def initiate_package_payment(request, package_type, amount):
    """Initiate package payment"""
    return redirect('payment')

def initiate_education_payment(request, program_type, duration):
    """Initiate education payment"""
    return redirect('payment')

def initiate_partnership_payment(request, tier):
    """Initiate partnership payment"""
    return redirect('payment')

def initiate_custom_payment(request):
    """Initiate custom payment"""
    if request.method == 'POST':
        return JsonResponse({'status': 'success'})
    return redirect('payment')

def payment_video(request, video_id):
    """Payment page for a specific video"""
    video = get_object_or_404(TrainingVideo, id=video_id, is_active=True)
    amount_kes = float(video.price) * 129
    
    # Create transaction
    transaction = None
    if request.user.is_authenticated:
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            reference=generate_reference(),
            amount=Decimal(str(amount_kes)),
            currency='KES',
            payment_type='video_purchase',
            payment_method='paystack',
            description=f'Video: {video.title}',
            metadata={
                'video_id': video.id,
                'video_title': video.title,
                'amount_usd': float(video.price)
            },
            status='initiated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
    
    context = {
        'video': video,
        'amount_usd': float(video.price),
        'amount_kes': amount_kes,
        'user': request.user if request.user.is_authenticated else None,
        'transaction': transaction,
        'reference': transaction.reference if transaction else None,
    }
    
    return render(request, 'payment/video.html', context)

def initiate_video_payment(request):
    """Initiate payment for a video"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            video = get_object_or_404(TrainingVideo, id=video_id)
            
            # Convert USD to KES
            amount_usd = video.price
            amount_kes = amount_usd * Decimal('129')
            
            transaction = PaymentTransaction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                reference=generate_reference(),
                amount=amount_kes,  # Store KES
                currency='KES',
                payment_type='video_purchase',
                payment_method='paystack',
                description=f'Video: {video.title}',
                metadata={
                    'video_id': video.id,
                    'amount_usd': float(amount_usd)
                },
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'reference': transaction.reference,
                'amount': float(amount_kes),  # Return KES for Paystack
                'currency': 'KES'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def initiate_course_payment(request):
    """Initiate payment for a course"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            
            # Convert USD to KES
            amount_usd = course.price
            amount_kes = amount_usd * Decimal('129')
            
            transaction = PaymentTransaction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                reference=generate_reference(),
                amount=amount_kes,  # Store KES
                currency='KES',
                payment_type='course_purchase',
                payment_method='paystack',
                description=f'Course: {course.title}',
                metadata={
                    'course_id': course.id,
                    'amount_usd': float(amount_usd)
                },
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'reference': transaction.reference,
                'amount': float(amount_kes),  # Return KES for Paystack
                'currency': 'KES'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def initiate_mentorship_payment(request):
    """Initiate payment for mentorship"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            program_id = data.get('program_id')
            program = get_object_or_404(MentorshipProgram, id=program_id)
            
            # Convert USD to KES
            amount_usd = program.price
            amount_kes = amount_usd * Decimal('129')
            
            transaction = PaymentTransaction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                reference=generate_reference(),
                amount=amount_kes,  # Store KES
                currency='KES',
                payment_type='mentorship_purchase',
                payment_method='paystack',
                description=f'Mentorship: {program.title}',
                metadata={
                    'program_id': program.id,
                    'amount_usd': float(amount_usd)
                },
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'reference': transaction.reference,
                'amount': float(amount_kes),  # Return KES for Paystack
                'currency': 'KES'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# ==================== COURSE PROGRESS APIS ====================

@login_required
@csrf_exempt
def api_mark_lesson_complete(request):
    """Mark lesson complete (API version) - WITH EXPIRATION CHECK"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    course_id = data.get('course_id')
    lesson_id = data.get('lesson_id')
    lesson_type = data.get('lesson_type')
    
    if not all([course_id, lesson_id, lesson_type]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    # Check access with expiration
    has_access, enrollment = check_course_access(request.user, course_id)
    
    if not has_access or not enrollment:
        return JsonResponse({'error': 'Not enrolled or access expired'}, status=403)
    
    # Mark lesson as complete
    success = enrollment.mark_lesson_complete(lesson_type, lesson_id)
    
    if not success:
        return JsonResponse({
            'success': True,
            'message': 'Lesson already completed',
            'progress': enrollment.progress,
            'completed_count': enrollment.get_completed_count(),
            'total_lessons': enrollment.get_total_lessons()
        })
    
    # Get next lesson
    next_lesson = enrollment.get_next_lesson()
    
    return JsonResponse({
        'success': True,
        'progress': enrollment.progress,
        'completed_count': enrollment.get_completed_count(),
        'total_lessons': enrollment.get_total_lessons(),
        'next_lesson': next_lesson,
        'is_complete': enrollment.progress == 100,
        'expires_in': enrollment.time_until_expiry()
    })

@login_required
def api_course_progress(request, course_id):
    """Get detailed progress for a course - WITH EXPIRATION"""
    has_access, enrollment = check_course_access(request.user, course_id)
    
    if not has_access or not enrollment:
        return JsonResponse({'error': 'Not enrolled or access expired'}, status=404)
    
    data = {
        'course_id': course_id,
        'progress': enrollment.progress,
        'completed_count': enrollment.get_completed_count(),
        'total_lessons': enrollment.get_total_lessons(),
        'remaining': enrollment.get_remaining_lessons(),
        'lessons': enrollment.get_lesson_statuses(),
        'next_lesson': enrollment.get_next_lesson(),
        'is_expired': enrollment.is_access_expired(),
        'expires_in': enrollment.time_until_expiry(),
        'days_remaining': enrollment.days_until_expiry()
    }
    
    return JsonResponse(data)

@login_required
def api_course_next_lesson(request, course_id):
    """Get next lesson for a course - WITH EXPIRATION"""
    has_access, enrollment = check_course_access(request.user, course_id)
    
    if not has_access or not enrollment:
        return JsonResponse({'error': 'Not enrolled or access expired'}, status=404)
    
    next_lesson = enrollment.get_next_lesson()
    
    if next_lesson:
        return JsonResponse({
            'has_next': True,
            'type': next_lesson['type'],
            'id': next_lesson['id'],
            'title': next_lesson['title'],
            'url': f"/{next_lesson['type']}/{next_lesson['id']}/"
        })
    else:
        return JsonResponse({
            'has_next': False,
            'message': 'Course completed!'
        })

@login_required
def api_course_reset_progress(request, course_id):
    """Reset progress for a course (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        enrollment = UserCourse.objects.get(
            user_id=request.GET.get('user_id'),
            course_id=course_id
        )
    except UserCourse.DoesNotExist:
        return JsonResponse({'error': 'Enrollment not found'}, status=404)
    
    enrollment.reset_progress()
    
    return JsonResponse({'success': True})

@login_required
def pesapal_initiate_payment(request):
    """Initiate payment with Pesapal"""
    package_type = request.GET.get('type')
    package_id = request.GET.get('id')
    
    if request.method == 'POST':
        # Get payment details from POST
        amount_usd = Decimal(request.POST.get('amount', 0))
        amount_kes = amount_usd * Decimal('129')  # Convert to KES
        phone = request.POST.get('phone', request.user.phone)
        email = request.POST.get('email', request.user.email)
        first_name = request.POST.get('first_name', request.user.first_name)
        last_name = request.POST.get('last_name', request.user.last_name)
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            reference=generate_reference(),
            amount=amount_kes,
            currency='KES',
            payment_type=package_type or 'other',
            payment_method='pesapal',
            description=f'Payment for {package_type}',
            metadata={
                'item_type': package_type,
                'item_id': package_id,
                'amount_usd': float(amount_usd)
            },
            status='initiated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Prepare Pesapal parameters
        params = {
            'pesapal_transaction_type': 'MERCHANT',
            'pesapal_merchant_reference': transaction.reference,
            'pesapal_amount': str(int(amount_kes)),  # No decimals
            'pesapal_currency': 'KES',
            'pesapal_description': transaction.description[:100],
            'pesapal_type': 'MERCHANT',
            'pesapal_first_name': first_name,
            'pesapal_last_name': last_name,
            'pesapal_email_address': email,
            'pesapal_phone_number': phone,
            'pesapal_country_code': 'KE',
        }
        
        # Get iframe URL
        iframe_url = get_pesapal_iframe_url(
            params,
            settings.PESAPAL_CONFIG['CALLBACK_URL'],
            settings.PESAPAL_CONFIG['CONSUMER_KEY'],
            settings.PESAPAL_CONFIG['CONSUMER_SECRET']
        )
        
        # Store in session
        request.session['pesapal_transaction_id'] = transaction.id
        
        return JsonResponse({
            'success': True,
            'iframe_url': iframe_url,
            'reference': transaction.reference
        })
    
    # GET request - show payment form
    context = {
        'user': request.user,
        'package_type': package_type,
        'package_id': package_id,
    }
    return render(request, 'payment/pesapal_form.html', context)

@csrf_exempt
def pesapal_callback(request):
    """Pesapal callback URL - user returns here after payment"""
    # Get parameters from Pesapal
    merchant_reference = request.GET.get('pesapal_merchant_reference')
    tracking_id = request.GET.get('pesapal_transaction_tracking_id')
    
    if not merchant_reference:
        messages.error(request, 'Invalid payment callback')
        return redirect('payment_failed')
    
    try:
        transaction = PaymentTransaction.objects.get(reference=merchant_reference)
        
        # Update transaction with tracking ID
        transaction.pesapal_tracking_id = tracking_id
        transaction.save(update_fields=['pesapal_tracking_id'])
        
        # Query payment status
        status_response = query_pesapal_status(merchant_reference, tracking_id)
        
        # Parse status (Pesapal returns "PENDING", "COMPLETED", "FAILED")
        if 'COMPLETED' in status_response:
            transaction.status = 'completed'
            transaction.paid_at = timezone.now()
            transaction.completed_at = timezone.now()
            transaction.save(update_fields=['status', 'paid_at', 'completed_at'])
            
            # Process successful payment
            process_successful_payment(transaction, request)
            
            messages.success(request, 'Payment successful!')
            return redirect('payment_success', reference=merchant_reference)
        elif 'FAILED' in status_response:
            transaction.status = 'failed'
            transaction.save(update_fields=['status'])
            messages.error(request, 'Payment failed')
            return redirect('payment_failed')
        else:
            transaction.status = 'pending'
            transaction.save(update_fields=['status'])
            messages.info(request, 'Payment is being processed')
            return redirect('payment_pending', reference=merchant_reference)
            
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Transaction not found')
        return redirect('payment_failed')

@csrf_exempt
def pesapal_ipn(request):
    """Pesapal Instant Payment Notification endpoint"""
    if request.method != 'POST':
        return HttpResponse('OK')
    
    # Get parameters from POST
    merchant_reference = request.POST.get('pesapal_merchant_reference')
    tracking_id = request.POST.get('pesapal_transaction_tracking_id')
    notification_type = request.POST.get('pesapal_notification_type')
    
    if not merchant_reference:
        return HttpResponse('OK')
    
    try:
        transaction = PaymentTransaction.objects.get(reference=merchant_reference)
        
        # Update with tracking ID
        transaction.pesapal_tracking_id = tracking_id
        
        # Query status
        status_response = query_pesapal_status(merchant_reference, tracking_id)
        
        # Store raw response
        transaction.pesapal_raw_response = {
            'notification_type': notification_type,
            'status_response': status_response
        }
        
        # Update status
        if 'COMPLETED' in status_response:
            transaction.status = 'completed'
            transaction.paid_at = timezone.now()
            transaction.completed_at = timezone.now()
        elif 'FAILED' in status_response:
            transaction.status = 'failed'
        
        transaction.save()
        
        # Process if completed
        if transaction.status == 'completed' and transaction.user:
            process_successful_payment(transaction, None)
        
    except PaymentTransaction.DoesNotExist:
        pass
    
    return HttpResponse('OK')

def process_successful_payment(transaction, request):
    """Helper function to process successful payments"""
    if not transaction.user:
        return
    
    user = transaction.user
    
    # Update user balance
    user.total_deposits += transaction.amount
    user.account_balance += transaction.amount
    user.save(update_fields=['total_deposits', 'account_balance'])
    
    # Process based on metadata
    metadata = transaction.metadata
    if metadata:
        item_type = metadata.get('item_type')
        item_id = metadata.get('item_id')
        
        if item_type == 'video':
            try:
                video = TrainingVideo.objects.get(id=item_id)
                grant_video_access(user, video, transaction)
            except TrainingVideo.DoesNotExist:
                pass
                
        elif item_type == 'course':
            try:
                course = Course.objects.get(id=item_id)
                enrollment = UserCourse.objects.create(
                    user=user,
                    course=course,
                    payment=transaction,
                    access_expires_at=timezone.now() + timedelta(days=365)  # 1 YEAR
                )
                enrollment.get_video_access()
                enrollment.get_pdf_access()
                
                Notification.objects.create(
                    user=user,
                    title='Course Access Granted',
                    message=f'You now have 1 year access to {course.title}',
                    notification_type='SUCCESS',
                    related_object_type='course',
                    related_object_id=course.id
                )
            except Course.DoesNotExist:
                pass
                
        elif item_type == 'pdf':
            try:
                pdf = PDF.objects.get(id=item_id)
                grant_pdf_access(user, pdf, transaction)
            except PDF.DoesNotExist:
                pass
    
    # Create notification
    amount_usd = metadata.get('amount_usd', float(transaction.amount / Decimal('129'))) if metadata else float(transaction.amount / Decimal('129'))
    
    Notification.objects.create(
        user=user,
        title='Payment Successful',
        message=f'Your payment of ${amount_usd:.2f} via Pesapal was successful. Reference: {transaction.reference}',
        notification_type='SUCCESS',
        related_object_type='payment',
        related_object_id=transaction.id,
    )
    
    # Log activity
    log_activity(
        user,
        'PAYMENT_COMPLETED',
        f'Payment completed via Pesapal: ${amount_usd:.2f} (KES {transaction.amount})',
        request
    )

def payment_pending(request, reference):
    """Payment pending page"""
    transaction = get_object_or_404(PaymentTransaction, reference=reference)
    context = {
        'transaction': transaction,
        'reference': reference,
    }
    return render(request, 'payment/pending.html', context)


@login_required
@csrf_exempt
def sasapay_process_payment(request):
    """Process payment with SasaPay"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    reference = data.get('reference')
    phone = data.get('phone', '254708374149')  # Default test phone
    payment_method = data.get('payment_method', 'c2b')
    
    print(f"\n{'='*50}")
    print(f"SasaPay Request: {payment_method} for {reference}")
    print(f"{'='*50}")
    
    if not reference:
        return JsonResponse({'error': 'Reference required'}, status=400)
    
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    
    from .sasapay_utils import initiate_c2b_payment, initiate_checkout
    
    amount_kes = int(transaction.amount)
    
    if payment_method == 'c2b':
        # M-PESA STK Push
        result = initiate_c2b_payment(
            phone=phone,
            amount=amount_kes,
            reference=reference,
            description=transaction.description
        )
        
        print(f"SasaPay Result: {result}")
        
        if result.get('success'):
            transaction.sasapay_transaction_id = result.get('transaction_id')
            transaction.sasapay_checkout_id = result.get('checkout_id')
            transaction.sasapay_payment_method = 'mpesa'
            transaction.sasapay_raw_response = result
            transaction.status = 'pending'
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'message': result.get('message', 'Payment initiated'),
                'transaction_id': result.get('transaction_id'),
                'mock': True  # Flag to indicate mock mode
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Payment failed')
            })
    
    elif payment_method == 'checkout':
        # Web checkout
        result = initiate_checkout(
            amount=amount_kes,
            reference=reference,
            description=transaction.description,
            email=request.user.email,
            phone=phone
        )
        
        print(f"SasaPay Result: {result}")
        
        if result.get('success'):
            transaction.sasapay_checkout_id = result.get('checkout_id')
            transaction.sasapay_payment_method = 'checkout'
            transaction.sasapay_raw_response = result
            transaction.status = 'pending'
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'checkout_url': result.get('checkout_url'),
                'message': result.get('message'),
                'mock': True  # Flag to indicate mock mode
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Checkout failed')
            })
    
    return JsonResponse({'error': 'Invalid payment method'}, status=400)

def process_successful_payment(transaction, request):
    """Process successful payment - grant access to content"""
    if not transaction.user:
        return
    
    user = transaction.user
    
    # Update user balance
    user.total_deposits += transaction.amount
    user.account_balance += transaction.amount
    user.save(update_fields=['total_deposits', 'account_balance'])
    
    # Process based on metadata
    metadata = transaction.metadata
    if metadata:
        item_type = metadata.get('item_type')
        item_id = metadata.get('item_id')
        
        if item_type == 'video':
            try:
                video = TrainingVideo.objects.get(id=item_id)
                grant_video_access(user, video, transaction)
            except TrainingVideo.DoesNotExist:
                pass
                
        elif item_type == 'course':
            try:
                course = Course.objects.get(id=item_id)
                enrollment = UserCourse.objects.create(
                    user=user,
                    course=course,
                    payment=transaction,
                    access_expires_at=timezone.now() + timedelta(days=365)  # 1 YEAR
                )
                enrollment.get_video_access()
                enrollment.get_pdf_access()
                
                Notification.objects.create(
                    user=user,
                    title='Course Access Granted',
                    message=f'You now have 1 year access to {course.title}',
                    notification_type='SUCCESS',
                    related_object_type='course',
                    related_object_id=course.id
                )
            except Course.DoesNotExist:
                pass
                
        elif item_type == 'pdf':
            try:
                pdf = PDF.objects.get(id=item_id)
                grant_pdf_access(user, pdf, transaction)
            except PDF.DoesNotExist:
                pass
    
    # Create notification
    amount_usd = metadata.get('amount_usd', float(transaction.amount / Decimal('129'))) if metadata else float(transaction.amount / Decimal('129'))
    
    Notification.objects.create(
        user=user,
        title='Payment Successful',
        message=f'Your payment of ${amount_usd:.2f} was successful. Reference: {transaction.reference}',
        notification_type='SUCCESS',
        related_object_type='payment',
        related_object_id=transaction.id,
    )
    
    # Log activity
    log_activity(
        user,
        'PAYMENT_COMPLETED',
        f'Payment completed: ${amount_usd:.2f} (KES {transaction.amount})',
        request
    )

@csrf_exempt
def sasapay_callback(request):
    """SasaPay callback endpoint - receives payment notifications"""
    if request.method == 'GET':
        # Redirect callback after checkout
        transaction_id = request.GET.get('transaction_id')
        checkout_id = request.GET.get('checkout_id')
        status = request.GET.get('status')
        
        if transaction_id:
            return redirect(f'/sasapay/verify/?transaction_id={transaction_id}')
        
        return redirect('payment_failed')
    
    elif request.method == 'POST':
        # IPN callback
        try:
            data = json.loads(request.body)
        except:
            data = request.POST.dict()
        
        transaction_id = data.get('transaction_id')
        checkout_id = data.get('checkout_id')
        status = data.get('status')
        reference = data.get('reference')
        
        if not transaction_id and not reference:
            return HttpResponse('OK')
        
        # Find transaction
        transaction = None
        if reference:
            try:
                transaction = PaymentTransaction.objects.get(reference=reference)
            except PaymentTransaction.DoesNotExist:
                pass
        
        if not transaction and transaction_id:
            try:
                transaction = PaymentTransaction.objects.get(sasapay_transaction_id=transaction_id)
            except PaymentTransaction.DoesNotExist:
                pass
        
        if transaction:
            # Update transaction
            transaction.sasapay_raw_response = data
            transaction.sasapay_status = status
            
            if status == 'COMPLETED':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                
                # Process successful payment
                process_successful_payment(transaction, request)
                
            elif status == 'FAILED':
                transaction.status = 'failed'
                transaction.save()
            
            else:
                transaction.save()
        
        return HttpResponse('OK')

def sasapay_verify(request):
    """Verify payment after redirect"""
    transaction_id = request.GET.get('transaction_id')
    
    if not transaction_id:
        return redirect('payment_failed')
    
    from .sasapay_utils import query_payment_status
    
    # Query status
    result = query_payment_status(transaction_id)
    
    if result.get('status') == 'COMPLETED':
        # Find transaction
        try:
            transaction = PaymentTransaction.objects.get(sasapay_transaction_id=transaction_id)
            if transaction.status != 'completed':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                process_successful_payment(transaction, request)
            
            return redirect('payment_success', reference=transaction.reference)
        except PaymentTransaction.DoesNotExist:
            pass
    
    return redirect('payment_failed')

def sasapay_status(request, reference):
    """Check payment status (AJAX)"""
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
        
        # If still pending, query SasaPay
        if transaction.status == 'pending' and transaction.sasapay_transaction_id:
            from .sasapay_utils import query_payment_status
            result = query_payment_status(transaction.sasapay_transaction_id)
            
            if result.get('status') == 'COMPLETED':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                process_successful_payment(transaction, None)
            elif result.get('status') == 'FAILED':
                transaction.status = 'failed'
                transaction.save()
        
        return JsonResponse({
            'status': transaction.status,
            'success_url': f'/payment/success/{reference}/' if transaction.status == 'completed' else None
        })
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)


# ==================== SASAPAY PAYMENT VIEWS ====================

@login_required
@csrf_exempt
def sasapay_process_payment(request):
    """Process payment with SasaPay"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    reference = data.get('reference')
    phone = data.get('phone')
    payment_method = data.get('payment_method', 'c2b')  # 'c2b' for M-PESA, 'checkout' for web
    
    if not reference:
        return JsonResponse({'error': 'Reference required'}, status=400)
    
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)
    
    # Import sasapay utils
    from .sasapay_utils import initiate_c2b_payment, initiate_checkout
    
    amount_kes = int(transaction.amount)  # Already in KES
    
    if payment_method == 'c2b' and phone:
        # M-PESA STK Push
        result = initiate_c2b_payment(
            phone=phone,
            amount=amount_kes,
            reference=reference,
            description=transaction.description
        )
        
        if result.get('success'):
            transaction.sasapay_transaction_id = result.get('transaction_id')
            transaction.sasapay_checkout_id = result.get('checkout_id')
            transaction.sasapay_payment_method = 'mpesa'
            transaction.sasapay_raw_response = result
            transaction.status = 'pending'
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'message': 'STK Push sent. Check your phone.',
                'transaction_id': result.get('transaction_id')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Payment failed')
            })
    
    elif payment_method == 'checkout':
        # Web checkout (card, etc.)
        result = initiate_checkout(
            amount=amount_kes,
            reference=reference,
            description=transaction.description,
            email=request.user.email,
            phone=phone
        )
        
        if result.get('success'):
            transaction.sasapay_checkout_id = result.get('checkout_id')
            transaction.sasapay_payment_method = 'checkout'
            transaction.sasapay_raw_response = result
            transaction.status = 'pending'
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'checkout_url': result.get('checkout_url'),
                'message': 'Redirecting to checkout...'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Checkout failed')
            })
    
    return JsonResponse({'error': 'Invalid payment method'}, status=400)


@csrf_exempt
def sasapay_callback(request):
    """SasaPay callback endpoint - receives payment notifications"""
    if request.method == 'GET':
        # Redirect callback after checkout
        transaction_id = request.GET.get('transaction_id')
        checkout_id = request.GET.get('checkout_id')
        status = request.GET.get('status')
        
        if transaction_id:
            return redirect(f'/sasapay/verify/?transaction_id={transaction_id}')
        
        return redirect('payment_failed')
    
    elif request.method == 'POST':
        # IPN callback
        try:
            data = json.loads(request.body)
        except:
            data = request.POST.dict()
        
        transaction_id = data.get('transaction_id')
        checkout_id = data.get('checkout_id')
        status = data.get('status')
        reference = data.get('reference')
        
        if not transaction_id and not reference:
            return HttpResponse('OK')
        
        # Find transaction
        transaction = None
        if reference:
            try:
                transaction = PaymentTransaction.objects.get(reference=reference)
            except PaymentTransaction.DoesNotExist:
                pass
        
        if not transaction and transaction_id:
            try:
                transaction = PaymentTransaction.objects.get(sasapay_transaction_id=transaction_id)
            except PaymentTransaction.DoesNotExist:
                pass
        
        if transaction:
            # Update transaction
            transaction.sasapay_raw_response = data
            transaction.sasapay_status = status
            
            if status == 'COMPLETED':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                
                # Process successful payment
                process_successful_payment(transaction, request)
                
            elif status == 'FAILED':
                transaction.status = 'failed'
                transaction.save()
            
            else:
                transaction.save()
        
        return HttpResponse('OK')


def sasapay_verify(request):
    """Verify payment after redirect"""
    transaction_id = request.GET.get('transaction_id')
    
    if not transaction_id:
        return redirect('payment_failed')
    
    from .sasapay_utils import query_payment_status
    
    # Query status
    result = query_payment_status(transaction_id)
    
    if result.get('status') == 'COMPLETED':
        # Find transaction
        try:
            transaction = PaymentTransaction.objects.get(sasapay_transaction_id=transaction_id)
            if transaction.status != 'completed':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                process_successful_payment(transaction, request)
            
            return redirect('payment_success', reference=transaction.reference)
        except PaymentTransaction.DoesNotExist:
            pass
    
    return redirect('payment_failed')


def sasapay_status(request, reference):
    """Check payment status (AJAX)"""
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
        
        # If still pending, query SasaPay
        if transaction.status == 'pending' and transaction.sasapay_transaction_id:
            from .sasapay_utils import query_payment_status
            result = query_payment_status(transaction.sasapay_transaction_id)
            
            if result.get('status') == 'COMPLETED':
                transaction.status = 'completed'
                transaction.paid_at = timezone.now()
                transaction.completed_at = timezone.now()
                transaction.save()
                process_successful_payment(transaction, None)
            elif result.get('status') == 'FAILED':
                transaction.status = 'failed'
                transaction.save()
        
        return JsonResponse({
            'status': transaction.status,
            'success_url': f'/payment/success/{reference}/' if transaction.status == 'completed' else None
        })
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)        



# ==================== ERROR HANDLERS ====================

def health_check(request):
    """Simple health check that verifies database connection"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("OK - Database connected", content_type="text/plain", status=200)
    except Exception as e:
        return HttpResponse(f"ERROR - Database: {str(e)}", content_type="text/plain", status=500)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)