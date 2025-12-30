from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import random

# Users model - COMPLETE VERSION
class MfalmeUsers(models.Model):
    # ===== BASIC INFO =====
    email = models.EmailField(unique=True)
    password = models.TextField() 
    username = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    
    # ===== SOLDIER ID SYSTEM =====
    soldier_id = models.CharField(max_length=20, unique=True, blank=True)
    elite_rank = models.CharField(max_length=50, default='Recruit', blank=True)
    
    # ===== VERIFICATION STATUS =====
    email_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_code = models.CharField(max_length=6, blank=True)
    
    # ===== REGISTRATION METADATA =====
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    registration_time = models.DateTimeField(auto_now_add=True)
    registration_device = models.CharField(max_length=200, blank=True)
    registration_location = models.CharField(max_length=200, blank=True)
    
    # ===== TRADING INFORMATION =====
    trading_experience = models.CharField(max_length=50, default='Beginner', blank=True)
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_package = models.CharField(max_length=100, blank=True)
    trading_platform = models.CharField(max_length=100, blank=True)
    
    # ===== USER STATUS =====
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, default='pending', blank=True)
    
    # ===== TIMESTAMPS =====
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # ===== ADDITIONAL FIELDS =====
    whatsapp_number = models.CharField(max_length=30, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    referral_code = models.CharField(max_length=20, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.soldier_id} - {self.username}'
    
    def save(self, *args, **kwargs):
        # Generate SOLDIER ID if not exists
        if not self.soldier_id:
            self.soldier_id = self.generate_soldier_id()
        
        # Set registration time if not set
        if not self.registration_time:
            self.registration_time = timezone.now()
        
        # Set elite rank based on investment
        if self.investment_amount:
            if self.investment_amount >= 10000:
                self.elite_rank = 'Commander'
            elif self.investment_amount >= 5000:
                self.elite_rank = 'Captain'
            elif self.investment_amount >= 1000:
                self.elite_rank = 'Sergeant'
            else:
                self.elite_rank = 'Private'
        
        super().save(*args, **kwargs)
    
    def generate_soldier_id(self):
        """Generate unique soldier ID in format: MFALME-YYYY-XXXXX"""
        year = timezone.now().strftime('%Y')
        unique_code = str(uuid.uuid4())[:8].upper()
        return f"MFALME-{year}-{unique_code}"
    
    def get_registration_data(self):
        """Get complete registration data for emails"""
        return {
            'soldier_id': self.soldier_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'registration_date': self.date_joined.strftime('%Y-%m-%d'),
            'registration_time': self.registration_time.strftime('%H:%M:%S'),
            'registration_ip': self.registration_ip or 'Not recorded',
            'whatsapp': self.whatsapp_number or 'Not provided',
            'telegram': self.telegram_username or 'Not provided',
            'experience': self.trading_experience,
            'preferred_package': self.preferred_package,
            'elite_rank': self.elite_rank,
            'account_age_days': (timezone.now() - self.date_joined).days,
        }
    
    def create_verification_code(self):
        """Create new verification code"""
        code = ''.join(random.choices('0123456789', k=6))
        self.verification_code = code
        self.verification_sent_at = timezone.now()
        self.save()
        
        # Also save in VerificationCode model
        VerificationCode.objects.create(
            user=self,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        return code
    
    class Meta:
        verbose_name = 'Elite Soldier'
        verbose_name_plural = 'Elite Soldiers'
        ordering = ['-date_joined']

# Verification Code model - ENHANCED
class VerificationCode(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.user.soldier_id} - {self.code}'
    
    def save(self, *args, **kwargs):
        # Auto-set expiry (30 minutes from creation)
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        self.is_used = True
        self.save()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Code'
        verbose_name_plural = 'Verification Codes'

# Registration Log model (for tracking)
class RegistrationLog(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    registration_time = models.DateTimeField(default=timezone.now, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f'{self.user.soldier_id} - {self.registration_time}'
    
    class Meta:
        ordering = ['-registration_time']


# Payment Models
class PaymentTransaction(models.Model):
    """Track all payment transactions"""
    TRANSACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_TYPES = [
        ('package', 'Package Payment'),
        ('education', 'Education Program'),
        ('partnership', 'Partnership'),
        ('custom', 'Custom Payment'),
        ('subscription', 'Subscription'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='payments')
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    
    # Package specific
    package_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Education specific
    program_type = models.CharField(max_length=50, blank=True, null=True)
    duration = models.CharField(max_length=20, blank=True, null=True)
    
    # Partnership specific
    partnership_tier = models.CharField(max_length=50, blank=True, null=True)
    
    # Custom payment
    description = models.TextField(blank=True, null=True)
    service_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Paystack data
    paystack_data = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.reference} - {self.user.username} - ${self.amount}"
    
    def is_successful(self):
        return self.status == 'completed'
    
    def get_payment_details(self):
        """Get human-readable payment details"""
        details = {
            'reference': self.reference,
            'amount': f"${self.amount} {self.currency}",
            'status': self.get_status_display(),
            'date': self.created_at.strftime('%B %d, %Y %H:%M'),
        }
        
        if self.package_type:
            details['type'] = f"Package: {self.package_type}"
        elif self.program_type:
            details['type'] = f"Education: {self.program_type}"
        elif self.partnership_tier:
            details['type'] = f"Partnership: {self.partnership_tier}"
        elif self.description:
            details['type'] = f"Custom: {self.description[:50]}..."
        
        return details
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'


class Subscription(models.Model):
    """For recurring payments/subscriptions"""
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=20)  # daily, weekly, monthly, yearly
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    
    # Paystack subscription ID
    paystack_subscription_code = models.CharField(max_length=100, blank=True, null=True)
    
    # Dates
    start_date = models.DateTimeField()
    next_payment_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan}"
    
    def is_active(self):
        return self.status == 'active' and self.next_payment_date > timezone.now()
    
    class Meta:
        ordering = ['-start_date']        