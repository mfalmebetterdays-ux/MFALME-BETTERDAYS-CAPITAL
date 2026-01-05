# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import uuid
import random
from django.utils.timezone import now
from decimal import Decimal


# ==================== CUSTOM USER MANAGER ====================

class MfalmeUserManager(BaseUserManager):
    """Custom manager for MfalmeUsers model"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

## ==================== MAIN USER MODEL ====================

class MfalmeUsers(AbstractBaseUser, PermissionsMixin):
    """Enhanced custom user model"""
    
    # ===== BASIC INFO =====
    email = models.EmailField(unique=True, verbose_name='Email Address')
    username = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=30)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    
    # ===== SOLDIER ID SYSTEM =====
    soldier_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Soldier ID')
    elite_rank = models.CharField(max_length=50, default='Recruit', choices=[
        ('Recruit', 'Recruit'),
        ('Private', 'Private'),
        ('Sergeant', 'Sergeant'),
        ('Captain', 'Captain'),
        ('Commander', 'Commander'),
        ('General', 'General'),
    ])
    
    # ===== VERIFICATION STATUS =====
    email_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # ===== REGISTRATION METADATA =====
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    registration_time = models.DateTimeField(auto_now_add=True)
    registration_device = models.CharField(max_length=200, blank=True)
    registration_location = models.CharField(max_length=200, blank=True)
    
    # ===== TRADING INFORMATION =====
    trading_experience = models.CharField(max_length=50, default='Beginner', choices=[
        ('Beginner', 'Beginner (0-1 years)'),
        ('Intermediate', 'Intermediate (1-3 years)'),
        ('Advanced', 'Advanced (3-5 years)'),
        ('Professional', 'Professional (5+ years)'),
    ])
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_package = models.CharField(max_length=100, blank=True)
    trading_platform = models.CharField(max_length=100, blank=True)
    broker_name = models.CharField(max_length=200, blank=True)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # ===== USER STATUS & PERMISSIONS =====
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending Verification'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('banned', 'Banned'),
        ('inactive', 'Inactive'),
    ])
    
    # ===== ADDITIONAL CONTACT INFO =====
    whatsapp_number = models.CharField(max_length=30, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    # ===== REFERRAL SYSTEM =====
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    referral_count = models.IntegerField(default=0)
    referral_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # ===== TIMESTAMPS =====
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    # ===== PROFILE SETTINGS =====
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    privacy_settings = models.JSONField(default=dict, blank=True)
    
    # ===== STATISTICS =====
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    success_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # ===== NOTES =====
    admin_notes = models.TextField(blank=True)
    
    # ===== GROUPS & PERMISSIONS =====
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='mfalme_users_set',
        related_query_name='mfalme_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='mfalme_users_set',
        related_query_name='mfalme_user',
    )
    
    # ===== MANAGER & USERNAME FIELD =====
    objects = MfalmeUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone']
    
    class Meta:
        verbose_name = 'Elite Soldier'
        verbose_name_plural = 'Elite Soldiers'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['soldier_id']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return f'{self.soldier_id} - {self.email}'
    
    def save(self, *args, **kwargs):
        # Generate SOLDIER ID if not exists
        if not self.soldier_id:
            self.soldier_id = self.generate_soldier_id()
        
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        # Set elite rank based on investment
        if self.investment_amount:
            if self.investment_amount >= Decimal('10000'):
                self.elite_rank = 'Commander'
            elif self.investment_amount >= Decimal('5000'):
                self.elite_rank = 'Captain'
            elif self.investment_amount >= Decimal('1000'):
                self.elite_rank = 'Sergeant'
            elif self.investment_amount >= Decimal('500'):
                self.elite_rank = 'Private'
            else:
                self.elite_rank = 'Recruit'
        
        # Calculate success rate if we have trades
        if self.total_profit + self.total_loss > 0:
            self.success_rate = (float(self.total_profit) / (float(self.total_profit) + float(self.total_loss))) * 100
        
        super().save(*args, **kwargs)
    
    def generate_soldier_id(self):
        """Generate unique soldier ID in format: MBC-YYYY-XXXXX"""
        year = timezone.now().strftime('%Y')
        unique_num = str(uuid.uuid4().int)[:8]
        return f"MBC-{year}-{unique_num}"
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        return f"MBC{self.username.upper()[:4]}{random.randint(1000, 9999)}"
    
    def get_full_name(self):
        """Return the full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """Return the short name for the user"""
        return self.username

# ==================== VERIFICATION CODE MODEL ====================

class VerificationCode(models.Model):
    """Enhanced verification code model"""
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    code_type = models.CharField(max_length=20, default='email_verification', choices=[
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
        ('two_factor', 'Two-Factor Authentication'),
        ('transaction', 'Transaction Verification'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Security tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # For transaction verification
    transaction_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Code'
        verbose_name_plural = 'Verification Codes'
        indexes = [
            models.Index(fields=['user', 'is_used', 'expires_at']),
            models.Index(fields=['code', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.soldier_id} - {self.code_type} - {self.code}'
    
    def save(self, *args, **kwargs):
        # Auto-set expiry (30 minutes from creation)
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the code has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if code is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    @property
    def time_remaining(self):
        """Get time remaining in minutes"""
        if self.is_expired():
            return 0
        remaining = self.expires_at - timezone.now()
        return int(remaining.total_seconds() / 60)

# ==================== PAYMENT MODELS ====================

class PaymentTransaction(models.Model):
    """Track all payment transactions with Paystack integration"""
    
    TRANSACTION_STATUS = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    ]
    
    PAYMENT_TYPES = [
        ('market_consultation', 'Market Consultation'),
        ('lifetime_mentorship', 'Lifetime Mentorship'),
        ('leveraging_package', 'Leveraging Package'),
        ('education_program', 'Education Program'),
        ('partnership', 'Partnership Program'),
        ('subscription', 'Subscription'),
        ('deposit', 'Account Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('other', 'Other'),
    ]
    
    PAYMENT_METHODS = [
        ('paystack', 'Paystack'),
        ('mpesa', 'M-Pesa'),
        ('bitcoin', 'Bitcoin'),
        ('usdt', 'USDT'),
        ('bank_transfer', 'Bank Transfer'),
        ('equity_bank', 'Equity Bank'),
        ('manual', 'Manual Payment'),
    ]
    
    CURRENCIES = [
        ('USD', 'US Dollar'),
        ('KES', 'Kenyan Shilling'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    # User and basic info
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='payment_transactions')
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paystack')
    
    # Package/Service specific
    package_type = models.CharField(max_length=50, blank=True, null=True)
    package_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Education specific
    program_type = models.CharField(max_length=50, blank=True, null=True)
    program_name = models.CharField(max_length=200, blank=True, null=True)
    duration = models.CharField(max_length=20, blank=True, null=True)
    
    # Partnership specific
    partnership_tier = models.CharField(max_length=50, blank=True, null=True)
    partnership_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Payment details
    description = models.TextField(blank=True, null=True)
    service_details = models.JSONField(default=dict, blank=True)
    
    # Paystack integration
    paystack_data = models.JSONField(default=dict, blank=True)
    paystack_status = models.CharField(max_length=50, blank=True, null=True)
    paystack_message = models.TextField(blank=True, null=True)
    authorization_url = models.URLField(max_length=500, blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)
    
    # Customer info
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Fee and net amount
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    initiated_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Audit trail
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'created_at']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.user.username} - ${self.amount} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Generate reference if not exists
        if not self.reference:
            self.reference = f"TXN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        
        # Set customer info from user if not provided
        if not self.customer_email and self.user:
            self.customer_email = self.user.email
        if not self.customer_phone and self.user:
            self.customer_phone = self.user.phone
        if not self.customer_name and self.user:
            self.customer_name = self.user.get_full_name()
        
        # Calculate net amount
        self.net_amount = self.amount - self.transaction_fee
        
        # Set timestamps based on status
        if self.status == 'initiated' and not self.initiated_at:
            self.initiated_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status == 'failed' and not self.failed_at:
            self.failed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'completed'
    
    def get_payment_details(self):
        """Get human-readable payment details"""
        details = {
            'reference': self.reference,
            'amount': f"{self.currency} {self.amount:,.2f}",
            'net_amount': f"{self.currency} {self.net_amount:,.2f}",
            'status': self.get_status_display(),
            'payment_method': self.get_payment_method_display(),
            'date': self.created_at.strftime('%B %d, %Y %H:%M'),
            'type': self.get_payment_type_display(),
        }
        
        # Add specific details
        if self.package_name:
            details['service'] = f"Package: {self.package_name}"
        elif self.program_name:
            details['service'] = f"Education: {self.program_name}"
        elif self.partnership_name:
            details['service'] = f"Partnership: {self.partnership_name}"
        elif self.description:
            details['service'] = self.description[:100]
        
        return details
    
    def verify_payment(self, verified_by=None):
        """Verify a manual payment"""
        self.is_verified = True
        self.verified_by = verified_by
        self.verified_at = timezone.now()
        self.status = 'completed'
        self.save()
        
        # Trigger payment completion actions
        self._on_payment_completed()
    
    def _on_payment_completed(self):
        """Actions to perform when payment is completed"""
        # Update user account balance
        if self.payment_type in ['deposit', 'market_consultation', 'lifetime_mentorship', 
                                'leveraging_package', 'education_program', 'partnership']:
            self.user.account_balance += self.amount
            self.user.total_deposits += self.amount
            self.user.save()
    
    def refund(self, refund_amount=None, refund_reason=""):
        """Process refund for this transaction"""
        if self.status != 'completed':
            raise ValueError("Only completed transactions can be refunded")
        
        if not refund_amount:
            refund_amount = self.amount
        
        # Create refund transaction
        refund_txn = PaymentTransaction.objects.create(
            user=self.user,
            amount=refund_amount,
            currency=self.currency,
            status='completed',
            payment_type='refund',
            description=f"Refund for {self.reference}: {refund_reason}",
            metadata={'original_transaction': self.reference, 'refund_reason': refund_reason}
        )
        
        # Update original transaction
        self.status = 'refunded'
        self.save()
        
        return refund_txn

# ==================== SUBSCRIPTION MODEL ====================

class Subscription(models.Model):
    """For recurring payments/subscriptions"""
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    
    SUBSCRIPTION_PLANS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('lifetime', 'Lifetime'),
    ]
    
    # User and plan info
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    
    # Service details
    service_type = models.CharField(max_length=50, choices=[
        ('education', 'Education Program'),
        ('signals', 'Trading Signals'),
        ('mentorship', 'Mentorship'),
        ('community', 'Community Access'),
        ('tools', 'Trading Tools'),
    ])
    service_details = models.JSONField(default=dict, blank=True)
    
    # Paystack subscription
    paystack_subscription_code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    paystack_customer_code = models.CharField(max_length=100, blank=True, null=True)
    
    # Dates
    start_date = models.DateTimeField()
    next_payment_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment tracking
    last_payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscription_payments')
    total_payments = models.IntegerField(default=0)
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'next_payment_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan_name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Set start date if not provided
        if not self.start_date:
            self.start_date = timezone.now()
        
        # Set next payment date based on plan type
        if not self.next_payment_date:
            if self.plan_type == 'monthly':
                self.next_payment_date = self.start_date + timedelta(days=30)
            elif self.plan_type == 'quarterly':
                self.next_payment_date = self.start_date + timedelta(days=90)
            elif self.plan_type == 'semi_annual':
                self.next_payment_date = self.start_date + timedelta(days=180)
            elif self.plan_type == 'annual':
                self.next_payment_date = self.start_date + timedelta(days=365)
            elif self.plan_type == 'lifetime':
                self.next_payment_date = None
        
        super().save(*args, **kwargs)
    
    def is_active(self):
        """Check if subscription is active"""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        if self.next_payment_date and timezone.now() > self.next_payment_date:
            # Check if it's grace period (7 days)
            if timezone.now() > self.next_payment_date + timedelta(days=7):
                return False
        return True
    
    def cancel(self, cancellation_reason=""):
        """Cancel the subscription"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.metadata['cancellation_reason'] = cancellation_reason
        self.save()
    
    def renew(self, payment_transaction=None):
        """Renew the subscription"""
        if payment_transaction:
            self.last_payment = payment_transaction
            self.total_payments += 1
            self.total_amount_paid += payment_transaction.amount
        
        # Update next payment date
        if self.plan_type == 'monthly':
            self.next_payment_date = self.next_payment_date + timedelta(days=30)
        elif self.plan_type == 'quarterly':
            self.next_payment_date = self.next_payment_date + timedelta(days=90)
        elif self.plan_type == 'semi_annual':
            self.next_payment_date = self.next_payment_date + timedelta(days=180)
        elif self.plan_type == 'annual':
            self.next_payment_date = self.next_payment_date + timedelta(days=365)
        
        self.status = 'active'
        self.save()

# ==================== TRADING PACKAGES ====================

class Package(models.Model):
    """Trading packages"""
    
    PACKAGE_TYPES = [
        ('market_consultation', 'Market Consultation'),
        ('lifetime_mentorship', 'Lifetime Mentorship'),
        ('leveraging_package', 'Leveraging Package'),
        ('education_bundle', 'Education Bundle'),
        ('premium_signals', 'Premium Signals'),
    ]
    
    name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPES)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=200)
    full_description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Pricing options
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Images
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='packages/thumbnails/', blank=True, null=True)
    
    # Features
    features = models.JSONField(default=list, help_text="List of features in JSON format")
    benefits = models.JSONField(default=list, help_text="List of benefits in JSON format")
    
    # Duration
    duration_days = models.IntegerField(default=30, help_text="Package duration in days")
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.CharField(max_length=20, blank=True, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ])
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Payment
    payment_url = models.CharField(max_length=200, blank=True)
    payment_options = models.JSONField(default=list, help_text="Available payment options")
    
    # Access requirements
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    required_experience = models.CharField(max_length=50, blank=True, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('any', 'Any Level'),
    ])
    
    # Statistics
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Trading Package'
        verbose_name_plural = 'Trading Packages'
        indexes = [
            models.Index(fields=['package_type', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Generate payment URL if not provided
        if not self.payment_url:
            self.payment_url = f"/payment/package/{self.slug}/"
        
        # Calculate discounted price
        if self.original_price and self.discount_percentage > 0:
            discount_amount = (self.original_price * Decimal(self.discount_percentage / 100))
            self.price = self.original_price - discount_amount
        
        super().save(*args, **kwargs)
    
    @property
    def discounted_price(self):
        """Get the discounted price"""
        if self.original_price and self.discount_percentage > 0:
            discount_amount = (self.original_price * Decimal(self.discount_percentage / 100))
            return self.original_price - discount_amount
        return self.price
    
    def get_features_list(self):
        """Get features as list"""
        if isinstance(self.features, list):
            return self.features
        return []
    
    def increment_sales(self, amount):
        """Increment sales counter"""
        self.total_sales += 1
        self.total_revenue += amount
        self.save()

# ==================== EDUCATION PROGRAMS ====================

class EducationProgram(models.Model):
    """Education programs"""
    
    PROGRAM_TYPES = [
        ('IPLT', 'IPLT - Introduction to Professional Level Trading'),
        ('PTM', 'PTM - Professional Trading Masterclass'),
        ('POTM', 'POTM 2.0 - Professional Options Trading Masterclass'),
        ('PFTM', 'PFTM - Professional FOREX Trading Masterclass'),
        ('CUSTOM', 'Custom Program'),
    ]
    
    name = models.CharField(max_length=100)
    program_type = models.CharField(max_length=10, choices=PROGRAM_TYPES, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=200)
    full_description = models.TextField()
    
    # Curriculum
    curriculum = models.JSONField(default=list, help_text="List of modules/topics in JSON format")
    features = models.JSONField(default=list, help_text="List of features in JSON format")
    requirements = models.JSONField(default=list, help_text="List of requirements in JSON format")
    
    # Pricing
    price_1_month = models.DecimalField(max_digits=10, decimal_places=2)
    price_12_months = models.DecimalField(max_digits=10, decimal_places=2)
    original_price_1_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price_12_months = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Duration and stats
    total_hours = models.IntegerField(default=40, help_text="Total program hours")
    total_lessons = models.IntegerField(default=20, help_text="Total number of lessons")
    total_modules = models.IntegerField(default=5, help_text="Total number of modules")
    
    # Status
    is_popular = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Icons and badges
    icon_class = models.CharField(max_length=100, default="fas fa-play-circle")
    badge_text = models.CharField(max_length=50, blank=True)
    badge_color = models.CharField(max_length=50, default="primary", choices=[
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
    
    # Media
    thumbnail = models.ImageField(upload_to='education/thumbnails/', blank=True, null=True)
    promo_video = models.URLField(blank=True, null=True, help_text="YouTube/Vimeo URL")
    
    # Enrollment
    enrolled_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    launch_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Education Program'
        verbose_name_plural = 'Education Programs'
        indexes = [
            models.Index(fields=['program_type', 'is_active']),
            models.Index(fields=['is_popular', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.program_type} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.program_type}-{self.name}")
        
        # Set launch date if new and not set
        if self.is_new and not self.launch_date:
            self.launch_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_price(self, duration='1_month'):
        """Get price based on duration"""
        if duration == '12_months':
            return self.price_12_months
        return self.price_1_month
    
    def get_discount_percentage(self, duration='1_month'):
        """Get discount percentage"""
        if duration == '1_month' and self.original_price_1_month:
            discount = ((self.original_price_1_month - self.price_1_month) / self.original_price_1_month) * 100
            return round(discount, 1)
        elif duration == '12_months' and self.original_price_12_months:
            discount = ((self.original_price_12_months - self.price_12_months) / self.original_price_12_months) * 100
            return round(discount, 1)
        return 0

# ==================== USER EDUCATION ENROLLMENT ====================

class UserEducationEnrollment(models.Model):
    """Track user enrollment in education programs"""
    
    ENROLLMENT_TYPES = [
        ('1_month', '1 Month Access'),
        ('12_months', '12 Months Access'),
        ('lifetime', 'Lifetime Access'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='education_enrollments')
    program = models.ForeignKey(EducationProgram, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment details
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Access period
    enrolled_at = models.DateTimeField(auto_now_add=True)
    access_starts = models.DateTimeField(default=timezone.now)
    access_expires = models.DateTimeField()
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_modules = models.JSONField(default=list, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Certificates
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-enrolled_at']
        verbose_name = 'Education Enrollment'
        verbose_name_plural = 'Education Enrollments'
        unique_together = ['user', 'program']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['program', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.program.program_type} ({self.get_enrollment_type_display()})"
    
    def save(self, *args, **kwargs):
        # Check if access has expired
        if self.access_expires and timezone.now() > self.access_expires and self.status == 'active':
            self.status = 'expired'
            self.is_active = False
        
        # Check if completed
        if self.progress_percentage >= 100 and not self.completed_at:
            self.completed_at = timezone.now()
            self.status = 'completed'
        
        super().save(*args, **kwargs)
    
    def update_progress(self, module_name):
        """Update progress when a module is completed"""
        if module_name not in self.completed_modules:
            self.completed_modules.append(module_name)
            self.progress_percentage = (len(self.completed_modules) / len(self.program.curriculum)) * 100
            self.last_accessed = timezone.now()
            self.save()
    
    @property
    def days_remaining(self):
        """Get days remaining for access"""
        if not self.access_expires:
            return None
        remaining = self.access_expires - timezone.now()
        return max(0, remaining.days)
    
    @property
    def is_expired(self):
        """Check if enrollment has expired"""
        return self.status == 'expired' or (self.access_expires and timezone.now() > self.access_expires)
    
    def issue_certificate(self):
        """Issue completion certificate"""
        if self.progress_percentage >= 100 and not self.certificate_issued:
            self.certificate_issued = True
            self.certificate_issued_at = timezone.now()
            self.certificate_number = f"CERT-{self.program.program_type}-{uuid.uuid4().hex[:8].upper()}"
            self.save()
            return True
        return False

# ==================== PARTNERSHIP PROGRAMS ====================

class PartnershipProgram(models.Model):
    """Partnership programs"""
    
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('premium', 'Portfolio Management'),
    ]
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=50, choices=TIER_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    short_description = models.CharField(max_length=200)
    
    # Details
    features = models.JSONField(default=list, help_text="List of features in JSON format")
    benefits = models.JSONField(default=list, help_text="List of benefits in JSON format")
    requirements = models.JSONField(default=list, help_text="List of requirements in JSON format")
    
    # Styling
    icon_class = models.CharField(max_length=100, default="fas fa-medal")
    color_class = models.CharField(max_length=50, default="bronze", choices=[
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('premium', 'Premium'),
    ])
    
    # Investment details
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2)
    expected_returns = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=50, default='Medium', choices=[
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk'),
        ('Very High', 'Very High Risk'),
    ])
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Statistics
    total_partners = models.IntegerField(default=0)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Partnership Program'
        verbose_name_plural = 'Partnership Programs'
        indexes = [
            models.Index(fields=['tier', 'is_active']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.get_tier_display()} - {self.name}"
    
    def get_investment_range(self):
        """Get investment range based on tier"""
        ranges = {
            'bronze': '$250K',
            'silver': '$500K',
            'gold': '$1M',
            'platinum': '$5M',
            'premium': '$10M+',
        }
        return ranges.get(self.tier, f"${self.minimum_investment:,.0f}K")

# ==================== USER PARTNERSHIP ====================

class UserPartnership(models.Model):
    """Track user partnership enrollments"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='partnerships')
    program = models.ForeignKey(PartnershipProgram, on_delete=models.CASCADE, related_name='partners')
    
    # Investment details
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_months = models.IntegerField(default=12, help_text="Partnership duration in months")
    
    # Returns
    expected_returns = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_share_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    # Payment
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Management
    assigned_manager = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_partnerships')
    manager_notes = models.TextField(blank=True)
    
    # Contract
    contract_number = models.CharField(max_length=50, unique=True, blank=True)
    contract_signed = models.BooleanField(default=False)
    contract_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Partnership'
        verbose_name_plural = 'User Partnerships'
        unique_together = ['user', 'program']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['program', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.program.get_tier_display()} Partnership"
    
    def save(self, *args, **kwargs):
        # Generate contract number
        if not self.contract_number:
            self.contract_number = f"CONTRACT-{self.program.tier.upper()}-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate end date if not set
        if not self.end_date and self.start_date:
            self.end_date = self.start_date + timedelta(days=self.duration_months * 30)
        
        # Calculate expected returns
        if not self.expected_returns and self.program.expected_returns:
            # Simple calculation - you can implement more complex logic
            self.expected_returns = self.investment_amount * Decimal('1.2')  # 20% returns
        
        super().save(*args, **kwargs)
    
    def calculate_profit_share(self, total_profit):
        """Calculate profit share for user"""
        user_share = total_profit * Decimal(self.profit_share_percentage / 100)
        self.actual_returns += user_share
        self.save()
        return user_share
    
    @property
    def months_remaining(self):
        """Get months remaining in partnership"""
        if not self.end_date:
            return self.duration_months
        remaining = self.end_date - timezone.now()
        return max(0, remaining.days // 30)
    
    def terminate(self, termination_reason=""):
        """Terminate partnership"""
        self.status = 'terminated'
        self.is_active = False
        self.end_date = timezone.now()
        self.manager_notes += f"\nTerminated on {timezone.now().strftime('%Y-%m-%d')}: {termination_reason}"
        self.save()

# ==================== TESTIMONIAL MODEL ====================

class Testimonial(models.Model):
    """Customer testimonials"""
    
    PROGRAM_CHOICES = [
        ('PTM', 'PTM Series'),
        ('PFTM', 'PFTM Series'),
        ('POTM', 'POTM Series'),
        ('IPLT', 'IPLT Series'),
        ('mentoring', 'Mentoring'),
        ('signals', 'Trading Signals'),
        ('partnership', 'Partnership'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Media
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    # Rating
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    
    # Program association
    program = models.CharField(max_length=50, blank=True, choices=PROGRAM_CHOICES)
    program_name = models.CharField(max_length=200, blank=True)
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Verification
    verified_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-is_featured', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        indexes = [
            models.Index(fields=['program', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return f"Testimonial by {self.name}"
    
    def verify(self, verified_by):
        """Verify testimonial"""
        self.is_verified = True
        self.verified_by = verified_by
        self.verified_at = timezone.now()
        self.save()

# ==================== FAQ MODEL ====================

class FAQ(models.Model):
    """Frequently Asked Questions"""
    
    CATEGORY_CHOICES = [
        ('webinars', 'Webinars & Seminars'),
        ('education', 'Education & Programs'),
        ('accounts', 'Accounts & Community'),
        ('payments', 'Payments & Pricing'),
        ('packages', 'Trading Packages'),
        ('partnership', 'Partnership Programs'),
        ('technical', 'Technical Support'),
        ('general', 'General'),
    ]
    
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Statistics
    views_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'category']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return self.question
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def mark_helpful(self, helpful=True):
        """Mark FAQ as helpful or not helpful"""
        if helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
        self.save()

# ==================== COMMUNITY TIER MODEL ====================

class CommunityTier(models.Model):
    """Community tiers"""
    
    TIER_CHOICES = [
        ('citizens', 'Citizens@MBC'),
        ('studyhall', 'StudyHall@MBC'),
        ('society', 'Society@MBC'),
    ]
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=50, choices=TIER_CHOICES, unique=True)
    description = models.TextField()
    
    # Features and benefits
    features = models.JSONField(default=list, help_text="List of features in JSON format")
    benefits = models.JSONField(default=list, help_text="List of benefits in JSON format")
    access_level = models.CharField(max_length=50, default='Public', choices=[
        ('Public', 'Public Access'),
        ('Alumni', 'Alumni Only'),
        ('Premium', 'Premium Members'),
        ('Exclusive', 'Exclusive Members'),
    ])
    
    # Styling
    icon_class = models.CharField(max_length=100, default="fas fa-users")
    badge_text = models.CharField(max_length=100, default="Public Discord Server")
    color_scheme = models.CharField(max_length=50, default='blue', choices=[
        ('blue', 'Blue'),
        ('purple', 'Purple'),
        ('gold', 'Gold'),
        ('green', 'Green'),
        ('red', 'Red'),
    ])
    
    # Access
    button_text = models.CharField(max_length=100, default="Join")
    button_url = models.CharField(max_length=200, blank=True)
    discord_invite = models.URLField(blank=True, null=True)
    telegram_link = models.URLField(blank=True, null=True)
    
    # Requirements
    requirements = models.JSONField(default=list, help_text="List of requirements in JSON format")
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Statistics
    member_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Community Tier'
        verbose_name_plural = 'Community Tiers'
    
    def __str__(self):
        return self.name
    
    def add_member(self):
        """Add member to community"""
        self.member_count += 1
        self.save()

# ==================== USER COMMUNITY MEMBERSHIP ====================

class UserCommunityMembership(models.Model):
    """Track user membership in community tiers"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='community_memberships')
    community = models.ForeignKey(CommunityTier, on_delete=models.CASCADE, related_name='members')
    
    # Membership details
    joined_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Access info
    discord_username = models.CharField(max_length=100, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    access_granted = models.BooleanField(default=False)
    access_granted_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Notes
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-joined_at']
        verbose_name = 'Community Membership'
        verbose_name_plural = 'Community Memberships'
        unique_together = ['user', 'community']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['community', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.community.name}"
    
    @property
    def days_remaining(self):
        """Get days remaining in membership"""
        if not self.expires_at:
            return None
        remaining = self.expires_at - timezone.now()
        return max(0, remaining.days)
    
    def grant_access(self):
        """Grant access to community"""
        self.access_granted = True
        self.access_granted_at = timezone.now()
        self.save()

# ==================== BROKERAGE MODEL ====================

class Brokerage(models.Model):
    """Brokerage companies"""
    
    REGION_CHOICES = [
        ('uk_europe_canada', 'UK, Europe & Canada'),
        ('usa_canada', 'USA and Canada'),
        ('singapore_hongkong', 'Singapore & Hong Kong'),
        ('australia_world', 'Australia, New Zealand & Rest of World'),
        ('africa', 'Africa'),
    ]
    
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    website = models.URLField(blank=True, null=True)
    
    # Media
    logo = models.ImageField(upload_to='brokerages/')
    featured_image = models.ImageField(upload_to='brokerages/featured/', blank=True, null=True)
    
    # Details
    description = models.TextField(blank=True)
    features = models.JSONField(default=list, help_text="List of features in JSON format")
    supported_markets = models.JSONField(default=list, help_text="List of supported markets")
    account_types = models.JSONField(default=list, help_text="List of account types")
    
    # Ratings
    trust_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    regulation_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    platform_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Status
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Statistics
    referral_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['region', 'order']
        verbose_name = 'Brokerage'
        verbose_name_plural = 'Brokerages'
        indexes = [
            models.Index(fields=['region', 'is_active']),
            models.Index(fields=['is_recommended', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_region_display()}"
    
    @property
    def overall_score(self):
        """Calculate overall score"""
        return round((self.trust_score + self.regulation_score + self.platform_score) / 3, 1)

# ==================== CONTACT SUBMISSION ====================

class ContactSubmission(models.Model):
    """Contact form submissions"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
        ('spam', 'Spam'),
    ]
    
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    # Inquiry details
    package = models.CharField(max_length=100, blank=True)
    program = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, default='normal', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ])
    
    # Technical info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Follow-up
    assigned_to = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    replied_at = models.DateTimeField(null=True, blank=True)
    reply_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.package} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def mark_as_read(self, read_by=None):
        """Mark submission as read"""
        self.status = 'read'
        if read_by:
            self.assigned_to = read_by
        self.save()
    
    def reply(self, reply_notes, replied_by):
        """Add reply to submission"""
        self.status = 'replied'
        self.replied_at = timezone.now()
        self.reply_notes = reply_notes
        self.assigned_to = replied_by
        self.save()

# ==================== SITE CONTENT ====================

class SiteContent(models.Model):
    """Dynamic content sections"""
    
    SECTION_CHOICES = [
        ('about', 'About Section'),
        ('hero', 'Hero Section'),
        ('packages_intro', 'Packages Introduction'),
        ('payment_intro', 'Payment Introduction'),
        ('partnership_intro', 'Partnership Introduction'),
        ('seminars_intro', 'Seminars Introduction'),
        ('education_intro', 'Education Introduction'),
        ('mentoring_intro', 'Mentoring Introduction'),
        ('accounts_intro', 'Accounts Introduction'),
        ('community_intro', 'Community Introduction'),
        ('testimonials_intro', 'Testimonials Introduction'),
        ('contact_intro', 'Contact Introduction'),
        ('footer', 'Footer Content'),
        ('terms', 'Terms & Conditions'),
        ('privacy', 'Privacy Policy'),
        ('disclaimer', 'Disclaimer'),
    ]
    
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    
    # Media
    image = models.ImageField(upload_to='site_content/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    
    # Versioning
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_content')
    updated_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_content')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['section']
        verbose_name = 'Site Content'
        verbose_name_plural = 'Site Contents'
        indexes = [
            models.Index(fields=['section', 'is_active']),
        ]
    
    def __str__(self):
        return self.get_section_display()
    
    def create_version(self, user):
        """Create new version of content"""
        SiteContentVersion.objects.create(
            content=self,
            title=self.title,
            subtitle=self.subtitle,
            content_text=self.content,
            updated_by=user,
            version=self.version
        )
        self.version += 1
        self.save()

# ==================== SITE CONTENT VERSION ====================

class SiteContentVersion(models.Model):
    """Version history for site content"""
    
    content = models.ForeignKey(SiteContent, on_delete=models.CASCADE, related_name='versions')
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    content_text = models.TextField()
    
    version = models.IntegerField()
    updated_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Content Version'
        verbose_name_plural = 'Content Versions'
        unique_together = ['content', 'version']
    
    def __str__(self):
        return f"{self.content.section} - v{self.version}"

# ==================== STATISTIC MODEL ====================

class Statistic(models.Model):
    """Statistics for homepage"""
    
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    suffix = models.CharField(max_length=20, blank=True, help_text="e.g., +, %, years")
    description = models.CharField(max_length=200, blank=True)
    
    # Styling
    icon_class = models.CharField(max_length=100, default="fas fa-chart-line")
    color = models.CharField(max_length=50, default='primary', choices=[
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('gold', 'Gold'),
    ])
    
    # Animation
    animation_delay = models.IntegerField(default=0, help_text="Animation delay in milliseconds")
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Statistic'
        verbose_name_plural = 'Statistics'
    
    def __str__(self):
        return f"{self.title}: {self.value}{self.suffix}"

# ==================== NOTIFICATION MODEL ====================

class Notification(models.Model):
    """System notifications"""
    
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
        ('PAYMENT', 'Payment'),
        ('COURSE', 'Course'),
        ('MENTORING', 'Mentoring'),
        ('COMMUNITY', 'Community'),
        ('SYSTEM', 'System'),
        ('SECURITY', 'Security'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    
    # Actions
    action_text = models.CharField(max_length=100, blank=True)
    action_url = models.URLField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    @classmethod
    def send_notification(cls, user, title, message, notification_type='INFO', **kwargs):
        """Create and send notification"""
        notification = cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            **kwargs
        )
        return notification

# ==================== ACTIVITY LOG ====================

class ActivityLog(models.Model):
    """System activity logging"""
    
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('REGISTER', 'User Registration'),
        ('PROFILE_UPDATE', 'Profile Updated'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('EMAIL_VERIFICATION', 'Email Verified'),
        ('PAYMENT_INITIATED', 'Payment Initiated'),
        ('PAYMENT_COMPLETED', 'Payment Completed'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('COURSE_ENROLLED', 'Course Enrolled'),
        ('COURSE_COMPLETED', 'Course Completed'),
        ('MENTORING_BOOKED', 'Mentoring Booked'),
        ('COMMUNITY_JOINED', 'Community Joined'),
        ('SUPPORT_TICKET_CREATED', 'Support Ticket Created'),
        ('SUPPORT_TICKET_UPDATED', 'Support Ticket Updated'),
        ('SETTINGS_UPDATE', 'Settings Updated'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('SECURITY_EVENT', 'Security Event'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Technical info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_info = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Related objects
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, default='info', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"
    
    @classmethod
    def log_activity(cls, user, action, description, **kwargs):
        """Create activity log entry"""
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            **kwargs
        )

# ==================== SYSTEM SETTINGS ====================

class SystemSettings(models.Model):
    """System-wide settings"""
    
    SETTING_CATEGORIES = [
        ('general', 'General Settings'),
        ('payment', 'Payment Settings'),
        ('email', 'Email Settings'),
        ('security', 'Security Settings'),
        ('notifications', 'Notification Settings'),
        ('maintenance', 'Maintenance Settings'),
        ('seo', 'SEO Settings'),
        ('social', 'Social Media Settings'),
        ('trading', 'Trading Settings'),
        ('api', 'API Settings'),
    ]
    
    SETTING_TYPES = [
        ('string', 'String'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('array', 'Array'),
        ('object', 'Object'),
        ('text', 'Text'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    category = models.CharField(max_length=50, choices=SETTING_CATEGORIES, default='general')
    
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False, help_text="Can be accessed via API")
    is_editable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Versioning
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_settings')
    updated_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'key']
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return self.key
    
    def get_value(self):
        """Get typed value based on setting type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'number':
            try:
                return float(self.value) if '.' in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.setting_type in ('json', 'array', 'object'):
            try:
                import json
                return json.loads(self.value)
            except:
                return {}
        else:
            return self.value
    
    def set_value(self, value):
        """Set typed value"""
        import json
        if self.setting_type == 'boolean':
            self.value = 'true' if value else 'false'
        elif self.setting_type == 'number':
            self.value = str(value)
        elif self.setting_type in ('json', 'array', 'object'):
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value by key"""
        try:
            setting = cls.objects.get(key=key, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, setting_type='string', category='general', **kwargs):
        """Set setting value"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': '',
                'setting_type': setting_type,
                'category': category,
                **kwargs
            }
        )
        setting.set_value(value)
        setting.save()
        return setting

# ==================== SUPPORT TICKET ====================

class SupportTicket(models.Model):
    """Customer support tickets"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_reply', 'Waiting for Reply'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing/Payment'),
        ('account', 'Account Issues'),
        ('education', 'Education Programs'),
        ('mentoring', 'Mentoring'),
        ('community', 'Community Access'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]
    
    # Basic info
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket details
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Assignment
    assigned_to = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    department = models.CharField(max_length=100, blank=True)
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Ratings
    satisfaction_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    rating_comment = models.TextField(blank=True)
    
    # Statistics
    reply_count = models.IntegerField(default=0)
    last_reply_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TICKET{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

# ==================== TICKET REPLY ====================

class TicketReply(models.Model):
    """Replies to support tickets"""
    
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='ticket_replies')
    
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal note (not visible to user)")
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment URLs")
    
    # Read receipts
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='read_replies')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Reply'
        verbose_name_plural = 'Ticket Replies'
    
    def __str__(self):
        return f"Reply to {self.ticket.ticket_number} by {self.user.username}"
    
    def mark_as_read(self, read_by):
        """Mark reply as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.read_by = read_by
        self.save()

# ==================== SESSION MANAGEMENT ====================

class UserSession(models.Model):
    """Track user sessions for security"""
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Device info
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ])
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device_name = models.CharField(max_length=200, blank=True)
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)
    
    # Security
    is_suspicious = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)
    
    # Timestamps
    login_at = models.DateTimeField(default=now)
    last_activity = models.DateTimeField(auto_now=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-login_at']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ip_address', 'login_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.login_at.strftime('%Y-%m-%d %H:%M')}"
    
    def terminate(self):
        """Terminate session"""
        self.is_active = False
        self.logout_at = timezone.now()
        self.save()
    
    @property
    def duration(self):
        """Get session duration"""
        end_time = self.logout_at or timezone.now()
        return end_time - self.login_at

# ==================== HERO SLIDER ====================

class HeroSlider(models.Model):
    """Homepage hero slider"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='hero_sliders/')
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

# ==================== ABOUT SECTION ====================

class AboutSection(models.Model):
    """About us section content"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='about/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

# ==================== PAYMENT METHOD ====================

class PaymentMethod(models.Model):
    """Available payment methods"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

# ==================== CONTACT INFO ====================

class ContactInfo(models.Model):
    """Contact information"""
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    hours = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return "Contact Information"

# ==================== LOGO ====================

class Logo(models.Model):
    """Site logos"""
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='logos/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

# ==================== TRAINING VIDEO ====================

class TrainingVideo(models.Model):
    """Training videos managed by admin"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(help_text="URL to video (Vimeo, YouTube, etc.)")
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    
    category = models.CharField(max_length=20, choices=[
        ('PTM', 'PTM Series'),
        ('POTM', 'POTM Series'),
        ('PFTM', 'PFTM Series'),
        ('Webinars', 'Webinars'),
    ], default='PTM')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    
    # Security settings
    allow_download = models.BooleanField(default=False)
    disable_screenshots = models.BooleanField(default=True)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Training Video'
        verbose_name_plural = 'Training Videos'
    
    def __str__(self):
        return self.title

# ==================== USER VIDEO ACCESS ====================

class UserVideoAccess(models.Model):
    """Track which videos users have unlocked"""
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    video = models.ForeignKey(TrainingVideo, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey('PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'video']
        verbose_name = 'User Video Access'
        verbose_name_plural = 'User Video Accesses'
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

# ==================== COURSE ====================

class Course(models.Model):
    """Courses managed by admin"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    materials = models.JSONField(default=list, help_text="List of materials/lessons")
    duration_weeks = models.IntegerField(default=4)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return self.title

# ==================== USER COURSE ====================

class UserCourse(models.Model):
    """Track user course enrollment and progress"""
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey('PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True)
    
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_lessons = models.JSONField(default=list, blank=True)
    
    class Meta:
        unique_together = ['user', 'course']
        verbose_name = 'User Course'
        verbose_name_plural = 'User Courses'
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

# ==================== MENTORSHIP PROGRAM ====================

class MentorshipProgram(models.Model):
    """Mentorship programs managed by admin"""
    title = models.CharField(max_length=200)
    mentor_name = models.CharField(max_length=100)
    mentor_role = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    sessions_per_week = models.IntegerField(default=1)
    duration_months = models.IntegerField(default=3)
    
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Mentorship Program'
        verbose_name_plural = 'Mentorship Programs'
    
    def __str__(self):
        return f"{self.mentor_name} - {self.title}"

# ==================== USER ACTIVITY ====================

class UserActivity(models.Model):
    """Log user activities"""
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('video_watch', 'Video Watched'),
        ('course_access', 'Course Accessed'),
        ('payment_made', 'Payment Made'),
        ('support_request', 'Support Request'),
        ('settings_update', 'Settings Updated'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    
    # Related objects
    video = models.ForeignKey(TrainingVideo, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey('PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.action}"