from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from .models import MfalmeUsers
from datetime import datetime
import random
import string
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

# ===== EMAIL FUNCTIONS =====
def send_verification_email(user, verification_code):
    """Send verification email with the code - HANDLES MISSING TEMPLATES"""
    try:
        subject = 'Verify Your Account - MFALME BETTERDAYS CAPITAL'
        
        # Context for template
        context = {
            'username': user.username,
            'verification_code': verification_code,
            'verification_url': 'http://127.0.0.1:8000/verify-account/',
            'current_year': datetime.now().year,
        }
        
        # Try to render HTML template
        try:
            html_content = render_to_string('emails/verification_email.html', context)
        except:
            # Fallback HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h2>Verify Your Account - MFALME BETTERDAYS CAPITAL</h2>
                <p>Hello {user.username},</p>
                <p>Your verification code is: <strong>{verification_code}</strong></p>
                <p>Go to: http://127.0.0.1:8000/verify-account/</p>
                <p>This code will expire in 30 minutes.</p>
            </body>
            </html>
            """
        
        # Try to render text template
        try:
            text_content = render_to_string('emails/verification_email.txt', context)
        except:
            # Fallback text
            text_content = f"""
            Verify Your Account - MFALME BETTERDAYS CAPITAL
            
            Hello {user.username},
            
            Your verification code is: {verification_code}
            
            Go to: http://127.0.0.1:8000/verify-account/
            
            This code will expire in 30 minutes.
            """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ VERIFICATION EMAIL SENT TO: {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ VERIFICATION EMAIL FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def notify_admin_new_registration(user):
    """Send email to admin about new registration - HANDLES MISSING TEMPLATES"""
    try:
        # ⚠️ IMPORTANT: CHANGE THIS TO YOUR ACTUAL ADMIN EMAIL!
        admin_email = 'mfalmebetterdays@gmail.com'  # CHANGE THIS!
        
        subject = f'🆕 New User Registration: {user.email}'
        
        # Create simple text content
        text_content = f"""
        🆕 NEW USER REGISTRATION - MFALME BETTERDAYS CAPITAL
        
        User Details:
        ---------------
        Full Name: {user.username}
        Email: {user.email}
        Phone: {user.phone}
        Registration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Status: {'Verified' if user.email_verified else 'Pending Verification'}
        User ID: {user.id}
        
        This is an automated notification.
        """
        
        # Try to render HTML template
        try:
            context = {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_verified': user.email_verified,
                'user_id': user.id,
            }
            html_content = render_to_string('emails/admin_notification.html', context)
        except:
            # Fallback HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h2>🆕 New User Registration</h2>
                <p><strong>Name:</strong> {user.username}</p>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Phone:</strong> {user.phone}</p>
                <p><strong>ID:</strong> {user.id}</p>
                <p><strong>Status:</strong> {'Verified' if user.email_verified else 'Pending Verification'}</p>
            </body>
            </html>
            """
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ ADMIN NOTIFICATION SENT TO: {admin_email}")
        return True
        
    except Exception as e:
        print(f"❌ ADMIN NOTIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def send_welcome_email(user):
    """Send welcome email after verification - HANDLES MISSING TEMPLATES"""
    try:
        subject = f'Welcome to MFALME BETTERDAYS CAPITAL'
        
        # Create simple text content
        text_content = f"""
        Welcome to MFALME BETTERDAYS CAPITAL!
        
        Congratulations {user.username}!
        
        Your account has been successfully verified and activated.
        
        Account Details:
        - Email: {user.email}
        - Phone: {user.phone}
        - Joined: {user.date_joined.strftime('%B %d, %Y')}
        
        Access your dashboard: http://127.0.0.1:8000/dashboard/
        
        Start your trading journey today!
        """
        
        # Try to render HTML template
        try:
            context = {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'date_joined': user.date_joined.strftime('%B %d, %Y'),
                'dashboard_url': 'http://127.0.0.1:8000/dashboard/',
                'current_year': datetime.now().year,
            }
            html_content = render_to_string('emails/welcome_email.html', context)
        except:
            # Fallback HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h2>Welcome to MFALME BETTERDAYS CAPITAL!</h2>
                <p>Congratulations {user.username}!</p>
                <p>Your account has been successfully verified and activated.</p>
                <p><a href="http://127.0.0.1:8000/dashboard/">Go to Dashboard →</a></p>
            </body>
            </html>
            """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ WELCOME EMAIL SENT TO: {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ WELCOME EMAIL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ===== BASIC VIEWS =====
def index(request):
    return render(request, 'index.html')

def login_page(request):
    if 'user_id' in request.session:
        return redirect('dashboard')
    
    # Get active tab from URL or session
    active_tab = request.GET.get('tab', 'login')
    form_data = request.session.pop('form_data', {})
    
    # Get all messages
    message_list = []
    for message in messages.get_messages(request):
        message_list.append({
            'text': message.message,
            'tags': message.tags
        })
    
    return render(request, 'login.html', {
        'active_tab': active_tab,
        'form_data': form_data,
        'message_list': message_list
    })

def register_page(request):
    # Redirect to login page with signup tab
    return redirect(f'{reverse("login_page")}?tab=signup')

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        print(f"\n🔐 LOGIN ATTEMPT: {email}")
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('login_page')
        
        try:
            user = MfalmeUsers.objects.get(email=email)
            
            # Check password
            if user.password == password:
                # Check if email is verified
                if not user.email_verified:
                    # Store user ID for verification
                    request.session['pending_user_id'] = user.id
                    request.session['pending_user_email'] = user.email
                    
                    # Generate new verification code
                    verification_code = ''.join(random.choices(string.digits, k=6))
                    request.session['verification_code'] = verification_code
                    
                    # Send verification email
                    send_verification_email(user, verification_code)
                    
                    messages.error(request, 'Please verify your email first. A new verification code has been sent to your email.')
                    return redirect('verify_account_page')
                
                # Set session
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['username'] = user.username
                
                # Update last login
                user.last_login = datetime.now()
                user.save()
                
                messages.success(request, 'Login successful!')
                print(f"✅ LOGIN SUCCESS: {email}")
                return redirect('dashboard')
            else:
                print(f"❌ WRONG PASSWORD: {email}")
                messages.error(request, 'Invalid email or password.')
                return redirect('login_page')
                
        except MfalmeUsers.DoesNotExist:
            print(f"❌ USER NOT FOUND: {email}")
            messages.error(request, 'Invalid email or password.')
            return redirect('login_page')
        except Exception as e:
            print(f"❌ LOGIN ERROR: {str(e)}")
            messages.error(request, 'An error occurred during login.')
            return redirect('login_page')
    
    return redirect('login_page')


def create_account(request):
    """Handle account creation with email verification"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password1 = request.POST.get('password1', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        
        print(f"\n📝 REGISTRATION STARTED:")
        print(f"Email: {email}")
        print(f"Username: {username}")
        
        # Store form data in session to repopulate on error
        request.session['form_data'] = {
            'email': email,
            'username': username,
            'phone': phone
        }
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Full name is required.')
        
        if not email:
            errors.append('Email is required.')
        elif '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        
        if password != password1:
            errors.append('Passwords do not match.')
        
        if not phone:
            errors.append('Phone number is required.')
        
        # Check if user exists
        if MfalmeUsers.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect(f'{reverse("login_page")}?tab=signup')
        
        try:
            # Create user
            user = MfalmeUsers.objects.create(
                email=email,
                password=password,
                phone=phone,
                username=username,
                is_active=False,
                email_verified=False
            )
            
            print(f"✅ USER CREATED: ID={user.id}")
            
            # Send admin notification
            print(f"\n📧 SENDING ADMIN NOTIFICATION...")
            admin_notified = notify_admin_new_registration(user)
            if admin_notified:
                print(f"✅ ADMIN NOTIFIED")
            else:
                print(f"⚠️ ADMIN NOTIFICATION FAILED")
            
            # Clear form data from session
            if 'form_data' in request.session:
                del request.session['form_data']
            
            # Generate verification code
            verification_code = ''.join(random.choices(string.digits, k=6))
            print(f"📧 VERIFICATION CODE: {verification_code}")
            
            # Store in session
            request.session['pending_user_id'] = user.id
            request.session['pending_user_email'] = user.email
            request.session['verification_code'] = verification_code
            
            # Send verification email
            print(f"\n📧 ATTEMPTING TO SEND VERIFICATION EMAIL...")
            email_sent = send_verification_email(user, verification_code)
            
            if email_sent:
                messages.success(request, 'Registration successful! Check your email for verification code.')
                print(f"✅ VERIFICATION EMAIL SENT TO: {email}")
            else:
                messages.success(request, f'Registration successful! Your verification code: {verification_code}')
                print(f"⚠️ EMAIL FAILED, SHOWING CODE: {verification_code}")
            
            return redirect('verify_account_page')
            
        except Exception as e:
            print(f"❌ REGISTRATION ERROR: {str(e)}")
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect(f'{reverse("login_page")}?tab=signup')
    
    return redirect('login_page')


def logout_user(request):
    """Handle user logout"""
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['user_email']
        del request.session['username']
    messages.success(request, 'Logged out successfully!')
    return redirect('index')


# ===== VERIFICATION VIEWS =====
def verify_account_page(request):
    """Verification page"""
    if 'pending_user_id' not in request.session:
        messages.error(request, 'No pending verification. Please register first.')
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    user_email = request.session.get('pending_user_email', '')
    verification_code = request.session.get('verification_code', '')
    
    print(f"\n🔑 VERIFICATION PAGE ACCESSED:")
    print(f"Email: {user_email}")
    print(f"Code (for testing): {verification_code}")
    
    return render(request, 'verify_account.html', {
        'user_email': user_email,
        'verification_code': verification_code  # For testing only
    })


def verify_account_process(request):
    """Process verification code"""
    if request.method == 'POST':
        user_id = request.session.get('pending_user_id')
        entered_code = request.POST.get('verification_code', '').strip()
        
        print(f"\n🔍 VERIFICATION ATTEMPT:")
        print(f"User ID: {user_id}")
        print(f"Entered Code: {entered_code}")
        
        if not user_id:
            messages.error(request, 'Session expired. Please register again.')
            return redirect(f'{reverse("login_page")}?tab=signup')
        
        if not entered_code or len(entered_code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code.')
            return redirect('verify_account_page')
        
        try:
            user = MfalmeUsers.objects.get(id=user_id)
            stored_code = request.session.get('verification_code', '')
            
            if entered_code == stored_code:
                # Activate user
                user.is_active = True
                user.email_verified = True
                user.verified_at = datetime.now()
                user.save()
                
                # Clear pending session
                session_keys = ['pending_user_id', 'pending_user_email', 'verification_code']
                for key in session_keys:
                    if key in request.session:
                        del request.session[key]
                
                # Log user in
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['username'] = user.username
                
                print(f"✅ VERIFICATION SUCCESS: {user.email}")
                
                # Send welcome email
                send_welcome_email(user)
                
                messages.success(request, 'Account verified successfully! Welcome to MFALME BETTERDAYS CAPITAL.')
                return redirect('dashboard')
            else:
                print(f"❌ INVALID CODE: {entered_code}")
                messages.error(request, 'Invalid verification code.')
                return redirect('verify_account_page')
                
        except MfalmeUsers.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect(f'{reverse("login_page")}?tab=signup')
        except Exception as e:
            print(f"❌ VERIFICATION ERROR: {str(e)}")
            messages.error(request, 'Verification failed. Please try again.')
            return redirect('verify_account_page')
    
    return redirect('verify_account_page')


def resend_verification(request):
    """Resend verification code"""
    if request.method == 'POST':
        user_id = request.session.get('pending_user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Session expired.'
            })
        
        try:
            user = MfalmeUsers.objects.get(id=user_id)
            
            # Generate new code
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # Update session
            request.session['verification_code'] = verification_code
            
            # Send email
            email_sent = send_verification_email(user, verification_code)
            
            if email_sent:
                print(f"✅ CODE RESENT: {verification_code} to {user.email}")
                return JsonResponse({
                    'success': True,
                    'message': 'New verification code sent to your email.'
                })
            else:
                print(f"⚠️ EMAIL FAILED, CODE: {verification_code}")
                return JsonResponse({
                    'success': True,
                    'message': f'Email failed. Your new code: {verification_code}'
                })
                
        except Exception as e:
            print(f"❌ RESEND ERROR: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to resend verification code.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request.'
    })


# ===== DASHBOARD =====
def dashboard(request):
    """User dashboard"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to access dashboard.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        context = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        }
        
        return render(request, 'dashboard.html', context)
        
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login_page')


# ===== OTHER PAGES =====
def services(request):
    return render(request, 'services.html')

def contact_page(request):
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')

def partnership(request):
    return render(request, 'partnership.html')


# ===== TEST FUNCTIONS =====
def test_all_emails(request):
    """Test all email templates are working"""
    try:
        # Create a test user
        test_user = MfalmeUsers.objects.create(
            email='test@example.com',
            password='test123',
            phone='+254700000000',
            username='Test User',
            is_active=False,
            email_verified=False
        )
        
        verification_code = '123456'
        
        print(f"\n🧪 TESTING ALL EMAIL FUNCTIONS...")
        
        # Test 1: Verification Email
        print(f"1. Testing verification email...")
        verification_result = send_verification_email(test_user, verification_code)
        
        # Test 2: Admin Notification
        print(f"2. Testing admin notification...")
        admin_result = notify_admin_new_registration(test_user)
        
        # Test 3: Welcome Email
        print(f"3. Testing welcome email...")
        welcome_result = send_welcome_email(test_user)
        
        # Clean up test user
        test_user.delete()
        
        results = f"""
        Email Functions Test Results:
        -----------------------------
        1. Verification Email: {'✅ SUCCESS' if verification_result else '❌ FAILED'}
        2. Admin Notification: {'✅ SUCCESS' if admin_result else '❌ FAILED'}
        3. Welcome Email: {'✅ SUCCESS' if welcome_result else '❌ FAILED'}
        
        Check console for detailed logs.
        """
        
        return HttpResponse(results)
        
    except Exception as e:
        return HttpResponse(f"Test failed: {str(e)}")


# ===== CONTEXT PROCESSOR =====
def user_authenticated(request):
    return {
        'user_authenticated': 'user_id' in request.session,
        'user_email': request.session.get('user_email', ''),
        'username': request.session.get('username', '')
    }