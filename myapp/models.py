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
from django.conf import settings
from datetime import datetime

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
    

# ==================== USER ACCESS METHODS ====================

def has_pdf_access(self, pdf_id):
    """Check if user has access to a PDF"""
    try:
        pdf = PDF.objects.get(id=pdf_id)
        
        # Free PDFs are accessible to everyone
        if pdf.is_free:
            return True
        
        # Check direct purchase
        if UserPDFAccess.objects.filter(user=self, pdf=pdf).exists():
            return True
        
        # Check course access if PDF belongs to a course
        if pdf.course:
            return UserCourse.objects.filter(
                user=self, 
                course=pdf.course,
                is_active=True,
                access_expires_at__gt=timezone.now()
            ).exists()
        
        return False
    except PDF.DoesNotExist:
        return False

def has_video_access(self, video_id):
    """Check if user has access to a video"""
    try:
        video = TrainingVideo.objects.get(id=video_id)
        
        # Free videos are accessible to everyone
        if video.price == 0:
            return True
        
        # Check direct purchase
        if UserVideoAccess.objects.filter(user=self, video=video).exists():
            return True
        
        # Check course access if video belongs to a course
        if video.course:
            return UserCourse.objects.filter(
                user=self, 
                course=video.course,
                is_active=True,
                access_expires_at__gt=timezone.now()
            ).exists()
        
        return False
    except TrainingVideo.DoesNotExist:
        return False    


# ==================== MAIN USER MODEL ====================

class MfalmeUsers(AbstractBaseUser, PermissionsMixin):
    """Enhanced custom user model"""
    
    # ===== BASIC INFO =====
    email = models.EmailField(unique=True, verbose_name='Email Address')
    username = models.CharField(max_length=100)
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
        
        # AUTO-FIX: Ensure username is unique if provided
        if self.username:
            original_username = self.username
            counter = 1
            
            # Check if username already exists (excluding current user)
            query = MfalmeUsers.objects.filter(username=self.username)
            if self.pk:
                query = query.exclude(pk=self.pk)
            
            while query.exists():
                self.username = f"{original_username}{counter}"
                counter += 1
                
                # Update query with new username
                query = MfalmeUsers.objects.filter(username=self.username)
                if self.pk:
                    query = query.exclude(pk=self.pk)
                
                # Safety limit to prevent infinite loop
                if counter > 100:
                    import uuid
                    self.username = f"{original_username}_{uuid.uuid4().hex[:8]}"
                    break
        
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
    
    @property
    def profile_image_url(self):
        """Get profile image URL"""
        if not self.profile_image or not self.profile_image.name:
            return None
        try:
            return self.profile_image.url
        except Exception as e:
            print(f"❌ Error getting profile image URL for user {self.id}: {e}")
            return None


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
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    transaction_ref = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used', 'expires_at']),
            models.Index(fields=['code', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.soldier_id} - {self.code_type} - {self.code}'
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


# ==================== PAYMENT MODELS ====================

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
        ('market_consultation', 'Market Consultation'),
        ('lifetime_mentorship', 'Lifetime Mentorship'),
        ('leveraging_package', 'Leveraging Package'),
        ('education_program', 'Education Program'),
        ('partnership', 'Partnership Program'),
        ('subscription', 'Subscription'),
        ('deposit', 'Account Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('course_purchase', 'Course Purchase'),
        ('ticket', 'Event Ticket'),
        ('merchandise', 'Merchandise'),
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
        ('sasapay', 'SasaPay'),
        ('pesapal', 'Pesapal'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card'),
    ]
    
    CURRENCIES = [
        ('USD', 'US Dollar'),
        ('KES', 'Kenyan Shilling'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='payment_transactions')
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='initiated')
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paystack')
    pesapal_tracking_id = models.CharField(max_length=100, blank=True, null=True)
    pesapal_payment_method = models.CharField(max_length=50, blank=True, null=True)
    pesapal_raw_response = models.JSONField(null=True, blank=True)
    # SasaPay specific fields
    sasapay_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    sasapay_checkout_id = models.CharField(max_length=100, blank=True, null=True)
    sasapay_payment_method = models.CharField(max_length=50, blank=True, null=True)
    sasapay_raw_response = models.JSONField(blank=True, null=True)
    sasapay_status = models.CharField(max_length=20, blank=True, null=True)
    
    # Course-specific fields
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    
    package_type = models.CharField(max_length=50, blank=True, null=True)
    package_name = models.CharField(max_length=200, blank=True, null=True)
    program_type = models.CharField(max_length=50, blank=True, null=True)
    program_name = models.CharField(max_length=200, blank=True, null=True)
    duration = models.CharField(max_length=20, blank=True, null=True)
    partnership_tier = models.CharField(max_length=50, blank=True, null=True)
    partnership_name = models.CharField(max_length=200, blank=True, null=True)
    
    description = models.TextField(blank=True, null=True)
    service_details = models.JSONField(default=dict, blank=True)
    paystack_data = models.JSONField(default=dict, blank=True)
    paystack_status = models.CharField(max_length=50, blank=True, null=True)
    paystack_message = models.TextField(blank=True, null=True)
    authorization_url = models.URLField(max_length=500, blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)
    
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    initiated_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'created_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.user.username if self.user else 'No User'} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TXN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


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
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    
    service_type = models.CharField(max_length=50, choices=[
        ('education', 'Education Program'),
        ('signals', 'Trading Signals'),
        ('mentorship', 'Mentorship'),
        ('community', 'Community Access'),
        ('tools', 'Trading Tools'),
    ])
    service_details = models.JSONField(default=dict, blank=True)
    
    paystack_subscription_code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    paystack_customer_code = models.CharField(max_length=100, blank=True, null=True)
    
    start_date = models.DateTimeField()
    next_payment_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    last_payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscription_payments')
    total_payments = models.IntegerField(default=0)
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'next_payment_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"
    
    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()
        super().save(*args, **kwargs)


# ==================== PACKAGE MODEL ====================

class Package(models.Model):
    """Trading packages"""
    PACKAGE_TYPES = [
        ('market_consultation', 'Market Consultation'),
        ('lifetime_mentorship', 'Lifetime Mentorship'),
        ('leveraging_package', 'Leveraging Package'),
        ('education_bundle', 'Education Bundle'),
        ('premium_signals', 'Premium Signals'),
        ('ticket', 'Event Ticket'),
        ('merchandise', 'Merchandise'),
    ]
    
    name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPES)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=200)
    full_description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='packages/thumbnails/', blank=True, null=True)
    
    features = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    
    duration_days = models.IntegerField(default=30)
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.CharField(max_length=20, blank=True, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ])
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    payment_url = models.CharField(max_length=200, blank=True)
    payment_options = models.JSONField(default=list)
    
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    required_experience = models.CharField(max_length=50, blank=True, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('any', 'Any Level'),
    ])
    
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['package_type', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def image_url(self):
        """Get package image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except Exception as e:
            print(f"❌ Error getting image URL for package {self.id}: {e}")
            return None


# ==================== EDUCATION PROGRAM MODEL ====================
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
    
    curriculum = models.JSONField(default=list)
    features = models.JSONField(default=list)
    requirements = models.JSONField(default=list)
    
    price_1_month = models.DecimalField(max_digits=10, decimal_places=2)
    price_12_months = models.DecimalField(max_digits=10, decimal_places=2)
    original_price_1_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price_12_months = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    total_hours = models.IntegerField(default=40)
    total_lessons = models.IntegerField(default=20)
    total_modules = models.IntegerField(default=5)
    
    is_popular = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    icon_class = models.CharField(max_length=100, default="fas fa-play-circle")
    badge_text = models.CharField(max_length=50, blank=True)
    badge_color = models.CharField(max_length=50, default="primary")
    
    thumbnail = models.ImageField(upload_to='education/thumbnails/', blank=True, null=True)
    promo_video = models.URLField(blank=True, null=True)
    
    enrolled_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    launch_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['program_type', 'is_active']),
            models.Index(fields=['is_popular', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.program_type} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.program_type}-{self.name}")
        super().save(*args, **kwargs)
    
    @property
    def thumbnail_url(self):
        """Get program thumbnail URL"""
        if not self.thumbnail or not self.thumbnail.name:
            return None
        try:
            return self.thumbnail.url
        except Exception as e:
            print(f"❌ Error getting thumbnail URL for education program {self.id}: {e}")
            return None


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
    
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    access_starts = models.DateTimeField(default=timezone.now)
    access_expires = models.DateTimeField()
    
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_modules = models.JSONField(default=list, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=50, blank=True, null=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-enrolled_at']
        unique_together = ['user', 'program']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['program', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.program.program_type}"


# ==================== PARTNERSHIP PROGRAM MODEL ====================

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
    
    features = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    requirements = models.JSONField(default=list)
    
    icon_class = models.CharField(max_length=100, default="fas fa-medal")
    color_class = models.CharField(max_length=50, default="bronze")
    
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2)
    expected_returns = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=50, default='Medium')
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    total_partners = models.IntegerField(default=0)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['tier', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_tier_display()} - {self.name}"
    
    @property
    def image_url(self):
        """Get program image URL (if any)"""
        return None


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
    
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_months = models.IntegerField(default=12)
    
    expected_returns = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_share_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    assigned_manager = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_partnerships')
    manager_notes = models.TextField(blank=True)
    
    contract_number = models.CharField(max_length=50, unique=True, blank=True)
    contract_signed = models.BooleanField(default=False)
    contract_signed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'program']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['program', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.program.get_tier_display()} Partnership"
    
    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = f"CONTRACT-{self.program.tier.upper()}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ==================== WATCHLIST MODEL ====================

class Watchlist(models.Model):
    """User's saved items for later purchase"""
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('course', 'Course'),
        ('package', 'Package'),
        ('merchandise', 'Merchandise'),
        ('event', 'Event'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='watchlist')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'content_type', 'content_id']
        indexes = [
            models.Index(fields=['user', 'content_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.content_type}:{self.content_id}"
    
    def get_content(self):
        """Get the actual content object"""
        if self.content_type == 'video':
            return TrainingVideo.objects.filter(id=self.content_id).first()
        elif self.content_type == 'pdf':
            return PDF.objects.filter(id=self.content_id).first()
        elif self.content_type == 'course':
            return Course.objects.filter(id=self.content_id).first()
        elif self.content_type == 'package':
            return Package.objects.filter(id=self.content_id).first()
        elif self.content_type == 'merchandise':
            return Merchandise.objects.filter(id=self.content_id).first()
        elif self.content_type == 'event':
            return Event.objects.filter(id=self.content_id).first()
        return None


# ==================== INSTITUTE APPLICATION MODEL ====================

class InstituteApplication(models.Model):
    """Applications for Institute account status"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('info_needed', 'More Info Needed'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('1-3', '1-3 years'),
        ('3-5', '3-5 years'),
        ('5-10', '5-10 years'),
        ('10+', '10+ years'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='institute_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Application details
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    trading_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES)
    
    # Documents
    proof_of_funds = models.FileField(upload_to='institute/proof_of_funds/')
    trading_history = models.FileField(upload_to='institute/trading_history/', blank=True, null=True)
    
    # Additional info
    notes = models.TextField(blank=True, help_text="Additional information from applicant")
    
    # Metadata
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        MfalmeUsers, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications'
    )
    admin_notes = models.TextField(blank=True, help_text="Admin notes about this application")
    
    # Communication
    notified = models.BooleanField(default=False, help_text="Has the user been notified of decision?")
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['status', 'applied_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Institute Application - {self.user.email} - {self.status}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def proof_url(self):
        """Get proof of funds file URL"""
        if not self.proof_of_funds or not self.proof_of_funds.name:
            return None
        try:
            return self.proof_of_funds.url
        except:
            return None
    
    @property
    def history_url(self):
        """Get trading history file URL"""
        if not self.trading_history or not self.trading_history.name:
            return None
        try:
            return self.trading_history.url
        except:
            return None


# ==================== COMMUNITY JOIN REQUEST MODEL ====================

class CommunityJoinRequest(models.Model):
    """Requests to join community tiers that require approval"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='community_requests')
    community = models.ForeignKey('CommunityTier', on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Check if user met requirements at time of request
    met_requirements = models.BooleanField(default=False)
    investment_at_request = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    courses_completed = models.JSONField(default=list, blank=True)
    
    # Admin actions
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        MfalmeUsers, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_community_requests'
    )
    admin_notes = models.TextField(blank=True)
    
    # Communication
    notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'community']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.community.name} - {self.status}"


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
    
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    
    program = models.CharField(max_length=50, blank=True, choices=PROGRAM_CHOICES)
    program_name = models.CharField(max_length=200, blank=True)
    
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    verified_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['program', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return f"Testimonial by {self.name}"
    
    @property
    def image_url(self):
        """Get testimonial image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except:
            return None


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
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    views_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'category']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return self.question


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
    
    features = models.JSONField(default=list)
    benefits = models.JSONField(default=list)
    access_level = models.CharField(max_length=50, default='Public')
    
    icon_class = models.CharField(max_length=100, default="fas fa-users")
    badge_text = models.CharField(max_length=100, default="Public Discord Server")
    color_scheme = models.CharField(max_length=50, default='blue')
    
    button_text = models.CharField(max_length=100, default="Join")
    button_url = models.CharField(max_length=200, blank=True)
    discord_invite = models.URLField(blank=True, null=True)
    telegram_link = models.URLField(blank=True, null=True)
    
    requirements = models.JSONField(default=list)
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    required_courses = models.JSONField(default=list, blank=True, help_text="List of course IDs required")
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    member_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name
    
    def check_user_eligibility(self, user):
        """Check if user meets requirements for this tier"""
        if self.tier == 'citizens':
            return True, []
        
        missing = []
        
        # Check investment
        if self.minimum_investment and user.total_deposits < self.minimum_investment:
            missing.append(f"Minimum investment of ${self.minimum_investment} required")
        
        # Check required courses
        if self.required_courses:
            completed_courses = UserCourse.objects.filter(
                user=user,
                course_id__in=self.required_courses
            ).count()
            if completed_courses < len(self.required_courses):
                missing.append("Complete required courses")
        
        return len(missing) == 0, missing


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
    
    joined_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    discord_username = models.CharField(max_length=100, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    access_granted = models.BooleanField(default=False)
    access_granted_at = models.DateTimeField(null=True, blank=True)
    
    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-joined_at']
        unique_together = ['user', 'community']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['community', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.community.name}"


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
    
    logo = models.ImageField(upload_to='brokerages/')
    featured_image = models.ImageField(upload_to='brokerages/featured/', blank=True, null=True)
    
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    supported_markets = models.JSONField(default=list)
    account_types = models.JSONField(default=list)
    
    trust_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    regulation_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    platform_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    is_recommended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    referral_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['region', 'order']
        indexes = [
            models.Index(fields=['region', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_region_display()}"
    
    @property
    def logo_url(self):
        """Get logo URL"""
        if not self.logo or not self.logo.name:
            return None
        try:
            return self.logo.url
        except:
            return None
    
    @property
    def featured_image_url(self):
        """Get featured image URL"""
        if not self.featured_image or not self.featured_image.name:
            return None
        try:
            return self.featured_image.url
        except:
            return None


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
    
    package = models.CharField(max_length=100, blank=True)
    program = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, default='normal')
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    assigned_to = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    replied_at = models.DateTimeField(null=True, blank=True)
    reply_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d')}"


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
    
    image = models.ImageField(upload_to='site_content/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_content')
    updated_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_content')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['section']
        indexes = [
            models.Index(fields=['section', 'is_active']),
        ]
    
    def __str__(self):
        return self.get_section_display()
    
    @property
    def image_url(self):
        """Get content image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except:
            return None


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
        unique_together = ['content', 'version']
    
    def __str__(self):
        return f"{self.content.section} - v{self.version}"


# ==================== STATISTIC MODEL ====================

class Statistic(models.Model):
    """Statistics for homepage"""
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    suffix = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=200, blank=True)
    
    icon_class = models.CharField(max_length=100, default="fas fa-chart-line")
    color = models.CharField(max_length=50, default='primary')
    
    animation_delay = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
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
    
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    
    action_text = models.CharField(max_length=100, blank=True)
    action_url = models.URLField(blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


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
        ('COMMUNITY_REQUEST', 'Community Request'),
        ('SUPPORT_TICKET_CREATED', 'Support Ticket Created'),
        ('SUPPORT_TICKET_UPDATED', 'Support Ticket Updated'),
        ('SETTINGS_UPDATE', 'Settings Updated'),
        ('WATCHLIST_ADD', 'Added to Watchlist'),
        ('WATCHLIST_REMOVE', 'Removed from Watchlist'),
        ('INSTITUTE_APPLY', 'Institute Application'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('SECURITY_EVENT', 'Security Event'),
        ('COURSE_ACCESS_EXPIRED', 'Course Access Expired'),
        ('PDF_VIEWED', 'PDF Viewed'),
        ('VIDEO_WATCHED', 'Video Watched'),
        ('TICKET_PURCHASED', 'Ticket Purchased'),
        ('MERCHANDISE_PURCHASED', 'Merchandise Purchased'),
    ]
    
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_info = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, default='info')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


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
    is_public = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_settings')
    updated_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return self.key


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
        ('packages', 'Packages'),
        ('community', 'Community Access'),
        ('partnership', 'Partnership'),
        ('institute', 'Institute'),
        ('tickets', 'Event Tickets'),
        ('merchandise', 'Merchandise'),
        ('other', 'Other'),
    ]
    
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='support_tickets')
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    assigned_to = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    department = models.CharField(max_length=100, blank=True)
    
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    satisfaction_rating = models.IntegerField(null=True, blank=True)
    rating_comment = models.TextField(blank=True)
    
    reply_count = models.IntegerField(default=0)
    last_reply_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
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
    is_internal = models.BooleanField(default=False)
    
    attachments = models.JSONField(default=list, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True, related_name='read_replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply to {self.ticket.ticket_number} by {self.user.username}"


# ==================== SESSION MANAGEMENT ====================

class UserSession(models.Model):
    """Track user sessions for security"""
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True, db_index=True)
    
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
    
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)
    
    is_suspicious = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)
    
    login_at = models.DateTimeField(default=now)
    last_activity = models.DateTimeField(auto_now=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-login_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ip_address', 'login_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.login_at}"


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
    
    @property
    def image_url(self):
        """Get slider image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except:
            return None


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
    
    @property
    def image_url(self):
        """Get about section image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except:
            return None


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
    
    @property
    def image_url(self):
        """Get logo image URL"""
        if not self.image or not self.image.name:
            return None
        try:
            return self.image.url
        except:
            return None


# ==================== TRAINING VIDEO ====================
class TrainingVideo(models.Model):
    title = models.TextField()
    description = models.TextField(blank=True)
    s3_key = models.CharField(max_length=500, blank=True, null=True)
    external_url = models.URLField(max_length=1000, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail_s3_key = models.CharField(max_length=500, blank=True, null=True)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    module = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=20, default='PTM')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    duration = models.IntegerField(default=30)
    order = models.IntegerField(default=0)
    allow_download = models.BooleanField(default=False)
    disable_screenshots = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['course', 'order']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['s3_key']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.price == 0:
            self.is_free = True
        bypass_validation = kwargs.pop('bypass_validation', False)
        if bypass_validation:
            self._state.adding = not self.pk
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    @property
    def video_url(self):
        from django.conf import settings
        if self.s3_key:
            try:
                if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
                    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.s3_key}"
                else:
                    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.s3_key}"
            except:
                pass
        if self.external_url:
            return self.external_url
        if self.video_file and hasattr(self.video_file, 'url'):
            try:
                return self.video_file.url
            except:
                pass
        return None
    
    @property
    def thumbnail_url(self):
        from django.conf import settings
        if self.thumbnail_s3_key:
            try:
                if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
                    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.thumbnail_s3_key}"
                else:
                    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.thumbnail_s3_key}"
            except:
                pass
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            try:
                return self.thumbnail.url
            except:
                pass
        return None
    
    @property
    def is_s3_video(self):
        return bool(self.s3_key)
    
    @property
    def is_external_video(self):
        return bool(self.external_url)
    
    @property
    def video_type(self):
        if self.s3_key:
            return "S3"
        elif self.external_url:
            return "External"
        elif self.video_file:
            return "Uploaded"
        return "None"


# ==================== USER VIDEO ACCESS ====================

class UserVideoAccess(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    video = models.ForeignKey(TrainingVideo, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'video']
    
    def __str__(self):
        return f"{self.user.username} - {self.video.title}"


# ==================== USER PDF ACCESS ====================

class UserPDFAccess(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    pdf = models.ForeignKey('PDF', on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    viewed = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    downloaded = models.BooleanField(default=False, editable=False)
    download_count = models.IntegerField(default=0, editable=False)
    last_downloaded = models.DateTimeField(null=True, blank=True, editable=False)
    
    class Meta:
        unique_together = ['user', 'pdf']
    
    def __str__(self):
        return f"{self.user.username} - {self.pdf.title}"
    
    def mark_viewed(self):
        self.viewed = True
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['viewed', 'view_count', 'last_viewed'])


# ==================== COURSE ====================

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_1_month = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    price_12_months = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    materials = models.JSONField(default=list, blank=True)
    duration_weeks = models.IntegerField(default=4)
    thumbnail_s3_key = models.CharField(max_length=500, blank=True, null=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['thumbnail_s3_key']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        self.price_1_month = self.price
        bypass_validation = kwargs.pop('bypass_validation', False)
        if bypass_validation:
            self._state.adding = not self.pk
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    @property
    def thumbnail_url(self):
        from django.conf import settings
        if self.thumbnail_s3_key:
            try:
                if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
                    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.thumbnail_s3_key}"
                else:
                    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.thumbnail_s3_key}"
            except:
                pass
        if self.thumbnail and self.thumbnail.name:
            try:
                return self.thumbnail.url
            except:
                pass
        return None
    
    @property
    def is_s3_thumbnail(self):
        return bool(self.thumbnail_s3_key)
    
    def video_count(self):
        return self.videos.count() if hasattr(self, 'videos') else 0
    
    def pdf_count(self):
        return self.pdf_resources.count() if hasattr(self, 'pdf_resources') else 0


# ==================== USER COURSE ====================
class UserCourse(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_type = models.CharField(max_length=20, choices=[('1_month', '1 Month Access'), ('12_months', '12 Months Access')], default='12_months')
    access_expires_at = models.DateTimeField(null=True, blank=True)
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_lessons = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['access_expires_at']),
            models.Index(fields=['is_active', 'access_expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.access_expires_at:
            self.access_expires_at = timezone.now() + timedelta(days=365)
        if self.access_expires_at and timezone.now() > self.access_expires_at:
            self.is_active = False
        super().save(*args, **kwargs)
    
    def is_access_expired(self):
        if not self.access_expires_at:
            return False
        return timezone.now() > self.access_expires_at
    
    def get_video_access(self):
        videos = self.course.videos.filter(is_active=True)
        for video in videos:
            UserVideoAccess.objects.get_or_create(user=self.user, video=video, defaults={'payment': self.payment})
    
    def get_pdf_access(self):
        pdfs = self.course.pdf_resources.filter(is_active=True)
        for pdf in pdfs:
            UserPDFAccess.objects.get_or_create(user=self.user, pdf=pdf, defaults={'payment': self.payment})
    
    def update_progress(self):
        total_videos = self.course.videos.count()
        total_pdfs = self.course.pdf_resources.count()
        total_lessons = total_videos + total_pdfs
        if total_lessons == 0:
            self.progress = 0
            return
        completed_count = len(self.completed_lessons) if self.completed_lessons else 0
        self.progress = int((completed_count / total_lessons) * 100)


# ==================== MENTORSHIP PROGRAM ====================

class MentorshipProgram(models.Model):
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
    
    def __str__(self):
        return f"{self.mentor_name} - {self.title}"


# ==================== USER ACTIVITY ====================

class UserActivity(models.Model):
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
    video = models.ForeignKey(TrainingVideo, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action}"


# ==================== BLOG MODEL ====================

class Blog(models.Model):
    CATEGORY_CHOICES = [
        ('market_analysis', 'Market Analysis'),
        ('trading_psychology', 'Trading Psychology'),
        ('options_strategies', 'Options Strategies'),
        ('forex_trading', 'Forex Trading'),
        ('company_news', 'Company News'),
        ('education', 'Education'),
        ('general', 'General'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(MfalmeUsers, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    tags = models.CharField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='blog/thumbnails/', blank=True, null=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    read_time = models.IntegerField(default=5)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])
    
    @property
    def featured_image_url(self):
        if not self.featured_image or not self.featured_image.name:
            return None
        try:
            return self.featured_image.url
        except:
            return None


# ==================== PDF MODEL ====================

class PDF(models.Model):
    CATEGORY_CHOICES = [
        ('course_material', 'Course Material'),
        ('ebook', 'E-Book'),
        ('worksheet', 'Worksheet'),
        ('cheat_sheet', 'Cheat Sheet'),
        ('report', 'Market Report'),
        ('guide', 'Trading Guide'),
        ('other', 'Other'),
    ]
    
    ACCESS_LEVEL_CHOICES = [
        ('free', 'Free Access'),
        ('citizen', 'Citizen Tier'),
        ('studyhall', 'Study Hall Tier'),
        ('society', 'Society Tier'),
        ('paid', 'Paid Only'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    pdf_s3_key = models.CharField(max_length=500, blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)
    cover_s3_key = models.CharField(max_length=500, blank=True, null=True)
    cover_image = models.ImageField(upload_to='pdfs/covers/', blank=True, null=True)
    pages = models.IntegerField(default=0)
    file_size = models.CharField(max_length=20, blank=True)
    duration = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    tags = models.CharField(max_length=500, blank=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_resources')
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField(default=True)
    views = models.IntegerField(default=0)
    unique_viewers = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['access_level', 'is_active']),
            models.Index(fields=['course', 'is_active']),
            models.Index(fields=['pdf_s3_key']),
            models.Index(fields=['cover_s3_key']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while PDF.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        self.is_free = (self.price == 0)
        if not self.published_at:
            self.published_at = timezone.now()
        bypass_validation = kwargs.pop('bypass_validation', False)
        if bypass_validation:
            self._state.adding = not self.pk
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    @property
    def file_url(self):
        from django.conf import settings
        if self.pdf_s3_key:
            try:
                if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
                    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.pdf_s3_key}"
                else:
                    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.pdf_s3_key}"
            except:
                pass
        if self.pdf_file and hasattr(self.pdf_file, 'url'):
            try:
                return self.pdf_file.url
            except:
                pass
        return None
    
    @property
    def cover_url(self):
        from django.conf import settings
        if self.cover_s3_key:
            try:
                if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') and settings.AWS_S3_CUSTOM_DOMAIN:
                    return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.cover_s3_key}"
                else:
                    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{self.cover_s3_key}"
            except:
                pass
        if self.cover_image and hasattr(self.cover_image, 'url'):
            try:
                return self.cover_image.url
            except:
                pass
        return None
    
    @property
    def is_s3_pdf(self):
        return bool(self.pdf_s3_key)
    
    @property
    def is_s3_cover(self):
        return bool(self.cover_s3_key)
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


# ========== MERCHANDISE MODELS ==========
class Merchandise(models.Model):
    CATEGORY_CHOICES = [
        ('apparel', 'Apparel'),
        ('accessories', 'Accessories'),
        ('tools', 'Tools'),
        ('books', 'Books'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='apparel')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.URLField(max_length=500, blank=True, null=True)
    image_key = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, default='active', choices=[('active', 'Active'), ('inactive', 'Inactive')])
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']


class MerchandiseOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    delivery_address = models.TextField()
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, default='sasapay')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    order_reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"MBC-ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.order_number


# ========== EVENT MODELS ==========
class Event(models.Model):
    title = models.CharField(max_length=200, default="East & Central Africa Live Leveraging Summit")
    description = models.TextField(blank=True, default="")
    date = models.DateTimeField(default=datetime(2026, 8, 7, 9, 0, 0))
    venue = models.CharField(max_length=300, default="Safari Park Hotel, Nairobi")
    venue_address = models.TextField(blank=True)
    ticket_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=249)
    max_attendees = models.IntegerField(default=500)
    current_bookings = models.IntegerField(default=0)
    poster_image = models.URLField(max_length=500, blank=True, null=True)
    poster_key = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def seats_remaining(self):
        return max(0, self.max_attendees - self.current_bookings)
    
    @property
    def is_sold_out(self):
        return self.current_bookings >= self.max_attendees
    
    def __str__(self):
        return self.title


class EventTicket(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    
    ticket_number = models.CharField(max_length=50, unique=True, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    attendee_name = models.CharField(max_length=200)
    attendee_phone = models.CharField(max_length=20)
    attendee_email = models.EmailField()
    quantity = models.IntegerField(default=1)
    unit_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=249)
    unit_price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=32121)
    total_amount_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, default='sasapay')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    order_reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    qr_code = models.TextField(blank=True, null=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"MBC-TKT-{uuid.uuid4().hex[:8].upper()}"
        if self.quantity:
            self.total_amount_usd = self.quantity * self.unit_price_usd
            self.total_amount_kes = self.quantity * self.unit_price_kes
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.attendee_name}"


# ========== ORDER MODEL ==========
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    reference = models.CharField(max_length=100, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    item_type = models.CharField(max_length=50, choices=[('ticket', 'Ticket'), ('merchandise', 'Merchandise'), ('package', 'Package')])
    items = models.JSONField(default=list)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, default='sasapay')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"MBC-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.reference


# ==================== SIGNALS ====================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MfalmeUsers)
def create_activity_log_for_new_user(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance,
            action='REGISTER',
            description=f'New user registered: {instance.username}',
            metadata={'email': instance.email}
        )


@receiver(post_save, sender=UserCourse)
def grant_course_access(sender, instance, created, **kwargs):
    if created:
        instance.get_video_access()
        instance.get_pdf_access()
        Notification.objects.create(
            user=instance.user,
            title='Course Enrolled',
            message=f'You have successfully enrolled in {instance.course.title}.',
            notification_type='SUCCESS',
            related_object_type='course',
            related_object_id=instance.course.id
        )


# ==================== ADMIN COMPATIBILITY ALIASES ====================

Video = TrainingVideo
Activity = ActivityLog
Partnership = PartnershipProgram