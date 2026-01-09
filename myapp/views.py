# views.py - COMPLETE FILE WITH ALL FUNCTIONS AND UPDATED EMAILS
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import random
import string
import uuid
import hashlib
import requests
import json
from .models import MfalmeUsers, VerificationCode, PaymentTransaction,  TrainingVideo, UserVideoAccess, Course, UserCourse, MentorshipProgram, SupportTicket, UserActivity
from django.views.decorators.csrf import csrf_exempt
import time
import os
import logging
from django.db import models

# Setup logging
logger = logging.getLogger(__name__)

# ===== PAYSTACK PAYMENT INTEGRATION =====
try:
    from paystackapi.paystack import Paystack
    PAYSTACK_AVAILABLE = True
except ImportError:
    PAYSTACK_AVAILABLE = False
    print("⚠️ Paystack Python SDK not installed. Run: pip install paystack-python")

# ===== CORE EMAIL FUNCTIONS - UPDATED =====
def send_email_compatible(subject, html_content, text_content, recipient_list, from_email=None):
    """Send email with email client compatible HTML - GMAIL SAFE VERSION"""
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # IMPORTANT: Remove ALL emojis and special chars from subject
        import re
        import uuid
        
        # Remove emojis and special characters (Gmail hates them!)
        subject_clean = re.sub(r'[^\w\s\-.,!?@#()%&:/]', '', subject)
        subject_clean = subject_clean.strip()
        
        # Truncate if too long (Gmail displays ~60 chars)
        if len(subject_clean) > 70:
            subject_clean = subject_clean[:67] + "..."
        
        # Ensure from_email format is correct
        if '@' in from_email and '<' not in from_email:
            from_email = f"MFALME BETTERDAYS CAPITAL <{from_email}>"
        
        # GMAIL-FRIENDLY HEADERS - Avoids spam filters
        headers = {
            'X-Priority': '3',           # Changed from 1 (High) to 3 (Normal)
            'Importance': 'Normal',      # Changed from High to Normal
            'X-Mailer': 'MFALME Trading Platform v2.0',
            'Precedence': 'bulk',
            'Auto-Submitted': 'auto-generated',
            'List-Unsubscribe': f'<mailto:support@mfalmebetterdayscapital.com?subject=Unsubscribe>',
            'X-Entity-Ref-ID': str(uuid.uuid4()),  # Unique ID for tracking
            'X-Report-Abuse': 'Please report abuse to support@mfalmebetterdayscapital.com',
        }
        
        # Send email with Gmail-friendly headers
        email = EmailMultiAlternatives(
            subject=subject_clean,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
            headers=headers,
            reply_to=['support@mfalmebetterdayscapital.com']  # Add reply-to address
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Email sent to {recipient_list}")
        print(f"📧 Subject: {subject_clean}")
        print(f"📨 From: {from_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        print(f"🔧 Attempting fallback...")
        
        # Fallback 1: Try without HTML attachment (simpler)
        try:
            send_mail(
                subject=subject[:50],  # Shorter subject for fallback
                message=text_content,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            print(f"✅ Email sent (simple fallback) to {recipient_list}")
            return True
        except Exception as e2:
            print(f"❌ Simple fallback failed: {str(e2)}")
            
            # Fallback 2: Try with SMTP directly (most reliable)
            try:
                import smtplib
                from email.mime.text import MIMEText
                
                # Create simple plain text email
                msg = MIMEText(text_content)
                msg['Subject'] = subject[:50]
                msg['From'] = from_email
                msg['To'] = ', '.join(recipient_list)
                
                # Send via SMTP directly
                with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.send_message(msg)
                
                print(f"✅ Email sent (SMTP direct fallback) to {recipient_list}")
                return True
                
            except Exception as e3:
                print(f"❌ All email attempts failed. Last error: {str(e3)}")
                
                # Log the error for debugging
                import os
                debug_dir = os.path.join(settings.BASE_DIR, 'email_debug')
                os.makedirs(debug_dir, exist_ok=True)
                
                debug_file = os.path.join(debug_dir, f'email_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(debug_file, 'w') as f:
                    f.write(f"Time: {datetime.now()}\n")
                    f.write(f"To: {recipient_list}\n")
                    f.write(f"Subject: {subject}\n")
                    f.write(f"From: {from_email}\n")
                    f.write(f"Error 1: {str(e)}\n")
                    f.write(f"Error 2: {str(e2)}\n")
                    f.write(f"Error 3: {str(e3)}\n")
                    f.write("\n=== TEXT CONTENT ===\n")
                    f.write(text_content[:500] + "...")
                
                print(f"📝 Debug info saved to: {debug_file}")
                return False
# ===== VERIFICATION EMAIL =====
def send_verification_email(user, verification_code, request):
    """Send verification email - GMAIL SAFE VERSION"""
    try:
        verification_url = f"{request.scheme}://{request.get_host()}/verify-account/"
        
        # SIMPLIFIED HTML - Less spam triggers
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header - No verification mentions -->
                <tr>
                    <td style="background: #FFD700; padding: 30px; text-align: center;">
                        <h1 style="color: #000; margin: 0; font-size: 24px;">MFALME BETTERDAYS CAPITAL</h1>
                        <p style="color: #000; margin: 10px 0 0 0; font-weight: bold;">Complete Your Registration</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Hello <strong>{user.username}</strong>,<br><br>
                            Thank you for registering with MFALME BETTERDAYS CAPITAL!
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Your unique Soldier ID: <strong style="color: #FFD700;">{user.soldier_id}</strong>
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            To complete your account setup, please use the following access code:
                        </p>
                        
                        <!-- Access Code (not Verification Code) -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                            <tr>
                                <td align="center">
                                    <div style="background: #0A1520; color: #FFD700; font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 8px; letter-spacing: 10px; display: inline-block;">
                                        {verification_code}
                                    </div>
                                </td>
                            </tr>
                        </table>
                        
                        <p style="font-size: 14px; color: #666; text-align: center; margin-bottom: 30px;">
                            This access code is valid for 30 minutes
                        </p>
                        
                        <!-- Instructions - Changed wording -->
                        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #0A1520; margin-top: 0;">Complete Registration:</h3>
                            <ol style="color: #333; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Return to the registration page</li>
                                <li>Enter the 6-digit access code above</li>
                                <li>Click "Complete Registration"</li>
                                <li>Access your personal dashboard</li>
                            </ol>
                        </div>
                        
                        <!-- Button -->
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center">
                                    <a href="{verification_url}" style="background: #FFD700; color: #000; text-decoration: none; padding: 15px 40px; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">
                                        COMPLETE REGISTRATION
                                    </a>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Legal disclaimer - Important for spam filters -->
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="font-size: 11px; color: #666; text-align: center; line-height: 1.5;">
                                This email was sent to {user.email} because you registered on MFALME BETTERDAYS CAPITAL.<br>
                                If you did not request this registration, please ignore this email.<br>
                                This is an automated message, please do not reply directly.
                            </p>
                        </div>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0 0 10px 0; font-size: 12px;">
                            Phone: +254 706 286 667<br>
                            Email: support@mfalmebetterdayscapital.com
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Elite Trading Platform | Nairobi, Kenya<br>
                            © {datetime.now().year} MFALME BETTERDAYS CAPITAL. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Plain text version - Changed wording
        text_content = f"""
        MFALME BETTERDAYS CAPITAL - Complete Your Registration
        {'='*60}
        
        Hello {user.username},
        
        Thank you for registering with MFALME BETTERDAYS CAPITAL!
        
        Your Soldier ID: {user.soldier_id}
        
        To complete your registration, please use this access code:
        
        Access Code: {verification_code}
        
        Enter this code on our website to finalize your account setup.
        
        Registration Link: {verification_url}
        
        This access code is valid for 30 minutes.
        
        If you did not register for an account, please disregard this email.
        
        This is an automated message. Please do not reply directly.
        
        {'='*60}
        Contact: +254 706 286 667
        Email: support@mfalmebetterdayscapital.com
        {'='*60}
        """
        
        # CHANGED SUBJECT LINE - No "verify" or "verification"
        success = send_email_compatible(
            subject=f'Complete Your MFALME Registration - Soldier {user.soldier_id}',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Registration email sent to {user.email}")
        else:
            print(f"⚠️ Registration email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Registration email error: {str(e)}")
        return False

# ===== WELCOME EMAIL =====
def send_welcome_email(user, request):
    """Send welcome email after successful verification"""
    try:
        dashboard_url = f"{request.scheme}://{request.get_host()}/dashboard/"
        
        # Simple HTML that works in ALL email clients
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #FFD700; padding: 40px; text-align: center;">
                        <h1 style="color: #000; margin: 0; font-size: 28px; font-weight: bold;">
                            🎉 WELCOME TO MFALME!
                        </h1>
                        <p style="color: #000; margin: 10px 0 0 0; font-size: 16px;">
                            Your Elite Trading Journey Begins Now
                        </p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 40px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Congratulations, <strong>{user.username}</strong>!
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            Your account has been successfully verified and activated. 
                            Welcome to the elite trading community!
                        </p>
                        
                        <!-- Soldier ID Card -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #0A1520; border-radius: 10px; padding: 30px; margin-bottom: 30px; border: 2px solid #FFD700;">
                            <tr>
                                <td align="center">
                                    <p style="color: #FFD700; font-size: 14px; margin: 0 0 10px 0; text-transform: uppercase;">
                                        Elite Trading Soldier
                                    </p>
                                    <div style="color: #FFD700; font-size: 32px; font-weight: bold; margin: 10px 0;">
                                        {user.soldier_id}
                                    </div>
                                    <p style="color: #FFD700; font-size: 14px; margin: 10px 0 0 0;">
                                        {user.username}
                                    </p>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Account Details -->
                        <h3 style="color: #0A1520; margin-top: 0; margin-bottom: 20px;">
                            Your Account Details:
                        </h3>
                        
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                            <tr>
                                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                    <strong style="color: #666;">Username:</strong>
                                    <span style="float: right;">{user.username}</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                    <strong style="color: #666;">Email:</strong>
                                    <span style="float: right;">{user.email}</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                    <strong style="color: #666;">Status:</strong>
                                    <span style="float: right; color: #28a745; font-weight: bold;">✅ ACTIVE</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 0;">
                                    <strong style="color: #666;">Account Type:</strong>
                                    <span style="float: right; color: #FFD700; font-weight: bold;">ELITE TRADER</span>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Next Steps -->
                        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #0A1520; margin-top: 0;">🚀 Next Steps:</h3>
                            <ul style="color: #333; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Access your personalized dashboard</li>
                                <li>Explore trading courses & mentorship</li>
                                <li>Join our exclusive community</li>
                                <li>Setup security features</li>
                                <li>Start your trading journey</li>
                            </ul>
                        </div>
                        
                        <!-- Button -->
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center">
                                    <a href="{dashboard_url}" style="background: #FFD700; color: #000; text-decoration: none; padding: 15px 40px; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">
                                        LAUNCH MY DASHBOARD
                                    </a>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Support Info -->
                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="font-size: 14px; color: #666;">
                                <strong>Need Help?</strong><br>
                                📞 Call: +254 706 286 667 (24/7)<br>
                                📧 Email: support@mfalmebetterdayscapital.com<br>
                                ⏰ Response: Within 24 hours
                            </p>
                        </div>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0 0 10px 0; font-size: 12px;">
                            Elite Trading Platform | Nairobi, Kenya
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Trading involves risk. Only trade with capital you can afford to lose.<br>
                            © {datetime.now().year} MFALME BETTERDAYS CAPITAL. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        🎉 WELCOME TO MFALME BETTERDAYS CAPITAL!
        {'='*60}
        
        Congratulations {user.username}!
        
        Your account has been successfully verified and activated.
        
        📋 ACCOUNT DETAILS:
        Username: {user.username}
        Email: {user.email}
        Soldier ID: {user.soldier_id}
        Status: ✅ ACTIVE
        Account Type: ELITE TRADER
        
        🚀 NEXT STEPS:
        1. Access your dashboard: {dashboard_url}
        2. Explore trading courses & mentorship
        3. Join our exclusive community
        4. Setup security features
        5. Start your trading journey
        
        📞 24/7 SUPPORT:
        Phone: +254 706 286 667
        WhatsApp: +254 706 286 667
        Email: support@mfalmebetterdayscapital.com
        
        Your elite trading journey begins now. We're excited to have you!
        
        {'='*60}
        Best regards,
        Levi Muriuki & The MFALME BETTERDAYS CAPITAL Team
        {'='*60}
        """
        
        success = send_email_compatible(
            subject=f'Welcome to MFALME, Soldier {user.soldier_id}!',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Welcome email sent to {user.email}")
        else:
            print(f"⚠️ Welcome email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Welcome email error: {str(e)}")
        return False

# ===== ADMIN NOTIFICATION EMAIL =====
def notify_admin_new_registration(user, request):
    """Send admin notification for new registration"""
    try:
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        # Get registration data
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)
        total_users = MfalmeUsers.objects.count()
        today = timezone.now().date()
        today_registrations = MfalmeUsers.objects.filter(date_joined__date=today).count()
        
        # Simple HTML for admin notification
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #dc3545; color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">
                            🚨 NEW REGISTRATION ALERT
                        </h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">
                            MFALME BETTERDAYS CAPITAL
                        </p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            A new user has registered and verified their account.
                        </p>
                        
                        <!-- User Information -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">User Information:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Soldier ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                <strong style="color: #FFD700;">{user.soldier_id}</strong>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Name:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.username}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Email:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.email}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Phone:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.phone}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Registration Time:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>IP Address:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {ip_address}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Location:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right;">
                                                {location['city']}, {location['country']}
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Platform Stats -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Platform Statistics:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Total Users:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {total_users}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Today's Registrations:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {today_registrations}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Status:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right; color: #28a745; font-weight: bold;">
                                                ✅ VERIFIED & ACTIVE
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Action Required -->
                        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #856404; margin-top: 0;">📋 Required Actions:</h3>
                            <ol style="color: #856404; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Send welcome email & credentials</li>
                                <li>Assign mentor: Levi Muriuki</li>
                                <li>Add to communication channels</li>
                                <li>Schedule onboarding call (within 24h)</li>
                                <li>Activate trading package</li>
                            </ol>
                        </div>
                        
                        <p style="font-size: 12px; color: #666; text-align: center;">
                            This is an automated notification from MFALME Registration System.<br>
                            Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL • Admin System</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Priority: HIGH • Response Required: Within 24 hours
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        🚨 NEW USER REGISTRATION - MFALME BETTERDAYS CAPITAL
        {'='*70}
        
        ⚡ USER INFORMATION:
        Soldier ID: {user.soldier_id}
        Name: {user.username}
        Email: {user.email}
        Phone: {user.phone}
        Registration Time: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}
        IP Address: {ip_address}
        Location: {location['city']}, {location['country']}
        
        📊 PLATFORM STATISTICS:
        Total Users: {total_users}
        Today's Registrations: {today_registrations}
        Status: ✅ VERIFIED & ACTIVE
        
        📋 REQUIRED ACTIONS:
        1. Send welcome email & credentials
        2. Assign mentor: Levi Muriuki
        3. Add to communication channels
        4. Schedule onboarding call (within 24h)
        5. Activate trading package
        
        ⚡ PRIORITY: HIGH
        ⏰ RESPONSE REQUIRED: Within 24 hours
        
        {'='*70}
        This is an automated notification from MFALME Registration System.
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        {'='*70}
        """
        
        # Send to all admin emails
        all_success = True
        for admin_email in admin_emails:
            success = send_email_compatible(
                subject=f'🚨 NEW REGISTRATION: {user.soldier_id} - {user.username}',
                html_content=html_content,
                text_content=text_content,
                recipient_list=[admin_email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
            if success:
                print(f"✅ Admin notification sent to {admin_email}")
            else:
                print(f"⚠️ Admin notification failed for {admin_email}")
                all_success = False
        
        return all_success
        
    except Exception as e:
        print(f"❌ Admin notification error: {str(e)}")
        return False

# ===== PAYMENT EMAIL FUNCTIONS =====
def send_package_activation_email(user, transaction):
    """Send package activation email with conversion details"""
    try:
        metadata = transaction.metadata or {}
        package_name = metadata.get('package_name', 'Unknown Package')
        amount_usd = metadata.get('amount_usd', transaction.amount)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #28a745; color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🎉 PACKAGE ACTIVATED</h1>
                        <p style="margin: 10px 0 0 0;">MFALME BETTERDAYS CAPITAL</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Congratulations <strong>{user.username}</strong>!
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            Your <strong>{package_name}</strong> has been successfully activated.
                        </p>
                        
                        <!-- Transaction Details -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Transaction Details:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Package:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {package_name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Amount Paid:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                ${amount_usd:,.2f} USD
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Transaction ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {transaction.reference}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Status:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right; color: #28a745; font-weight: bold;">
                                                ✅ COMPLETED
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Next Steps -->
                        <div style="background: #e8f4fd; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #0A1520; margin-top: 0;">🚀 Next Steps:</h3>
                            <ul style="color: #333; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Access your dashboard for package features</li>
                                <li>Join the exclusive Telegram group</li>
                                <li>Schedule your onboarding call</li>
                                <li>Download the trading materials</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; text-align: center; color: #666;">
                            Thank you for choosing MFALME BETTERDAYS CAPITAL!
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Elite Trading Platform • Support: +254 706 286 667
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        🎉 PACKAGE ACTIVATION CONFIRMATION
        {'='*60}
        
        Congratulations {user.username}!
        
        Your {package_name} has been successfully activated.
        
        📋 TRANSACTION DETAILS:
        Package: {package_name}
        Amount Paid: ${amount_usd:,.2f} USD
        Transaction ID: {transaction.reference}
        Status: ✅ COMPLETED
        
        🚀 NEXT STEPS:
        1. Access your dashboard for package features
        2. Join the exclusive Telegram group
        3. Schedule your onboarding call
        4. Download the trading materials
        
        Thank you for choosing MFALME BETTERDAYS CAPITAL!
        
        {'='*60}
        Support: +254 706 286 667
        {'='*60}
        """
        
        success = send_email_compatible(
            subject=f'🎉 Package Activated - {package_name}',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Package activation email sent to {user.email}")
        else:
            print(f"⚠️ Package activation email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Package activation email error: {str(e)}")
        return False

def send_guest_welcome_email(user, temp_password, transaction):
    """Send welcome email to guest users after payment"""
    try:
        metadata = transaction.metadata or {}
        package_name = metadata.get('package_name', 'Selected Package')
        amount_usd = metadata.get('amount_usd', 0)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #FFD700; color: #000; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🎉 ACCOUNT CREATED</h1>
                        <p style="margin: 10px 0 0 0;">MFALME BETTERDAYS CAPITAL</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Hello <strong>{user.username}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            Your account has been created successfully! Your payment has been confirmed.
                        </p>
                        
                        <!-- Account Details -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Account Details:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Soldier ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.soldier_id}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Email:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {user.email}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Temporary Password:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                <strong>{temp_password}</strong>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Package:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {package_name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Amount:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right;">
                                                ${amount_usd:,.2f} USD
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Important Notice -->
                        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #856404; margin-top: 0;">⚠️ IMPORTANT:</h3>
                            <ul style="color: #856404; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Login with the temporary password above</li>
                                <li>Change your password immediately after login</li>
                                <li>Complete your profile information</li>
                                <li>Contact support if you need assistance</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; text-align: center; color: #666;">
                            Welcome to MFALME BETTERDAYS CAPITAL!
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Support: +254 706 286 667 • This is an automated message
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        🎉 ACCOUNT CREATED - MFALME BETTERDAYS CAPITAL
        {'='*60}
        
        Hello {user.username},
        
        Your account has been created successfully!
        
        📋 ACCOUNT DETAILS:
        Soldier ID: {user.soldier_id}
        Email: {user.email}
        Temporary Password: {temp_password}
        Package: {package_name}
        Amount: ${amount_usd:,.2f} USD
        
        ⚠️ IMPORTANT:
        1. Login with the temporary password above
        2. Change your password immediately after login
        3. Complete your profile information
        4. Contact support if you need assistance
        
        Welcome to MFALME BETTERDAYS CAPITAL!
        
        {'='*60}
        Support: +254 706 286 667
        {'='*60}
        """
        
        success = send_email_compatible(
            subject='🎉 Account Created - MFALME BETTERDAYS CAPITAL',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Guest welcome email sent to {user.email}")
        else:
            print(f"⚠️ Guest welcome email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Guest welcome email error: {str(e)}")
        return False

# ===== EDUCATION ENROLLMENT EMAIL =====
def send_education_enrollment_email(user, transaction):
    """Send education enrollment email"""
    try:
        metadata = transaction.metadata or {}
        program_name = metadata.get('program_name', 'Education Program')
        amount_usd = metadata.get('amount_usd', transaction.amount)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #17a2b8; color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🎓 EDUCATION ENROLLMENT</h1>
                        <p style="margin: 10px 0 0 0;">MFALME BETTERDAYS CAPITAL</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Congratulations <strong>{user.username}</strong>!
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            You have been successfully enrolled in <strong>{program_name}</strong>.
                        </p>
                        
                        <!-- Enrollment Details -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Enrollment Details:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Program:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {program_name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Amount Paid:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                ${amount_usd:,.2f} USD
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Transaction ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {transaction.reference}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Status:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right; color: #28a745; font-weight: bold;">
                                                ✅ ENROLLED
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Next Steps -->
                        <div style="background: #e8f4fd; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #0A1520; margin-top: 0;">📚 Next Steps:</h3>
                            <ul style="color: #333; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Access your learning dashboard</li>
                                <li>Join the student portal</li>
                                <li>Download course materials</li>
                                <li>Schedule orientation session</li>
                                <li>Connect with your instructor</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; text-align: center; color: #666;">
                            Best regards,<br>
                            MFALME BETTERDAYS CAPITAL Education Team
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Education Department • Support: +254 706 286 667
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        🎓 EDUCATION ENROLLMENT CONFIRMATION
        {'='*60}
        
        Congratulations {user.username}!
        
        You have been successfully enrolled in {program_name}.
        
        📋 ENROLLMENT DETAILS:
        Program: {program_name}
        Amount Paid: ${amount_usd:,.2f} USD
        Transaction ID: {transaction.reference}
        Status: ✅ ENROLLED
        
        📚 NEXT STEPS:
        1. Access your learning dashboard
        2. Join the student portal
        3. Download course materials
        4. Schedule orientation session
        5. Connect with your instructor
        
        Best regards,
        MFALME BETTERDAYS CAPITAL Education Team
        
        {'='*60}
        Support: +254 706 286 667
        {'='*60}
        """
        
        success = send_email_compatible(
            subject=f'🎓 Enrollment Confirmed - {program_name}',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Education enrollment email sent to {user.email}")
        else:
            print(f"⚠️ Education enrollment email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Education enrollment email error: {str(e)}")
        return False

# ===== PARTNERSHIP EMAIL =====
def send_partnership_approval_request(user, transaction):
    """Send partnership approval request email"""
    try:
        metadata = transaction.metadata or {}
        tier_name = metadata.get('tier', 'Partnership Tier')
        amount_usd = metadata.get('amount_usd', transaction.amount)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #6f42c1; color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🤝 PARTNERSHIP APPLICATION</h1>
                        <p style="margin: 10px 0 0 0;">MFALME BETTERDAYS CAPITAL</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Dear <strong>{user.username}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            Your partnership application for <strong>{tier_name}</strong> has been received and is under review.
                        </p>
                        
                        <!-- Application Details -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Application Details:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Partnership Tier:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {tier_name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Amount Paid:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                ${amount_usd:,.2f} USD
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Transaction ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {transaction.reference}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Status:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right; color: #ffc107; font-weight: bold;">
                                                ⏳ UNDER REVIEW
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Review Process -->
                        <div style="background: #fff3cd; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #856404; margin-top: 0;">⏳ Review Process:</h3>
                            <ul style="color: #856404; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Application under review (24-48 hours)</li>
                                <li>Partnership agreement preparation</li>
                                <li>Onboarding session scheduling</li>
                                <li>Access to partner dashboard</li>
                                <li>Integration with partner network</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; text-align: center; color: #666;">
                            We will contact you within 24-48 hours.<br>
                            Best regards,<br>
                            MFALME BETTERDAYS CAPITAL Partnership Team
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Partnership Department • Support: +254 706 286 667
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        🤝 PARTNERSHIP APPLICATION SUBMITTED
        {'='*60}
        
        Dear {user.username},
        
        Your partnership application for {tier_name} has been received.
        
        📋 APPLICATION DETAILS:
        Partnership Tier: {tier_name}
        Amount Paid: ${amount_usd:,.2f} USD
        Transaction ID: {transaction.reference}
        Status: ⏳ UNDER REVIEW
        
        ⏳ REVIEW PROCESS:
        1. Application under review (24-48 hours)
        2. Partnership agreement preparation
        3. Onboarding session scheduling
        4. Access to partner dashboard
        5. Integration with partner network
        
        We will contact you within 24-48 hours.
        
        Best regards,
        MFALME BETTERDAYS CAPITAL Partnership Team
        
        {'='*60}
        Support: +254 706 286 667
        {'='*60}
        """
        
        success = send_email_compatible(
            subject=f'🤝 Partnership Application - {tier_name}',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Partnership approval email sent to {user.email}")
        else:
            print(f"⚠️ Partnership approval email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Partnership approval email error: {str(e)}")
        return False

# ===== CUSTOM PAYMENT EMAIL =====
def send_custom_payment_confirmation(user, transaction):
    """Send custom payment confirmation email"""
    try:
        metadata = transaction.metadata or {}
        description = metadata.get('description', 'Custom Service')
        amount_usd = metadata.get('amount_usd', transaction.amount)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #6c757d; color: white; padding: 30px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">✅ PAYMENT RECEIVED</h1>
                        <p style="margin: 10px 0 0 0;">MFALME BETTERDAYS CAPITAL</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Dear <strong>{user.username}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; margin-bottom: 30px;">
                            Your payment for <strong>{description}</strong> has been received and confirmed.
                        </p>
                        
                        <!-- Payment Details -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <tr>
                                <td>
                                    <h3 style="color: #0A1520; margin-top: 0;">Payment Details:</h3>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Service:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {description}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Amount Paid:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                ${amount_usd:,.2f} USD
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6;">
                                                <strong>Transaction ID:</strong>
                                            </td>
                                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; text-align: right;">
                                                {transaction.reference}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <strong>Status:</strong>
                                            </td>
                                            <td style="padding: 8px 0; text-align: right; color: #28a745; font-weight: bold;">
                                                ✅ COMPLETED
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        
                        <!-- Next Steps -->
                        <div style="background: #e8f4fd; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                            <h3 style="color: #0A1520; margin-top: 0;">🔄 Next Steps:</h3>
                            <ul style="color: #333; font-size: 14px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>Service processing will begin shortly</li>
                                <li>You will receive updates via email</li>
                                <li>Contact support for any questions</li>
                                <li>Check your dashboard for status updates</li>
                            </ul>
                        </div>
                        
                        <p style="font-size: 14px; text-align: center; color: #666;">
                            Thank you for your business!<br>
                            Best regards,<br>
                            MFALME BETTERDAYS CAPITAL Support Team
                        </p>
                    </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                    <td style="background: #0A1520; color: #fff; padding: 20px; text-align: center;">
                        <p style="margin: 0 0 10px 0; font-size: 14px;">
                            <strong>MFALME BETTERDAYS CAPITAL</strong>
                        </p>
                        <p style="margin: 0; font-size: 10px; color: #999;">
                            Customer Support • Support: +254 706 286 667
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        ✅ CUSTOM PAYMENT CONFIRMATION
        {'='*60}
        
        Dear {user.username},
        
        Your payment for {description} has been received.
        
        📋 PAYMENT DETAILS:
        Service: {description}
        Amount Paid: ${amount_usd:,.2f} USD
        Transaction ID: {transaction.reference}
        Status: ✅ COMPLETED
        
        🔄 NEXT STEPS:
        1. Service processing will begin shortly
        2. You will receive updates via email
        3. Contact support for any questions
        4. Check your dashboard for status updates
        
        Thank you for your business!
        
        Best regards,
        MFALME BETTERDAYS CAPITAL Support Team
        
        {'='*60}
        Support: +254 706 286 667
        {'='*60}
        """
        
        success = send_email_compatible(
            subject=f'✅ Payment Received - {description}',
            html_content=html_content,
            text_content=text_content,
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        
        if success:
            print(f"✅ Custom payment email sent to {user.email}")
        else:
            print(f"⚠️ Custom payment email might have failed for {user.email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Custom payment confirmation email error: {str(e)}")
        return False

# ===== EXCHANGE RATE FUNCTIONS =====

def get_live_exchange_rate():
    """Get current USD to KES exchange rate from a reliable API"""
    try:
        # Try Frankfurter API
        response = requests.get('https://api.frankfurter.app/latest?from=USD&to=KES', timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data['rates']['KES']
            print(f"✅ Exchange rate from Frankfurter: 1 USD = {rate} KES")
            return float(rate)
    except:
        pass
    
    # Fallback rate
    print("⚠️ Using fallback exchange rate")
    return 160.0

def convert_usd_to_kes_cents(usd_amount):
    """Convert USD amount to KES cents for Paystack"""
    exchange_rate = get_live_exchange_rate()
    kes_amount = usd_amount * exchange_rate
    kes_cents = int(kes_amount * 100)  # Paystack expects cents
    
    print(f"💱 Currency Conversion: ${usd_amount} USD → {kes_amount:,.0f} KES → {kes_cents:,} cents (Rate: {exchange_rate})")
    
    return kes_cents, exchange_rate, kes_amount

# ===== CORE FUNCTIONS =====

def get_client_ip(request):
    """Get client IP address with proxy support"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def get_user_agent_info(request):
    """Extract device and browser information"""
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    device_info = {
        'user_agent': user_agent[:500],
        'is_mobile': 'Mobile' in user_agent,
        'is_tablet': 'Tablet' in user_agent,
        'is_desktop': not ('Mobile' in user_agent or 'Tablet' in user_agent),
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop'
    }
    
    # Browser detection
    if 'Chrome' in user_agent:
        device_info['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        device_info['browser'] = 'Firefox'
    elif 'Safari' in user_agent:
        device_info['browser'] = 'Safari'
    elif 'Edge' in user_agent:
        device_info['browser'] = 'Edge'
    elif 'Opera' in user_agent:
        device_info['browser'] = 'Opera'
    
    # OS detection
    if 'Windows' in user_agent:
        device_info['os'] = 'Windows'
    elif 'Mac' in user_agent:
        device_info['os'] = 'macOS'
    elif 'Linux' in user_agent:
        device_info['os'] = 'Linux'
    elif 'Android' in user_agent:
        device_info['os'] = 'Android'
        device_info['device'] = 'Mobile'
    elif 'iOS' in user_agent:
        device_info['os'] = 'iOS'
        device_info['device'] = 'Mobile'
    
    # Device type
    if device_info['is_mobile']:
        device_info['device'] = 'Mobile'
    elif device_info['is_tablet']:
        device_info['device'] = 'Tablet'
    
    return device_info

def get_location_from_ip(ip):
    """Get approximate location from IP address"""
    if ip in ['127.0.0.1', 'localhost']:
        return {'country': 'Local', 'city': 'Development', 'isp': 'Local Network'}
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone', 'Unknown')
                }
    except:
        pass
    
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}

def generate_soldier_id():
    """Generate unique soldier ID in format: MFALME-YYMM-XXXXX"""
    timestamp = datetime.now().strftime('%y%m')
    random_part = str(uuid.uuid4())[:8].upper()
    return f"MFALME-{timestamp}-{random_part}"

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

# ===== PAYSTACK WEBHOOK HANDLER =====
@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook notifications for recurring payments"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        # Get the payload
        payload = json.loads(request.body)
        
        # Verify the event
        event = payload.get('event', '')
        data = payload.get('data', {})
        
        print(f"🔔 Paystack Webhook Received: {event}")
        
        if event == 'charge.success':
            reference = data.get('reference', '')
            if reference:
                # Process the successful charge
                try:
                    transaction = PaymentTransaction.objects.get(reference=reference)
                    transaction.status = 'completed'
                    transaction.paystack_data = data
                    transaction.paid_at = timezone.now()
                    transaction.save()
                    
                    print(f"✅ Webhook: Payment {reference} marked as completed")
                    
                except PaymentTransaction.DoesNotExist:
                    print(f"⚠️ Webhook: Transaction {reference} not found in database")
        
        elif event == 'subscription.create':
            subscription_code = data.get('subscription_code', '')
            customer_email = data.get('customer', {}).get('email', '')
            
            print(f"📝 Webhook: New subscription created for {customer_email}")
            
            try:
                user = MfalmeUsers.objects.get(email=customer_email)
                # Create or update subscription record
                print(f"✅ Webhook: Subscription {subscription_code} linked to user {user.email}")
            except MfalmeUsers.DoesNotExist:
                print(f"⚠️ Webhook: User {customer_email} not found for subscription")
        
        elif event == 'subscription.disable':
            subscription_code = data.get('subscription_code', '')
            print(f"📝 Webhook: Subscription disabled: {subscription_code}")
        
        # Return success response to Paystack
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ===== CORE VIEWS =====

def index(request):
    """Home page"""
    return render(request, 'index.html')

def login_page(request):
    """Login/Signup page"""
    if 'user_id' in request.session:
        return redirect('dashboard')
    
    active_tab = request.GET.get('tab', 'login')
    form_data = request.session.pop('form_data', {})
    
    return render(request, 'login.html', {
        'active_tab': active_tab,
        'form_data': form_data
    })

def login_user(request):
    """Handle user login"""
    if request.method != 'POST':
        return redirect('login_page')
    
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '').strip()
    
    print(f"🔐 Login attempt: {email}")
    
    if not email or not password:
        messages.error(request, 'Email and password are required.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(email=email)
        
        # Check password
        if user.password == password or hash_password(password) == user.password:
            # Check email verification
            if not user.email_verified:
                # Store for verification
                request.session['pending_user_id'] = user.id
                request.session['pending_user_email'] = user.email
                
                # Generate and send new verification code
                verification_code = ''.join(random.choices(string.digits, k=6))
                request.session['verification_code'] = verification_code
                
                # Save verification code to database
                VerificationCode.objects.create(
                    user=user,
                    code=verification_code,
                    expires_at=timezone.now() + timedelta(minutes=30),
                    ip_address=get_client_ip(request)
                )
                
                # Send verification email
                send_verification_email(user, verification_code, request)
                
                messages.error(request, 'Please verify your email first. A new verification code has been sent.')
                return redirect('verify_account_page')
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Set session
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['username'] = user.username
            request.session['soldier_id'] = user.soldier_id
            request.session['elite_rank'] = getattr(user, 'elite_rank', 'Recruit')
            
            messages.success(request, f'Welcome back, {user.username}!')
            print(f"✅ Login successful: {email}")
            return redirect('dashboard')
        
        else:
            messages.error(request, 'Invalid email or password.')
            print(f"❌ Wrong password: {email}")
            return redirect('login_page')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'Account not found. Please register first.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        messages.error(request, 'An error occurred. Please try again.')
        return redirect('login_page')

@csrf_exempt
def create_account(request):
    """Handle new account registration"""
    if request.method != 'POST':
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    # Collect form data
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '').strip()
    confirm_password = request.POST.get('password1', '').strip()
    phone = request.POST.get('phone', '').strip()
    username = request.POST.get('username', '').strip()
    
    print(f"\n📝 Registration started for: {email}")
    
    # Store form data for repopulation
    request.session['form_data'] = {
        'email': email,
        'username': username,
        'phone': phone,
    }
    
    # Validation
    errors = []
    
    if not username or len(username) < 2:
        errors.append('Please enter your full name.')
    
    if not email or '@' not in email:
        errors.append('Please enter a valid email address.')
    
    if len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    
    if password != confirm_password:
        errors.append('Passwords do not match.')
    
    if not phone:
        errors.append('Phone number is required.')
    
    # Check existing user
    if MfalmeUsers.objects.filter(email=email).exists():
        errors.append('Email already registered. Please login instead.')
    
    if errors:
        for error in errors:
            messages.error(request, error)
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    try:
        # Get registration metadata
        ip_address = get_client_ip(request)
        location = get_location_from_ip(ip_address)
        device_info = get_user_agent_info(request)
        
        # Generate soldier ID
        soldier_id = generate_soldier_id()
        
        # Create user
        user = MfalmeUsers.objects.create(
            email=email,
            password=hash_password(password),
            username=username,
            phone=phone,
            soldier_id=soldier_id,
            is_active=True,
            email_verified=False,
            registration_ip=ip_address,
            registration_time=timezone.now(),
            registration_location=f"{location['city']}, {location['country']}",
            account_status='pending_verification',
            elite_rank='Recruit'
        )
        
        print(f"✅ User created: {user.soldier_id}")
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Save verification code
        VerificationCode.objects.create(
            user=user,
            code=verification_code,
            expires_at=timezone.now() + timedelta(minutes=30),
            ip_address=ip_address,
            device_info=device_info['user_agent']
        )
        
        # Store in session
        request.session['pending_user_id'] = user.id
        request.session['pending_user_email'] = user.email
        request.session['pending_soldier_id'] = user.soldier_id
        request.session['verification_code'] = verification_code
        
        # Clear form data from session
        if 'form_data' in request.session:
            del request.session['form_data']
        
        print(f"📧 Generated code: {verification_code}")
        
        # Send admin notification
        print("📧 Sending admin notification...")
        admin_success = notify_admin_new_registration(user, request)
        
        # Send verification email WITH RETRY
        max_retries = 3
        email_sent = False
        for attempt in range(max_retries):
            email_sent = send_verification_email(user, verification_code, request)
            if email_sent:
                print(f"✅ Verification email sent on attempt {attempt + 1}")
                break
            else:
                print(f"⚠️ Email attempt {attempt + 1} failed")
                time.sleep(1)
        
        if email_sent:
            messages.success(request, 
                f'Registration successful! Check {email} for verification code. '
                f'Your Soldier ID: {user.soldier_id}'
            )
        else:
            messages.warning(request,
                f'Registration successful but email failed. '
                f'Your verification code: {verification_code} '
                f'Soldier ID: {user.soldier_id}'
            )
        
        return redirect('verify_account_page')
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        messages.error(request, 'Registration failed. Please try again.')
        return redirect(f'{reverse("login_page")}?tab=signup')

def verify_account_page(request):
    """Verification page"""
    if 'pending_user_id' not in request.session:
        messages.error(request, 'No pending verification. Please register first.')
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    user_email = request.session.get('pending_user_email', '')
    soldier_id = request.session.get('pending_soldier_id', '')
    
    # For debugging only - remove in production
    debug_code = request.session.get('verification_code', '')
    
    print(f"🔑 Verification page accessed: {user_email} | Soldier: {soldier_id}")
    
    return render(request, 'verify_account.html', {
        'user_email': user_email,
        'soldier_id': soldier_id,
        'debug_code': debug_code  # Remove this in production!
    })

def verify_account_process(request):
    """Process verification code"""
    if request.method != 'POST':
        return redirect('verify_account_page')
    
    user_id = request.session.get('pending_user_id')
    entered_code = request.POST.get('verification_code', '').strip()
    
    print(f"\n🔍 Verification attempt: User {user_id}, Code: {entered_code}")
    
    if not user_id or not entered_code:
        messages.error(request, 'Session expired. Please register again.')
        return redirect(f'{reverse("login_page")}?tab=signup')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Check against session code
        session_code = request.session.get('verification_code')
        
        # Also check in database
        verification = VerificationCode.objects.filter(
            user=user,
            code=entered_code,
            is_used=False
        ).order_by('-created_at').first()
        
        valid_session = (session_code == entered_code)
        valid_db = (verification and verification.expires_at > timezone.now())
        
        if valid_session or valid_db:
            # Activate user account
            user.email_verified = True
            user.verified_at = timezone.now()
            user.is_active = True
            user.account_status = 'active'
            user.elite_rank = 'Private'
            user.save()
            
            # Mark verification as used
            if verification:
                verification.is_used = True
                verification.save()
            
            # Clear verification session
            session_keys = [
                'pending_user_id', 'pending_user_email', 
                'pending_soldier_id', 'verification_code'
            ]
            for key in session_keys:
                if key in request.session:
                    del request.session[key]
            
            # Login user
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['username'] = user.username
            request.session['soldier_id'] = user.soldier_id
            request.session['elite_rank'] = user.elite_rank
            
            print(f"✅ Account verified: {user.soldier_id}")
            
            # Send welcome email
            print("📧 Sending welcome email...")
            welcome_sent = send_welcome_email(user, request)
            
            if welcome_sent:
                print(f"✅ Welcome email sent to {user.email}")
            
            messages.success(request, 
                f'🎉 Account verified successfully! Welcome {user.username} (#{user.soldier_id}).'
            )
            return redirect('dashboard')
        
        else:
            print(f"❌ Invalid code: {entered_code}")
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('verify_account_page')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        messages.error(request, 'Verification failed. Please try again.')
        return redirect('verify_account_page')

def resend_verification(request):
    """Resend verification code"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method.'
        })
    
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please refresh and try again.'
        })
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Generate new code
        new_code = ''.join(random.choices(string.digits, k=6))
        
        # Save to database
        VerificationCode.objects.create(
            user=user,
            code=new_code,
            expires_at=timezone.now() + timedelta(minutes=30),
            ip_address=get_client_ip(request)
        )
        
        # Update session
        request.session['verification_code'] = new_code
        
        # Send email
        email_sent = send_verification_email(user, new_code, request)
        
        if email_sent:
            print(f"✅ Code resent to {user.email}: {new_code}")
            return JsonResponse({
                'success': True,
                'message': 'New verification code sent to your email.',
            })
        else:
            print(f"⚠️ Email failed, showing code: {new_code}")
            return JsonResponse({
                'success': True,
                'message': f'Email failed. Your new code: {new_code}',
            })
            
    except Exception as e:
        print(f"❌ Resend error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to resend verification code.'
        })

def dashboard(request):
    """User dashboard"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, 'Please login to access dashboard.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Calculate account age
        account_age = (timezone.now() - user.date_joined).days
        
        # Get user's payment history
        payments = PaymentTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        
        context = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'soldier_id': user.soldier_id,
            'elite_rank': getattr(user, 'elite_rank', 'Recruit'),
            'is_verified': user.email_verified,
            'account_status': getattr(user, 'account_status', 'active'),
            'date_joined': user.date_joined.strftime('%B %d, %Y'),
            'account_age_days': account_age,
            'last_login': user.last_login.strftime('%B %d, %Y at %H:%M') if user.last_login else 'First login',
            'payment_history': payments,
        }
        
        # Update last activity
        user.last_activity = timezone.now()
        user.save()
        
        return render(request, 'dashboard.html', context)
        
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')

def logout_user(request):
    """Handle user logout"""
    # Clear all session data
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    messages.success(request, 'Logged out successfully!')
    return redirect('index')

# ===== PAYMENT VIEWS =====

@csrf_exempt
def initiate_package_payment(request, package_type, amount):
    """Initiate payment for trading packages"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to make a payment.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Map package types to proper names
        package_map = {
            'market_consultation': {'name': 'Market Consultation', 'amount_usd': 200},
            'lifetime_mentorship': {'name': 'Lifetime Mentorship Package', 'amount_usd': 5000},
            'leveraging_package': {'name': 'Leveraging Package', 'amount_usd': 100000},
            'lifetime_signals': {'name': 'Lifetime Signals Package', 'amount_usd': 200},
        }
        
        if package_type not in package_map:
            messages.error(request, 'Invalid package selection.')
            return redirect('services')
        
        package_info = package_map[package_type]
        usd_amount = package_info['amount_usd']
        
        print(f"💰 Package Payment Initiated: {package_info['name']} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-PKG-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction in database
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            package_type=package_type,
            status='initiated',
            payment_type='package',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'package_name': package_info['name'],
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'package_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API headers
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        # Paystack data with KES amount
        data = {
            'email': user.email,
            'amount': kes_cents,  # Amount in KES cents
            'reference': reference,
            'currency': 'KES',  # Paystack Kenya uses KES
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Full Name",
                        'variable_name': "full_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Package",
                        'variable_name': "package",
                        'value': package_info['name']
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    },
                    {
                        'display_name': "Exchange Rate",
                        'variable_name': "exchange_rate",
                        'value': f"1 USD = {exchange_rate:,.2f} KES"
                    }
                ]
            }
        }
        
        print(f"📤 Sending to Paystack: KES {kes_amount:,.2f} ({kes_cents:,} cents)")
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                # Store in session for verification
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'package'
                request.session['package_type'] = package_type
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                # Redirect to Paystack payment page
                return redirect(result['data']['authorization_url'])
            else:
                error_msg = result.get('message', 'Failed to initialize payment')
                messages.error(request, f'Paystack Error: {error_msg}')
                transaction.status = 'failed'
                transaction.error_message = error_msg
                transaction.save()
                return redirect('services')
        else:
            error_msg = f'Payment service error: {response.status_code}'
            messages.error(request, error_msg)
            transaction.status = 'failed'
            transaction.error_message = error_msg
            transaction.save()
            return redirect('services')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Payment initialization error: {str(e)}")
        messages.error(request, f'Payment initialization failed: {str(e)}')
        return redirect('services')

def initiate_education_payment(request, program_type, duration):
    """Initiate payment for education programs"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to enroll in a program.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Map education programs to prices (in USD)
        program_prices = {
            'IPLT': {'1_month': 0, '12_months': 1299},
            'PTM': {'1_month': 1999, '12_months': 3499},
            'POTM': {'1_month': 1999, '12_months': 3499},
            'PFTM': {'1_month': 1499, '12_months': 2999},
        }
        
        if program_type not in program_prices or duration not in program_prices[program_type]:
            messages.error(request, 'Invalid program selection.')
            return redirect('education')
        
        usd_amount = program_prices[program_type][duration]
        program_name = f"{program_type} Program ({duration.replace('_', ' ')})"
        
        print(f"🎓 Education Payment: {program_name} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-EDU-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            program_type=program_type,
            duration=duration,
            status='initiated',
            payment_type='education',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'program_name': program_name,
                'duration': duration,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'education_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Student Name",
                        'variable_name': "student_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Program",
                        'variable_name': "program",
                        'value': program_name
                    },
                    {
                        'display_name': "Duration",
                        'variable_name': "duration",
                        'value': duration.replace('_', ' ')
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'education'
                request.session['program_type'] = program_type
                request.session['program_duration'] = duration
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Education payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('education')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Education payment error: {str(e)}")
        messages.error(request, 'Payment initialization failed.')
        return redirect('education')

def initiate_partnership_payment(request, tier):
    """Initiate payment for partnership programs"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to become a partner.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Partnership tier amounts (in USD)
        tier_amounts = {
            'bronze': 250000,
            'silver': 500000,
            'gold': 1000000,
            'platinum': 5000000,
            'premium': 10000000,
        }
        
        if tier not in tier_amounts:
            messages.error(request, 'Invalid partnership tier.')
            return redirect('partnership')
        
        usd_amount = tier_amounts[tier]
        tier_name = tier.capitalize() + " Partnership"
        
        print(f"🤝 Partnership Payment: {tier_name} - ${usd_amount:,} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-PART-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            partnership_tier=tier,
            status='initiated',
            payment_type='partnership',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'company_name': user.username,
                'tier': tier_name,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'partnership_payment',
                'requires_approval': True,
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # For large amounts, use standard Paystack flow
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Company/Individual",
                        'variable_name': "company",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Partnership Tier",
                        'variable_name': "tier",
                        'value': tier_name
                    },
                    {
                        'display_name': "Contact Phone",
                        'variable_name': "phone",
                        'value': user.phone
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'partnership'
                request.session['partnership_tier'] = tier
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Partnership payment initialized: ${usd_amount:,} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('partnership')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Partnership payment error: {str(e)}")
        messages.error(request, 'Partnership payment initialization failed.')
        return redirect('partnership')

@csrf_exempt
def initiate_custom_payment(request):
    """Custom payment for miscellaneous services"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('contact')
    
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to make a payment.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Get custom payment details
        usd_amount = float(request.POST.get('amount', 0))
        description = request.POST.get('description', 'Custom Payment')
        service_type = request.POST.get('service_type', 'other')
        
        if usd_amount <= 0:
            messages.error(request, 'Invalid payment amount.')
            return redirect('contact')
        
        print(f"💰 Custom Payment: {description} - ${usd_amount} USD")
        
        # CONVERT USD TO KES CENTS
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
        
        # Generate unique reference
        reference = f"MFALME-CUST-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=usd_amount,  # Store USD amount
            currency='USD',
            description=description,
            service_type=service_type,
            status='initiated',
            payment_type='custom',
            metadata={
                'user_id': user.id,
                'soldier_id': user.soldier_id,
                'description': description,
                'service_type': service_type,
                'amount_usd': usd_amount,
                'amount_kes': kes_amount,
                'amount_kes_cents': kes_cents,
                'exchange_rate': exchange_rate,
                'conversion_timestamp': datetime.now().isoformat(),
                'payment_type': 'custom_payment',
                'currency_converted': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'email': user.email,
            'amount': kes_cents,  # KES cents
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Customer Name",
                        'variable_name': "customer_name",
                        'value': user.username
                    },
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Service Description",
                        'variable_name': "service",
                        'value': description
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${usd_amount:,.2f}"
                    },
                    {
                        'display_name': "Amount KES",
                        'variable_name': "amount_kes",
                        'value': f"KES {kes_amount:,.2f}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                request.session['payment_reference'] = reference
                request.session['payment_type'] = 'custom'
                request.session['custom_description'] = description
                request.session['amount_usd'] = usd_amount
                request.session['amount_kes'] = kes_amount
                request.session['exchange_rate'] = exchange_rate
                
                print(f"✅ Custom payment initialized: ${usd_amount} USD → KES {kes_amount:,.2f}")
                
                return redirect(result['data']['authorization_url'])
            else:
                messages.error(request, result.get('message', 'Failed to initialize payment'))
        else:
            messages.error(request, 'Failed to connect to payment service')
        
        transaction.status = 'failed'
        transaction.save()
        return redirect('contact')
            
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')
    except Exception as e:
        print(f"❌ Custom payment error: {str(e)}")
        messages.error(request, 'Custom payment initialization failed.')
        return redirect('contact')

@csrf_exempt
def verify_payment(request, reference):
    """Verify Paystack payment callback"""
    try:
        # Verify payment with Paystack API
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        # Get transaction from database
        transaction = PaymentTransaction.objects.get(reference=reference)
        
        if response.status_code == 200:
            verification = response.json()
            
            if verification.get('status') and verification['data']['status'] == 'success':
                # Payment successful
                transaction.status = 'completed'
                transaction.paystack_data = verification['data']
                transaction.paid_at = timezone.now()
                transaction.save()
                
                # Get user from transaction
                user = transaction.user
                metadata = transaction.metadata or {}
                
                # Display conversion details in success message
                usd_amount = metadata.get('amount_usd', transaction.amount)
                kes_amount = metadata.get('amount_kes', 0)
                exchange_rate = metadata.get('exchange_rate', 0)
                
                if kes_amount and exchange_rate:
                    success_msg = (
                        f'✅ Payment successful! '
                        f'${usd_amount:,.2f} USD → KES {kes_amount:,.2f} '
                        f'(Rate: {exchange_rate:,.2f})'
                    )
                else:
                    success_msg = '✅ Payment verified successfully!'
                
                # Handle different payment types
                payment_type = transaction.payment_type
                
                if payment_type == 'package':
                    # Activate package for user
                    package_name = metadata.get('package_name', 'Unknown Package')
                    user.preferred_package = package_name
                    user.account_status = 'active'
                    user.save()
                    
                    # Send package activation email
                    send_package_activation_email(user, transaction)
                    
                    messages.success(request, f'🎉 {success_msg} Package activated: {package_name}')
                    return redirect('payment_success')
                    
                elif payment_type == 'education':
                    # Enroll in education program
                    send_education_enrollment_email(user, transaction)
                    
                    messages.success(request, f'🎓 {success_msg} Education enrollment confirmed!')
                    return redirect('payment_success')
                    
                elif payment_type == 'partnership':
                    # Process partnership application
                    send_partnership_approval_request(user, transaction)
                    
                    messages.success(request, f'🤝 {success_msg} Partnership application submitted!')
                    return redirect('payment_success')
                    
                elif payment_type == 'custom':
                    # Handle custom payment
                    send_custom_payment_confirmation(user, transaction)
                    
                    messages.success(request, f'✅ {success_msg} Custom payment received!')
                    return redirect('payment_success')
                
                else:
                    messages.success(request, success_msg)
                    return redirect('payment_success')
                    
            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.paystack_data = verification.get('data', {}) if response.status_code == 200 else {}
                transaction.save()
                
                messages.error(request, '❌ Payment verification failed. Please try again.')
                return redirect('payment_failed')
        else:
            # API call failed
            transaction.status = 'failed'
            transaction.save()
            
            messages.error(request, '❌ Unable to verify payment. Please contact support.')
            return redirect('payment_failed')
            
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('index')
    except Exception as e:
        print(f"❌ Payment verification error: {str(e)}")
        messages.error(request, 'Payment verification error.')
        return redirect('payment_failed')

def payment_success(request):
    """Payment success page"""
    reference = request.session.get('payment_reference', '')
    payment_type = request.session.get('payment_type', '')
    
    # Get conversion details from session
    usd_amount = request.session.get('amount_usd', 0)
    kes_amount = request.session.get('amount_kes', 0)
    exchange_rate = request.session.get('exchange_rate', 0)
    
    # Try to get transaction details
    transaction = None
    if reference:
        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
        except PaymentTransaction.DoesNotExist:
            pass
    
    context = {
        'reference': reference,
        'payment_type': payment_type,
        'transaction': transaction,
        'usd_amount': usd_amount,
        'kes_amount': kes_amount,
        'exchange_rate': exchange_rate,
        'conversion_applied': bool(kes_amount and exchange_rate),
    }
    
    # Clear payment session data
    payment_keys = ['payment_reference', 'payment_type', 'package_type', 
                    'program_type', 'program_duration', 'partnership_tier', 
                    'custom_description', 'amount_usd', 'amount_kes', 'exchange_rate']
    for key in payment_keys:
        if key in request.session:
            del request.session[key]
    
    return render(request, 'payments/success.html', context)

def payment_failed(request):
    """Payment failed page"""
    reference = request.session.get('payment_reference', '')
    
    context = {
        'reference': reference,
    }
    
    # Clear payment session data
    if 'payment_reference' in request.session:
        del request.session['payment_reference']
    
    return render(request, 'payments/failed.html', context)

def payment_history(request):
    """User payment history"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to view payment history.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        transactions = PaymentTransaction.objects.filter(user=user).order_by('-created_at')
        
        # Calculate totals
        total_paid_usd = sum(t.amount for t in transactions if t.status == 'completed')
        
        # Get KES totals from metadata
        total_paid_kes = 0
        for t in transactions.filter(status='completed'):
            metadata = t.metadata or {}
            kes_amount = metadata.get('amount_kes', 0)
            if kes_amount:
                total_paid_kes += kes_amount
            else:
                # Estimate if not stored
                total_paid_kes += t.amount * 160  # Rough estimate
        
        pending_payments = transactions.filter(status__in=['initiated', 'pending']).count()
        
        context = {
            'user': user,
            'transactions': transactions,
            'total_paid_usd': total_paid_usd,
            'total_paid_kes': total_paid_kes,
            'pending_payments': pending_payments,
            'total_transactions': transactions.count(),
        }
        
        return render(request, 'payments/history.html', context)
    
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')

# ===== PAY WITHOUT LOGIN =====

@csrf_exempt
def pay_without_login(request):
    """Allow users to pay without creating an account first"""
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            phone = request.POST.get('phone', '').strip()
            package_type = request.POST.get('package_type', 'market_consultation')
            amount_usd = float(request.POST.get('amount', 200))
            
            # Validate
            if not all([full_name, email, phone]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'payments/pay_no_login.html')
            
            # Create or get user
            user, created = MfalmeUsers.objects.get_or_create(
                email=email,
                defaults={
                    'username': full_name,
                    'phone': phone,
                    'password': hashlib.sha256(str(random.random()).encode()).hexdigest()[:20],
                    'soldier_id': generate_soldier_id(),
                    'is_active': True,
                    'email_verified': True,
                    'account_status': 'active',
                    'elite_rank': 'Guest',
                    'is_guest': True,
                }
            )
            
            if created:
                print(f"✅ Created guest user: {email}")
            
            # Map package types
            package_map = {
                'market_consultation': {'name': 'Market Consultation', 'amount_usd': 200},
                'lifetime_mentorship': {'name': 'Lifetime Mentorship Package', 'amount_usd': 5000},
                'leveraging_package': {'name': 'Leveraging Package', 'amount_usd': 100000},
                'lifetime_signals': {'name': 'Lifetime Signals Package', 'amount_usd': 200},
            }
            
            if package_type not in package_map:
                package_type = 'market_consultation'
            
            package_info = package_map[package_type]
            usd_amount = package_info['amount_usd']
            
            print(f"💰 Guest Payment: {package_info['name']} - ${usd_amount} USD by {email}")
            
            # Convert USD to KES
            kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(usd_amount)
            
            # Generate reference
            reference = f"GUEST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
            
            # Create transaction
            transaction = PaymentTransaction.objects.create(
                user=user,
                reference=reference,
                amount=usd_amount,
                currency='USD',
                package_type=package_type,
                status='initiated',
                payment_type='package',
                metadata={
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'package_name': package_info['name'],
                    'amount_usd': usd_amount,
                    'amount_kes': kes_amount,
                    'amount_kes_cents': kes_cents,
                    'exchange_rate': exchange_rate,
                    'is_guest_payment': True,
                    'guest_created': created,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Paystack API
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'email': email,
                'amount': kes_cents,
                'reference': reference,
                'currency': 'KES',
                'callback_url': f"{request.scheme}://{request.get_host()}/payment/guest-verify/{reference}/",
                'metadata': {
                    'custom_fields': [
                        {
                            'display_name': "Customer Name",
                            'variable_name': "customer_name",
                            'value': full_name
                        },
                        {
                            'display_name': "Email",
                            'variable_name': "email",
                            'value': email
                        },
                        {
                            'display_name': "Phone",
                            'variable_name': "phone",
                            'value': phone
                        },
                        {
                            'display_name': "Package",
                            'variable_name': "package",
                            'value': package_info['name']
                        }
                    ]
                }
            }
            
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status'):
                    # Store minimal session data
                    request.session['guest_payment_ref'] = reference
                    request.session['guest_email'] = email
                    request.session['guest_name'] = full_name
                    
                    print(f"✅ Guest payment initiated: {reference}")
                    return redirect(result['data']['authorization_url'])
                else:
                    error_msg = result.get('message', 'Failed to initialize payment')
                    messages.error(request, f'Payment Error: {error_msg}')
            else:
                messages.error(request, 'Failed to connect to payment service')
            
            return render(request, 'payments/pay_no_login.html')
                
        except Exception as e:
            print(f"❌ Guest payment error: {str(e)}")
            messages.error(request, 'Payment initialization failed. Please try again.')
            return render(request, 'payments/pay_no_login.html')
    
    # GET request - show payment form
    return render(request, 'payments/pay_no_login.html')

@csrf_exempt
def verify_guest_payment(request, reference):
    """Verify guest payment and send login details"""
    try:
        # Verify with Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        if response.status_code == 200:
            verification = response.json()
            
            if verification.get('status') and verification['data']['status'] == 'success':
                # Payment successful
                transaction = PaymentTransaction.objects.get(reference=reference)
                transaction.status = 'completed'
                transaction.paystack_data = verification['data']
                transaction.paid_at = timezone.now()
                transaction.save()
                
                user = transaction.user
                metadata = transaction.metadata or {}
                
                # Generate temporary password for guest
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                user.password = hashlib.sha256(temp_password.encode()).hexdigest()
                user.save()
                
                # Send welcome email with credentials
                send_guest_welcome_email(user, temp_password, transaction)
                
                # Auto-login the user
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                request.session['username'] = user.username
                request.session['soldier_id'] = user.soldier_id
                request.session['elite_rank'] = user.elite_rank
                request.session['is_guest'] = True
                
                # Clear guest session
                if 'guest_payment_ref' in request.session:
                    del request.session['guest_payment_ref']
                
                messages.success(request, 
                    f"✅ Payment successful! Account created. Check your email for login details."
                )
                return redirect('payment_success')
                
            else:
                messages.error(request, "❌ Payment verification failed")
        else:
            messages.error(request, "❌ Unable to verify payment")
    
    except PaymentTransaction.DoesNotExist:
        messages.error(request, "Transaction not found")
    except Exception as e:
        print(f"❌ Guest payment verification error: {str(e)}")
        messages.error(request, "Payment verification error")
    
    return redirect('payment_failed')

# ===== OTHER PAGES =====

def services(request):
    """Services page"""
    return render(request, 'services.html')

def contact_page(request):
    """Contact page"""
    return render(request, 'contact.html')

def about(request):
    """About page"""
    return render(request, 'about.html')

def partnership(request):
    """Partnership page"""
    return render(request, 'partnership.html')

def education(request):
    """Education page"""
    return render(request, 'education.html')

# ===== ADMIN VIEWS =====

def admin_dashboard_view(request):
    """Custom admin dashboard"""
    # Simple admin authentication
    if not request.user.is_superuser and 'admin_logged_in' not in request.session:
        # Show admin login form
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            # Hardcoded admin credentials
            if username == 'admin' and password == 'Admin@2024':
                request.session['admin_logged_in'] = True
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid admin credentials')
                return render(request, 'admin/login.html')
        
        return render(request, 'admin/login.html')
    
    # User is authenticated as admin
    try:
        # Get statistics
        total_users = MfalmeUsers.objects.count()
        active_users = MfalmeUsers.objects.filter(is_active=True).count()
        verified_users = MfalmeUsers.objects.filter(email_verified=True).count()
        today_users = MfalmeUsers.objects.filter(date_joined__date=timezone.now().date()).count()
        
        # Get recent registrations
        recent_users = MfalmeUsers.objects.all().order_by('-date_joined')[:20]
        
        # Get payment statistics
        total_payments = PaymentTransaction.objects.count()
        successful_payments = PaymentTransaction.objects.filter(status='completed').count()
        pending_payments = PaymentTransaction.objects.filter(status='initiated').count()
        
        # Get recent payments
        recent_payments = PaymentTransaction.objects.all().order_by('-created_at')[:50]
        
        # Calculate revenue
        total_revenue_usd = sum(t.amount for t in PaymentTransaction.objects.filter(status='completed'))
        
        context = {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'today_users': today_users,
            'recent_users': recent_users,
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'total_revenue_usd': total_revenue_usd,
            'recent_payments': recent_payments,
            'current_time': timezone.now(),
        }
        
        return render(request, 'admin_dashboard.html', context)
        
    except Exception as e:
        print(f"❌ Admin dashboard error: {str(e)}")
        messages.error(request, 'Error loading dashboard')
        return render(request, 'admin_dashboard.html', {'error': str(e)})

def admin_logout_view(request):
    """Admin logout"""
    if 'admin_logged_in' in request.session:
        del request.session['admin_logged_in']
    messages.success(request, 'Admin logged out successfully')
    return redirect('admin_dashboard')

# ===== TESTING FUNCTIONS =====

def test_email_delivery(request):
    """Test email delivery with different clients"""
    test_email = request.GET.get('email', settings.DEFAULT_FROM_EMAIL)
    
    # Test with simple HTML
    html_content = """
    <table width="100%" bgcolor="#f5f5f5">
        <tr>
            <td align="center">
                <table width="600" bgcolor="white" style="border-radius:10px;">
                    <tr>
                        <td bgcolor="#FFD700" style="padding:20px; text-align:center;">
                            <h1 style="color:#000; margin:0;">TEST EMAIL</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <p>This is a test email to check CSS rendering.</p>
                            <p style="color:#FFD700; font-weight:bold;">If this text is gold, CSS is working!</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """
    
    try:
        success = send_email_compatible(
            subject='Email CSS Test - MFALME',
            html_content=html_content,
            text_content='Test email plain text',
            recipient_list=[test_email],
            from_email=f"MFALME Test <{settings.DEFAULT_FROM_EMAIL}>"
        )
        
        if success:
            return HttpResponse(f"""
            <h1>✅ Test Email Sent!</h1>
            <p>Check your inbox: {test_email}</p>
            <p>Check:</p>
            <ul>
                <li>Primary inbox</li>
                <li>Spam folder</li>
                <li>Promotions tab (Gmail)</li>
            </ul>
            <p>Email uses table-based layout for maximum compatibility.</p>
            """)
        else:
            return HttpResponse(f"<h1>❌ Test Failed</h1><p>Could not send email to {test_email}</p>")
        
    except Exception as e:
        return HttpResponse(f"<h1>❌ Test Failed</h1><pre>{str(e)}</pre>")

# ===== CONTEXT PROCESSOR =====

def user_authenticated(request):
    """Global context processor for user authentication status"""
    context = {
        'user_authenticated': 'user_id' in request.session,
        'user_email': request.session.get('user_email', ''),
        'username': request.session.get('username', ''),
        'soldier_id': request.session.get('soldier_id', ''),
        'elite_rank': request.session.get('elite_rank', 'Guest')
    }
    
    # Add user object if authenticated
    if 'user_id' in request.session:
        try:
            user = MfalmeUsers.objects.get(id=request.session['user_id'])
            context['user'] = user
            context['is_verified'] = user.email_verified
        except:
            pass
    
    return context

# ===== ERROR HANDLERS =====

def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page"""
    return render(request, '500.html', status=500)

# ===== API ENDPOINTS =====

@csrf_exempt
def api_check_email(request):
    """API endpoint to check if email exists"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'error': 'Email required'}, status=400)
    
    exists = MfalmeUsers.objects.filter(email=email).exists()
    
    return JsonResponse({
        'exists': exists,
        'email': email,
        'message': 'Email already registered' if exists else 'Email available'
    })

@csrf_exempt
def api_get_user_stats(request):
    """API endpoint for user statistics"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        stats = {
            'soldier_id': user.soldier_id,
            'username': user.username,
            'email_verified': user.email_verified,
            'account_age_days': (timezone.now() - user.date_joined).days,
            'elite_rank': getattr(user, 'elite_rank', 'Recruit'),
            'registration_date': user.date_joined.strftime('%Y-%m-%d'),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except MfalmeUsers.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

def register_page(request):
    """Handle registration page"""
    if request.method == 'POST':
        return create_account(request)
    
    return redirect(f'{reverse("login_page")}?tab=signup')

# ===== BOOKING/CONTACT FORM HANDLER =====
@csrf_exempt
def booking(request):
    """Handle booking/contact form submissions"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('contact')
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip().lower()
        package = request.POST.get('package', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not name or not phone or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact')
        
        # Send notification email
        subject = f'📞 New Contact Form Submission: {name}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <tr>
                    <td style="background: #FFD700; color: #000; padding: 30px; text-align: center;">
                        <h1 style="margin: 0;">📞 NEW CONTACT FORM</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 30px;">
                        <p><strong>Name:</strong> {name}</p>
                        <p><strong>Phone:</strong> {phone}</p>
                        <p><strong>Email:</strong> {email or 'Not provided'}</p>
                        <p><strong>Package:</strong> {package or 'Not specified'}</p>
                        <p><strong>Message:</strong><br>{message}</p>
                        <p><strong>Submitted:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>IP Address:</strong> {get_client_ip(request)}</p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = f"""
        NEW CONTACT FORM SUBMISSION
        
        Name: {name}
        Phone: {phone}
        Email: {email or 'Not provided'}
        Package: {package or 'Not specified'}
        
        Message:
        {message}
        
        Submission Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        IP Address: {get_client_ip(request)}
        """
        
        # Send to admin
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        for admin_email in admin_emails:
            send_email_compatible(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_list=[admin_email],
                from_email=f"MFALME Contact Form <{settings.DEFAULT_FROM_EMAIL}>"
            )
        
        messages.success(request, 'Thank you for your message! We will contact you shortly.')
        return redirect('contact')
        
    except Exception as e:
        print(f"❌ Booking form error: {str(e)}")
        messages.error(request, 'Failed to submit form. Please try again.')
        return redirect('contact')

# ===== TEST ALL EMAILS =====

def test_all_emails(request):
    """Test all email types"""
    try:
        # Create test user
        test_user, created = MfalmeUsers.objects.get_or_create(
            email='test@mfalmebetterdays.com',
            defaults={
                'username': 'Test Soldier',
                'phone': '+254700000000',
                'soldier_id': 'TEST-001',
                'password': hash_password('test123'),
                'email_verified': True,
                'is_active': True
            }
        )
        
        results = []
        
        # Create a mock request object
        class MockRequest:
            scheme = 'https'
            def get_host(self):
                return 'mfalmebetterdayscapital.com'
        
        mock_request = MockRequest()
        
        # Test 1: Verification Email
        ver_result = send_verification_email(test_user, '123456', mock_request)
        results.append(f"Verification Email: {'✅ SUCCESS' if ver_result else '❌ FAILED'}")
        
        # Test 2: Welcome Email
        welcome_result = send_welcome_email(test_user, mock_request)
        results.append(f"Welcome Email: {'✅ SUCCESS' if welcome_result else '❌ FAILED'}")
        
        # Test 3: Admin Notification
        admin_result = notify_admin_new_registration(test_user, mock_request)
        results.append(f"Admin Notification: {'✅ SUCCESS' if admin_result else '❌ FAILED'}")
        
        # Test 4: Create a mock transaction for other tests
        test_transaction = PaymentTransaction.objects.create(
            user=test_user,
            reference='TEST-TRANS-001',
            amount=200,
            currency='USD',
            status='completed',
            payment_type='package',
            metadata={
                'package_name': 'Test Package',
                'amount_usd': 200,
                'amount_kes': 32000,
                'exchange_rate': 160
            }
        )
        
        # Test 5: Package Activation
        package_result = send_package_activation_email(test_user, test_transaction)
        results.append(f"Package Activation: {'✅ SUCCESS' if package_result else '❌ FAILED'}")
        
        # Email configuration
        email_config = f"""
        📧 EMAIL CONFIGURATION:
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        From: {settings.DEFAULT_FROM_EMAIL}
        TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
        """
        
        return render(request, 'admin/email_test.html', {
            'results': results,
            'email_config': email_config,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return HttpResponse(f"<h2>Test Failed</h2><pre>{str(e)}</pre>")

# ===== EMERGENCY FIX =====

def emergency_email_fix(request):
    """Immediate fix for email issues"""
    import smtplib
    
    try:
        smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        smtp.starttls()
        smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        smtp.quit()
        
        return HttpResponse("""
        <h1>✅ EMAIL SYSTEM WORKING</h1>
        <p>SMTP connection successful!</p>
        <p>Now test:</p>
        <ul>
            <li><a href="/test-email-delivery/">Test Email Delivery</a></li>
            <li><a href="/test-all-emails/">Test All Emails</a></li>
            <li><a href="/admin-dashboard/">Admin Dashboard</a></li>
        </ul>
        """)
        
    except Exception as e:
        return HttpResponse(f"""
        <h1>❌ EMAIL SYSTEM BROKEN</h1>
        <pre>Error: {str(e)}</pre>
        <p>Check settings.py:</p>
        <pre>
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
        </pre>
        <p>For Gmail, enable 2FA and generate App Password</p>
        """)
    

# ===== TESTING FUNCTIONS =====

def test_email_delivery(request):
    """Test email delivery with different clients"""
    test_email = request.GET.get('email', settings.DEFAULT_FROM_EMAIL)
    
    # Test with simple HTML
    html_content = """
    <table width="100%" bgcolor="#f5f5f5">
        <tr>
            <td align="center">
                <table width="600" bgcolor="white" style="border-radius:10px;">
                    <tr>
                        <td bgcolor="#FFD700" style="padding:20px; text-align:center;">
                            <h1 style="color:#000; margin:0;">TEST EMAIL</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <p>This is a test email to check CSS rendering.</p>
                            <p style="color:#FFD700; font-weight:bold;">If this text is gold, CSS is working!</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """
    
    try:
        success = send_email_compatible(
            subject='Email CSS Test - MFALME',
            html_content=html_content,
            text_content='Test email plain text',
            recipient_list=[test_email],
            from_email=f"MFALME Test <{settings.DEFAULT_FROM_EMAIL}>"
        )
        
        if success:
            return HttpResponse(f"""
            <h1>✅ Test Email Sent!</h1>
            <p>Check your inbox: {test_email}</p>
            <p>Check:</p>
            <ul>
                <li>Primary inbox</li>
                <li>Spam folder</li>
                <li>Promotions tab (Gmail)</li>
            </ul>
            <p>Email uses table-based layout for maximum compatibility.</p>
            """)
        else:
            return HttpResponse(f"<h1>❌ Test Failed</h1><p>Could not send email to {test_email}</p>")
        
    except Exception as e:
        return HttpResponse(f"<h1>❌ Test Failed</h1><pre>{str(e)}</pre>")

# ADD THIS FUNCTION - IT WAS MISSING
def test_smtp_connection(request):
    """Test SMTP connection directly"""
    import smtplib
    
    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()
        
        return HttpResponse(f"""
        <h2>✅ SMTP Connection Successful</h2>
        <pre>
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        User: {settings.EMAIL_HOST_USER}
        Status: Connected & Authenticated
        </pre>
        
        <h3>Now test email sending:</h3>
        <ul>
            <li><a href="/test-email-delivery/">Test Email Delivery</a></li>
            <li><a href="/test-all-emails/">Test All Email Types</a></li>
        </ul>
        """)
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ SMTP Connection Failed</h2>
        <pre>
        Error: {str(e)}
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        User: {settings.EMAIL_HOST_USER}
        </pre>
        
        <h3>Troubleshooting:</h3>
        <ol>
            <li>Check if SMTP is enabled in your email account</li>
            <li>For Gmail: Enable 2FA and generate App Password</li>
            <li>Check firewall settings</li>
            <li>Verify email credentials</li>
        </ol>
        
        <h4>For Gmail users:</h4>
        <ol>
            <li>Go to <a href="https://myaccount.google.com/security" target="_blank">Google Account Security</a></li>
            <li>Enable 2-Step Verification</li>
            <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank">App Passwords</a></li>
            <li>Generate app password for "Mail"</li>
            <li>Use that password in settings.py (not your regular password)</li>
        </ol>
        """)

def test_all_emails(request):
    """Test all email types"""
    try:
        # Create test user
        test_user, created = MfalmeUsers.objects.get_or_create(
            email='test@mfalmebetterdays.com',
            defaults={
                'username': 'Test Soldier',
                'phone': '+254700000000',
                'soldier_id': 'TEST-001',
                'password': hash_password('test123'),
                'email_verified': True,
                'is_active': True
            }
        )
        
        results = []
        
        # Create a mock request object
        class MockRequest:
            scheme = 'https'
            def get_host(self):
                return 'mfalmebetterdayscapital.com'
        
        mock_request = MockRequest()
        
        # Test 1: Verification Email
        ver_result = send_verification_email(test_user, '123456', mock_request)
        results.append(f"Verification Email: {'✅ SUCCESS' if ver_result else '❌ FAILED'}")
        
        # Test 2: Welcome Email
        welcome_result = send_welcome_email(test_user, mock_request)
        results.append(f"Welcome Email: {'✅ SUCCESS' if welcome_result else '❌ FAILED'}")
        
        # Test 3: Admin Notification
        admin_result = notify_admin_new_registration(test_user, mock_request)
        results.append(f"Admin Notification: {'✅ SUCCESS' if admin_result else '❌ FAILED'}")
        
        # Test 4: Create a mock transaction for other tests
        test_transaction = PaymentTransaction.objects.create(
            user=test_user,
            reference='TEST-TRANS-001',
            amount=200,
            currency='USD',
            status='completed',
            payment_type='package',
            metadata={
                'package_name': 'Test Package',
                'amount_usd': 200,
                'amount_kes': 32000,
                'exchange_rate': 160
            }
        )
        
        # Test 5: Package Activation
        package_result = send_package_activation_email(test_user, test_transaction)
        results.append(f"Package Activation: {'✅ SUCCESS' if package_result else '❌ FAILED'}")
        
        # Email configuration
        email_config = f"""
        📧 EMAIL CONFIGURATION:
        Host: {settings.EMAIL_HOST}
        Port: {settings.EMAIL_PORT}
        From: {settings.DEFAULT_FROM_EMAIL}
        TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
        """
        
        return render(request, 'admin/email_test.html', {
            'results': results,
            'email_config': email_config,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return HttpResponse(f"<h2>Test Failed</h2><pre>{str(e)}</pre>")    
    


def dashboard(request):
    """Enhanced dashboard with all features"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, 'Please login to access dashboard.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=user_id)
        
        # Get unlocked videos
        unlocked_videos = UserVideoAccess.objects.filter(user=user).values_list('video_id', flat=True)
        
        # Get enrolled courses
        enrolled_courses = UserCourse.objects.filter(user=user)
        
        # Get user activities
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:10]
        
        # Get support tickets
        support_tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')[:5]
        
        context = {
            'user': user,
            'unlocked_video_ids': list(unlocked_videos),
            'enrolled_courses': enrolled_courses,
            'activities': activities,
            'support_tickets': support_tickets,
        }
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            action='login',
            description='User accessed dashboard',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return render(request, 'dashboard.html', context)
        
    except MfalmeUsers.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('login_page')

# API Endpoints for AJAX calls
@csrf_exempt
def api_get_videos(request):
    """Get videos for user"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Get all active videos
        videos = TrainingVideo.objects.filter(is_active=True).order_by('order')
        
        # Get unlocked videos
        unlocked_videos = UserVideoAccess.objects.filter(user=user).values_list('video_id', flat=True)
        
        video_data = []
        for video in videos:
            video_data.append({
                'id': video.id,
                'title': video.title,
                'category': video.category,
                'duration': video.duration,
                'price': float(video.price),
                'unlocked': video.id in unlocked_videos,
                'views': video.view_count,
                'thumbnail': video.thumbnail.url if video.thumbnail else '',
            })
        
        return JsonResponse({
            'success': True,
            'videos': video_data,
            'unlocked_count': len(unlocked_videos),
            'total_count': videos.count()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_unlock_video(request):
    """Unlock video for user"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        
        if not video_id:
            return JsonResponse({'error': 'Video ID required'}, status=400)
        
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        video = TrainingVideo.objects.get(id=video_id)
        
        # Check if already unlocked
        if UserVideoAccess.objects.filter(user=user, video=video).exists():
            return JsonResponse({'error': 'Video already unlocked'}, status=400)
        
        # Check if free
        if video.price == 0:
            # Free video - unlock immediately
            UserVideoAccess.objects.create(user=user, video=video)
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                action='video_watch',
                description=f'Unlocked free video: {video.title}',
                video=video
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Video unlocked successfully!'
            })
        else:
            # Paid video - create payment
            return JsonResponse({
                'success': False,
                'payment_required': True,
                'price': float(video.price),
                'redirect_url': f'/payment/video/{video.id}/'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_send_support(request):
    """Send support message"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        category = data.get('category', 'general')
        
        if not subject or not message:
            return JsonResponse({'error': 'Subject and message required'}, status=400)
        
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Create support ticket
        ticket = SupportTicket.objects.create(
            user=user,
            subject=subject,
            message=message,
            category=category
        )
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            action='support_request',
            description=f'Submitted support request: {subject}'
        )
        
        # Send notification to admin
        notify_admin_support_ticket(ticket)
        
        return JsonResponse({
            'success': True,
            'message': 'Support request sent successfully!',
            'ticket_id': ticket.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_update_settings(request):
    """Update user settings"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Update basic info
        if 'username' in data:
            user.username = data['username'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'country' in data:
            user.country = data['country'].strip()
        
        # Update password if provided
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if new_password:
            if not current_password:
                return JsonResponse({'error': 'Current password required'}, status=400)
            
            # Verify current password
            if user.password != hash_password(current_password):
                return JsonResponse({'error': 'Current password is incorrect'}, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({'error': 'New passwords do not match'}, status=400)
            
            user.password = hash_password(new_password)
        
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            action='settings_update',
            description='Updated account settings'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_get_activities(request):
    """Get user activities"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:20]
        
        activity_data = []
        for activity in activities:
            activity_data.append({
                'date': activity.created_at.strftime('%b %d, %Y %H:%M'),
                'action': activity.get_action_display(),
                'description': activity.description,
                'icon': get_activity_icon(activity.action)
            })
        
        return JsonResponse({
            'success': True,
            'activities': activity_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_activity_icon(action):
    """Get icon for activity type"""
    icons = {
        'login': 'fa-sign-in-alt',
        'video_watch': 'fa-video',
        'course_access': 'fa-book',
        'payment_made': 'fa-credit-card',
        'support_request': 'fa-headset',
        'settings_update': 'fa-cog',
    }
    return icons.get(action, 'fa-circle')

# Payment for video
def payment_video(request, video_id):
    """Handle video payment"""
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to make payment.')
        return redirect('login_page')
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        video = TrainingVideo.objects.get(id=video_id)
        
        # Check if already unlocked
        if UserVideoAccess.objects.filter(user=user, video=video).exists():
            messages.info(request, 'You already have access to this video.')
            return redirect('dashboard')
        
        # Create payment transaction
        reference = f"VIDEO-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=video.price,
            currency='USD',
            status='initiated',
            payment_type='video_unlock',
            metadata={
                'video_id': video.id,
                'video_title': video.title,
                'description': f'Unlock video: {video.title}',
            }
        )
        
        # Store in session
        request.session['payment_reference'] = reference
        request.session['payment_type'] = 'video'
        request.session['video_id'] = video.id
        
        # Redirect to payment gateway
        return redirect(f'/payment/initiate/{reference}/')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard')    
    

# ===== VIDEO PAYMENT VIEWS =====
@csrf_exempt
def initiate_video_payment(request):
    """Initiate payment for video unlocking"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        amount = data.get('amount', 0)
        
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Generate unique reference
        reference = f"VIDEO-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=amount,
            currency='USD',
            payment_type='video',
            status='pending',
            metadata={
                'video_id': video_id,
                'type': 'video_unlock',
                'user_id': user.id,
                'soldier_id': user.soldier_id
            }
        )
        
        # Convert USD to KES for Paystack
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(amount)
        
        # Initialize Paystack payment
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        paystack_data = {
            'email': user.email,
            'amount': kes_cents,
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Service",
                        'variable_name': "service",
                        'value': "Video Unlock"
                    },
                    {
                        'display_name': "Amount USD",
                        'variable_name': "amount_usd",
                        'value': f"${amount}"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=paystack_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                # Update transaction with Paystack data
                transaction.paystack_data = result['data']
                transaction.save()
                
                return JsonResponse({
                    'success': True,
                    'payment_url': result['data']['authorization_url'],
                    'reference': reference
                })
        
        return JsonResponse({'error': 'Payment initialization failed'}, status=400)
        
    except Exception as e:
        print(f"Video payment error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def initiate_course_payment(request):
    """Initiate payment for course enrollment"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        amount = data.get('amount', 0)
        
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Generate reference
        reference = f"COURSE-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=amount,
            currency='USD',
            payment_type='course',
            status='pending',
            metadata={
                'course_id': course_id,
                'type': 'course_enrollment',
                'user_id': user.id
            }
        )
        
        # Convert to KES
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(amount)
        
        # Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        paystack_data = {
            'email': user.email,
            'amount': kes_cents,
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Service",
                        'variable_name': "service",
                        'value': "Course Enrollment"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=paystack_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                transaction.paystack_data = result['data']
                transaction.save()
                
                return JsonResponse({
                    'success': True,
                    'payment_url': result['data']['authorization_url'],
                    'reference': reference
                })
        
        return JsonResponse({'error': 'Payment failed'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def initiate_mentorship_payment(request):
    """Initiate payment for mentorship booking"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Please login'}, status=401)
    
    try:
        data = json.loads(request.body)
        mentorship_id = data.get('mentorship_id')
        amount = data.get('amount', 0)
        
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Generate reference
        reference = f"MENTOR-{user.soldier_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            user=user,
            reference=reference,
            amount=amount,
            currency='USD',
            payment_type='mentorship',
            status='pending',
            metadata={
                'mentorship_id': mentorship_id,
                'type': 'mentorship_booking',
                'user_id': user.id
            }
        )
        
        # Convert to KES
        kes_cents, exchange_rate, kes_amount = convert_usd_to_kes_cents(amount)
        
        # Paystack
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        paystack_data = {
            'email': user.email,
            'amount': kes_cents,
            'reference': reference,
            'currency': 'KES',
            'callback_url': f"{request.scheme}://{request.get_host()}/payment/verify/{reference}/",
            'metadata': {
                'custom_fields': [
                    {
                        'display_name': "Soldier ID",
                        'variable_name': "soldier_id",
                        'value': user.soldier_id
                    },
                    {
                        'display_name': "Service",
                        'variable_name': "service",
                        'value': "Mentorship Booking"
                    }
                ]
            }
        }
        
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=headers,
            json=paystack_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status'):
                transaction.paystack_data = result['data']
                transaction.save()
                
                return JsonResponse({
                    'success': True,
                    'payment_url': result['data']['authorization_url'],
                    'reference': reference
                })
        
        return JsonResponse({'error': 'Payment failed'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ===== API ENDPOINTS FOR DASHBOARD =====

@csrf_exempt
def api_get_videos(request):
    """Get videos for dashboard"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        user = MfalmeUsers.objects.get(id=request.session['user_id'])
        
        # Get all videos
        videos = TrainingVideo.objects.filter(is_active=True).order_by('order')
        
        # Get unlocked videos
        unlocked_ids = UserVideoAccess.objects.filter(user=user).values_list('video_id', flat=True)
        
        video_data = []
        for video in videos:
            video_data.append({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'category': video.category,
                'duration': video.duration,
                'price': float(video.price),
                'thumbnail': video.thumbnail.url if video.thumbnail else '',
                'video_url': video.video_url,
                'unlocked': video.id in unlocked_ids,
                'views': video.view_count,
                'order': video.order
            })
        
        return JsonResponse({
            'success': True,
            'videos': video_data,
            'unlocked_count': len(unlocked_ids),
            'total_count': videos.count()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_get_mentorship_programs(request):
    """Get mentorship programs for dashboard"""
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        programs = MentorshipProgram.objects.filter(is_active=True).order_by('price')
        
        program_data = []
        for program in programs:
            program_data.append({
                'id': program.id,
                'title': program.title,
                'description': program.description,
                'duration': program.duration,
                'sessions': program.sessions,
                'price': float(program.price),
                'success_rate': program.success_rate,
                'image': program.image.url if program.image else '',
                'features': program.features
            })
        
        return JsonResponse({
            'success': True,
            'programs': program_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)    
    
    
# ===== PARTNERSHIP APPLICATION VIEW =====
@csrf_exempt
def submit_partnership_application(request):
    """Handle partnership application form submission"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method. Use POST.'
        }, status=400)
    
    try:
        # Get JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Handle form data
            data = request.POST.dict()
        
        print(f"📝 Partnership application received: {data.get('company_name', 'Unknown Company')}")
        
        # Prepare email subject
        tier = data.get('partnership_tier', 'general')
        tier_names = {
            'bronze': 'Bronze Partnership',
            'silver': 'Silver Partnership',
            'gold': 'Gold Partnership',
            'platinum': 'Platinum Partnership',
            'portfolio': 'Portfolio Management'
        }
        
        tier_name = tier_names.get(tier, 'Partnership Inquiry')
        
        # HTML email content for admin
        admin_html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <!-- Header -->
                <tr>
                    <td style="background: #FFD700; padding: 30px; text-align: center;">
                        <h1 style="color: #000; margin: 0; font-size: 24px;">🚀 NEW PARTNERSHIP APPLICATION</h1>
                        <p style="color: #000; margin: 10px 0 0 0; font-weight: bold;">{tier_name.upper()}</p>
                    </td>
                </tr>
                
                <!-- Content -->
                <tr>
                    <td style="padding: 30px;">
                        <h2 style="color: #0A1520; border-bottom: 2px solid #FFD700; padding-bottom: 10px;">📋 Application Details</h2>
                        
                        <!-- Contact Information -->
                        <div style="margin-bottom: 25px;">
                            <h3 style="color: #FFD700;">👤 Contact Information</h3>
                            <table width="100%" style="border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Full Name:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('contact_name', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Position:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('contact_position', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('contact_email', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Phone:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('contact_phone', 'N/A')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <!-- Company Information -->
                        <div style="margin-bottom: 25px;">
                            <h3 style="color: #FFD700;">🏢 Company Information</h3>
                            <table width="100%" style="border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Company Name:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('company_name', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Website:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('company_website', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Type:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('company_type', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Established:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('year_established', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Headquarters:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('headquarters', 'N/A')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <!-- Financial Details -->
                        <div style="margin-bottom: 25px;">
                            <h3 style="color: #FFD700;">💰 Financial Details</h3>
                            <table width="100%" style="border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>AUM Range:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('aum_range', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Client Count:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('client_count', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Trading Volume:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('trading_volume', 'N/A')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Primary Markets:</strong></td>
                                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{data.get('primary_markets', 'N/A')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <!-- Partnership Objectives -->
                        <div style="margin-bottom: 25px;">
                            <h3 style="color: #FFD700;">🎯 Partnership Objectives</h3>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #FFD700;">
                                {data.get('partnership_objectives', 'N/A').replace(chr(10), '<br>')}
                            </div>
                        </div>
                        
                        <!-- Technology Stack -->
                        {f'''
                        <div style="margin-bottom: 25px;">
                            <h3 style="color: #FFD700;">💻 Technology Stack</h3>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                {data.get('technology_stack', 'N/A').replace(chr(10), '<br>')}
                            </div>
                        </div>
                        ''' if data.get('technology_stack') else ''}
                        
                        <!-- Agreement Status -->
                        <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                            <h3 style="color: #0A1520; margin-top: 0;">📜 Agreement Status</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li><strong>NDA Agreement:</strong> {'✅ YES' if data.get('agree_nda') else '❌ NO'}</li>
                                <li><strong>Terms Accepted:</strong> {'✅ YES' if data.get('agree_terms') else '❌ NO'}</li>
                                <li><strong>Contact Consent:</strong> {'✅ YES' if data.get('agree_contact') else '❌ NO'}</li>
                            </ul>
                        </div>
                        
                        <!-- Footer -->
                        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #666; font-size: 12px;">
                                <strong>Application ID:</strong> PART-{datetime.now().strftime('%Y%m%d%H%M%S')}<br>
                                <strong>Submitted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                                <strong>IP Address:</strong> {get_client_ip(request)}
                            </p>
                        </div>
                    </td>
                </tr>
                
                <!-- Action Required Footer -->
                <tr>
                    <td style="background: #0A1520; color: #FFD700; padding: 20px; text-align: center;">
                        <h3 style="margin: 0 0 10px 0;">🎯 ACTION REQUIRED</h3>
                        <p style="margin: 0; font-size: 14px;">
                            Please review this application within 24 hours and contact the applicant.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Plain text version for admin
        admin_text_content = f"""
        🚀 NEW PARTNERSHIP APPLICATION - {tier_name.upper()}
        {'='*70}
        
        📋 APPLICATION DETAILS
        {'='*70}
        
        👤 CONTACT INFORMATION:
        Full Name: {data.get('contact_name', 'N/A')}
        Position: {data.get('contact_position', 'N/A')}
        Email: {data.get('contact_email', 'N/A')}
        Phone: {data.get('contact_phone', 'N/A')}
        
        🏢 COMPANY INFORMATION:
        Company Name: {data.get('company_name', 'N/A')}
        Website: {data.get('company_website', 'N/A')}
        Type: {data.get('company_type', 'N/A')}
        Established: {data.get('year_established', 'N/A')}
        Headquarters: {data.get('headquarters', 'N/A')}
        
        💰 FINANCIAL DETAILS:
        AUM Range: {data.get('aum_range', 'N/A')}
        Client Count: {data.get('client_count', 'N/A')}
        Trading Volume: {data.get('trading_volume', 'N/A')}
        Primary Markets: {data.get('primary_markets', 'N/A')}
        
        🎯 PARTNERSHIP OBJECTIVES:
        {data.get('partnership_objectives', 'N/A')}
        
        💻 TECHNOLOGY STACK:
        {data.get('technology_stack', 'N/A')}
        
        📜 AGREEMENT STATUS:
        NDA Agreement: {'YES' if data.get('agree_nda') else 'NO'}
        Terms Accepted: {'YES' if data.get('agree_terms') else 'NO'}
        Contact Consent: {'YES' if data.get('agree_contact') else 'NO'}
        
        {'='*70}
        Application ID: PART-{datetime.now().strftime('%Y%m%d%H%M%S')}
        Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        IP Address: {get_client_ip(request)}
        {'='*70}
        
        🎯 ACTION REQUIRED: Review within 24 hours
        {'='*70}
        """
        
        # Send email to admin(s)
        admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
        
        admin_success = True
        for admin_email in admin_emails:
            try:
                send_email_compatible(
                    subject=f'🚀 Partnership Application: {data.get("company_name", "Unknown")} - {tier_name}',
                    html_content=admin_html_content,
                    text_content=admin_text_content,
                    recipient_list=[admin_email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )
                print(f"✅ Partnership application sent to admin: {admin_email}")
            except Exception as email_error:
                admin_success = False
                print(f"❌ Failed to send to admin {admin_email}: {str(email_error)}")
        
        # Send confirmation to applicant
        applicant_email = data.get('contact_email')
        if applicant_email:
            try:
                # Applicant confirmation HTML
                applicant_html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: #FFD700; padding: 30px; text-align: center;">
                                <h1 style="color: #000; margin: 0; font-size: 24px;">🤝 THANK YOU!</h1>
                                <p style="color: #000; margin: 10px 0 0 0; font-weight: bold;">Your Partnership Application Has Been Received</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px;">
                                <p style="font-size: 16px; margin-bottom: 20px;">
                                    Dear <strong>{data.get('contact_name')}</strong>,
                                </p>
                                
                                <p style="font-size: 16px; margin-bottom: 20px;">
                                    Thank you for submitting your partnership application for the <strong>{tier_name}</strong> with Mfalme Betterdays Capital.
                                </p>
                                
                                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                                    <h3 style="color: #FFD700; margin-top: 0;">📋 Application Summary</h3>
                                    <p><strong>Company:</strong> {data.get('company_name')}</p>
                                    <p><strong>Application Reference:</strong> PART-{datetime.now().strftime('%Y%m%d%H%M%S')}</p>
                                    <p><strong>Partnership Tier:</strong> {tier_name}</p>
                                </div>
                                
                                <!-- Next Steps -->
                                <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                                    <h3 style="color: #0A1520; margin-top: 0;">🚀 Next Steps</h3>
                                    <ol style="margin: 0; padding-left: 20px;">
                                        <li><strong>Review Process:</strong> Our executive team will review your application within 24 hours</li>
                                        <li><strong>Initial Contact:</strong> We'll reach out to schedule a discovery call</li>
                                        <li><strong>NDA & Documentation:</strong> Formal NDA and partnership agreement preparation</li>
                                        <li><strong>Onboarding:</strong> Integration into our partner ecosystem</li>
                                    </ol>
                                </div>
                                
                                <!-- Timeline -->
                                <div style="margin-bottom: 25px;">
                                    <h3 style="color: #FFD700;">⏰ Estimated Timeline</h3>
                                    <table width="100%" style="border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 10px; border: 1px solid #eee;"><strong>Step 1:</strong> Application Review</td>
                                            <td style="padding: 10px; border: 1px solid #eee; text-align: right;">24-48 hours</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; border: 1px solid #eee;"><strong>Step 2:</strong> Initial Discussion</td>
                                            <td style="padding: 10px; border: 1px solid #eee; text-align: right;">1-3 days</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; border: 1px solid #eee;"><strong>Step 3:</strong> Agreement Finalization</td>
                                            <td style="padding: 10px; border: 1px solid #eee; text-align: right;">3-5 days</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 10px; border: 1px solid #eee;"><strong>Step 4:</strong> Full Onboarding</td>
                                            <td style="padding: 10px; border: 1px solid #eee; text-align: right;">1-2 weeks</td>
                                        </tr>
                                    </table>
                                </div>
                                
                                <!-- Contact Information -->
                                <div style="text-align: center; padding: 20px; background: #0A1520; border-radius: 8px; color: white;">
                                    <h3 style="color: #FFD700; margin-top: 0;">📞 Need Immediate Assistance?</h3>
                                    <p style="margin: 10px 0;">
                                        <strong>Partnership Team:</strong><br>
                                        📧 Email: partnership@mfalmebetterdayscapital.com<br>
                                        📱 Phone: +254 706 286 667<br>
                                        ⏰ Hours: Mon-Fri, 9:00 AM - 5:00 PM EAT
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background: #0A1520; color: #FFD700; padding: 20px; text-align: center;">
                                <p style="margin: 0; font-size: 12px;">
                                    This is an automated confirmation. Please do not reply to this email.<br>
                                    © {datetime.now().year} MFALME BETTERDAYS CAPITAL. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                
                # Plain text for applicant
                applicant_text_content = f"""
                🤝 PARTNERSHIP APPLICATION CONFIRMATION
                {'='*70}
                
                Dear {data.get('contact_name')},
                
                Thank you for submitting your partnership application for the {tier_name} with Mfalme Betterdays Capital.
                
                📋 APPLICATION SUMMARY:
                Company: {data.get('company_name')}
                Application Reference: PART-{datetime.now().strftime('%Y%m%d%H%M%S')}
                Partnership Tier: {tier_name}
                
                🚀 NEXT STEPS:
                1. Review Process: Our executive team will review your application within 24 hours
                2. Initial Contact: We'll reach out to schedule a discovery call
                3. NDA & Documentation: Formal NDA and partnership agreement preparation
                4. Onboarding: Integration into our partner ecosystem
                
                ⏰ ESTIMATED TIMELINE:
                • Step 1: Application Review - 24-48 hours
                • Step 2: Initial Discussion - 1-3 days
                • Step 3: Agreement Finalization - 3-5 days
                • Step 4: Full Onboarding - 1-2 weeks
                
                📞 NEED IMMEDIATE ASSISTANCE?
                Partnership Team:
                📧 Email: partnership@mfalmebetterdayscapital.com
                📱 Phone: +254 706 286 667
                ⏰ Hours: Mon-Fri, 9:00 AM - 5:00 PM EAT
                
                {'='*70}
                This is an automated confirmation. Please do not reply to this email.
                {'='*70}
                """
                
                send_email_compatible(
                    subject=f'🤝 Partnership Application Confirmation - {data.get("company_name")}',
                    html_content=applicant_html_content,
                    text_content=applicant_text_content,
                    recipient_list=[applicant_email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )
                print(f"✅ Confirmation email sent to applicant: {applicant_email}")
                
            except Exception as applicant_email_error:
                print(f"⚠️ Failed to send confirmation to applicant: {str(applicant_email_error)}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Partnership application submitted successfully!',
            'application_id': f'PART-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'timestamp': datetime.now().isoformat(),
            'admin_notified': admin_success,
            'applicant_notified': bool(applicant_email)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data provided.'
        }, status=400)
        
    except Exception as e:
        print(f"❌ Partnership application error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)    


# ===== CONTACT FORM SUBMISSION FUNCTION =====

@csrf_exempt
def contact_form_submit(request):
    """Handle contact form submission with AJAX support"""
    if request.method == 'POST':
        try:
            print("📧 Contact form submission received")
            
            # Get form data
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # Extract data
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            email = data.get('email', '').strip().lower()
            package = data.get('package', '').strip()
            message = data.get('message', '').strip()
            
            print(f"📝 Form data: {name}, {phone}, {package}")
            
            # Basic validation
            errors = []
            
            if not name or len(name) < 2:
                errors.append({'field': 'name', 'message': 'Please enter your full name'})
            
            if not phone:
                errors.append({'field': 'phone', 'message': 'Phone number is required'})
            else:
                # Clean phone number
                import re
                digits = re.sub(r'[^\d]', '', phone)
                if len(digits) < 10:
                    errors.append({'field': 'phone', 'message': 'Please enter a valid phone number'})
            
            if not package or package == '':
                errors.append({'field': 'package', 'message': 'Please select a package'})
            
            if not message or len(message) < 20:
                errors.append({'field': 'message', 'message': 'Message must be at least 20 characters'})
            elif len(message) > 500:
                errors.append({'field': 'message', 'message': 'Message cannot exceed 500 characters'})
            
            # Email validation (optional)
            if email:
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(email)
                except ValidationError:
                    errors.append({'field': 'email', 'message': 'Please enter a valid email address'})
            
            # If there are errors, return them
            if errors:
                print(f"❌ Form validation errors: {errors}")
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
            
            # Get client info
            ip_address = get_client_ip(request)
            location = get_location_from_ip(ip_address)
            
            # Prepare email subject
            subject = f"📞 New Contact: {name} - {package}"
            
            # HTML content for admin
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 20px; }}
                    .header {{ background: #FFD700; color: #000; padding: 20px; text-align: center; }}
                    .content {{ background: white; padding: 30px; }}
                    .field {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; color: #666; }}
                    .value {{ color: #333; margin-top: 5px; }}
                    .highlight {{ background: #fff8e1; padding: 10px; border-left: 4px solid #FFD700; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📞 NEW CONTACT FORM</h1>
                        <p>MFALME BETTERDAYS CAPITAL</p>
                    </div>
                    <div class="content">
                        <div class="highlight">
                            <strong>Time:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                            <strong>IP:</strong> {ip_address}<br>
                            <strong>Location:</strong> {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}
                        </div>
                        
                        <div class="field">
                            <div class="label">👤 Full Name:</div>
                            <div class="value">{name}</div>
                        </div>
                        
                        <div class="field">
                            <div class="label">📱 WhatsApp Number:</div>
                            <div class="value">{phone}</div>
                        </div>
                        
                        <div class="field">
                            <div class="label">📧 Email Address:</div>
                            <div class="value">{email if email else 'Not provided'}</div>
                        </div>
                        
                        <div class="field">
                            <div class="label">📦 Selected Package:</div>
                            <div class="value" style="color: #FFD700; font-weight: bold;">{package}</div>
                        </div>
                        
                        <div class="field">
                            <div class="label">💬 Message:</div>
                            <div class="value" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                {message.replace(chr(10), '<br>')}
                            </div>
                        </div>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #FFD700;">
                            <p style="color: #666; font-size: 12px;">
                                <strong>ACTION REQUIRED:</strong> Contact within 24 hours<br>
                                <strong>Priority:</strong> {'HIGH' if 'Lifetime' in package or 'Leveraging' in package else 'MEDIUM'}
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            NEW CONTACT FORM - MFALME BETTERDAYS CAPITAL
            
            📋 CONTACT DETAILS:
            Name: {name}
            Phone: {phone}
            Email: {email if email else 'Not provided'}
            Package: {package}
            
            💬 MESSAGE:
            {message}
            
            📊 SUBMISSION INFO:
            Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
            IP Address: {ip_address}
            Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}
            
            🎯 ACTION REQUIRED: Contact within 24 hours!
            """
            
            # Send email to admin
            admin_emails = getattr(settings, 'ADMIN_EMAILS', ['mfalmebetterdays@gmail.com'])
            
            email_sent = False
            try:
                for admin_email in admin_emails:
                    send_email_compatible(
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        recipient_list=[admin_email],
                        from_email=settings.DEFAULT_FROM_EMAIL
                    )
                email_sent = True
                print(f"✅ Contact form email sent to admins")
            except Exception as email_error:
                print(f"❌ Email sending error: {str(email_error)}")
                # Continue anyway - we'll still show success to user
            
            # Send confirmation to user if email provided
            user_confirmation_sent = False
            if email:
                try:
                    user_subject = f"✅ Message Received - Mfalme Betterdays Capital"
                    
                    user_html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                    </head>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                            <tr>
                                <td style="background: #FFD700; padding: 30px; text-align: center;">
                                    <h1 style="color: #000; margin: 0; font-size: 24px;">✅ THANK YOU!</h1>
                                    <p style="color: #000; margin: 10px 0 0 0;">Your Message Has Been Received</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 30px;">
                                    <p>Dear <strong>{name}</strong>,</p>
                                    
                                    <p>Thank you for contacting Mfalme Betterdays Capital!</p>
                                    
                                    <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #FFD700;">
                                        <p style="margin: 0 0 10px 0;"><strong>📋 Summary:</strong></p>
                                        <p style="margin: 5px 0;"><strong>Package:</strong> {package}</p>
                                        <p style="margin: 5px 0;"><strong>Submitted:</strong> {timezone.now().strftime('%B %d, %Y at %H:%M')}</p>
                                        <p style="margin: 5px 0;"><strong>Reference:</strong> CONTACT-{timezone.now().strftime('%Y%m%d%H%M')}</p>
                                    </div>
                                    
                                    <h3 style="color: #0A1520;">🚀 What Happens Next?</h3>
                                    <ol style="color: #333; line-height: 1.8;">
                                        <li>Our team will review your inquiry within 24 hours</li>
                                        <li>We'll contact you via WhatsApp/Phone for initial discussion</li>
                                        <li>Schedule a consultation call (if applicable)</li>
                                        <li>Provide detailed package information</li>
                                    </ol>
                                    
                                    <div style="background: #e8f4fd; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                        <h4 style="color: #0A1520; margin-top: 0;">📞 Need Immediate Assistance?</h4>
                                        <p style="margin: 10px 0;">
                                            <strong>Phone/WhatsApp:</strong> +254 706 286 667<br>
                                            <strong>Response Time:</strong> Usually within 2-4 hours
                                        </p>
                                    </div>
                                    
                                    <p>We're excited to help you achieve financial success!</p>
                                    
                                    <p style="margin-top: 30px;">
                                        Best regards,<br>
                                        <strong>Levi Muriuki & The MFALME Team</strong>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </body>
                    </html>
                    """
                    
                    user_text_content = f"""
                    ✅ MESSAGE RECEIVED - MFALME BETTERDAYS CAPITAL
                    
                    Dear {name},
                    
                    Thank you for contacting Mfalme Betterdays Capital!
                    
                    📋 SUMMARY:
                    Package: {package}
                    Submitted: {timezone.now().strftime('%B %d, %Y at %H:%M')}
                    Reference: CONTACT-{timezone.now().strftime('%Y%m%d%H%M')}
                    
                    🚀 WHAT HAPPENS NEXT?
                    1. Our team will review your inquiry within 24 hours
                    2. We'll contact you via WhatsApp/Phone for initial discussion
                    3. Schedule a consultation call (if applicable)
                    4. Provide detailed package information
                    
                    📞 NEED IMMEDIATE ASSISTANCE?
                    Phone/WhatsApp: +254 706 286 667
                    Response Time: Usually within 2-4 hours
                    
                    We're excited to help you achieve financial success!
                    
                    Best regards,
                    Levi Muriuki & The MFALME Team
                    """
                    
                    send_email_compatible(
                        subject=user_subject,
                        html_content=user_html_content,
                        text_content=user_text_content,
                        recipient_list=[email],
                        from_email=settings.DEFAULT_FROM_EMAIL
                    )
                    
                    user_confirmation_sent = True
                    print(f"✅ Confirmation email sent to user: {email}")
                    
                except Exception as user_email_error:
                    print(f"⚠️ Failed to send confirmation to user: {str(user_email_error)}")
            
            # Return success response
            response_data = {
                'success': True,
                'message': 'Message sent successfully! We will contact you shortly.',
                'reference': f'CONTACT-{timezone.now().strftime("%Y%m%d%H%M")}',
                'email_sent': email_sent,
                'user_notified': user_confirmation_sent
            }
            
            print(f"✅ Contact form processed successfully: {response_data}")
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON data")
            return JsonResponse({
                'success': False,
                'errors': [{'field': 'general', 'message': 'Invalid data format. Please try again.'}]
            }, status=400)
            
        except Exception as e:
            print(f"❌ Contact form error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'errors': [{'field': 'general', 'message': 'Server error occurred. Please try again or contact us directly.'}]
            }, status=500)
    
    else:
        return JsonResponse({
            'success': False,
            'errors': [{'field': 'general', 'message': 'Invalid request method. Please submit the form.'}]
        }, status=405)        