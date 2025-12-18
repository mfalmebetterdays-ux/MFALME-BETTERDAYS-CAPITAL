from django.db import models
from django.utils import timezone
from datetime import timedelta

# Users model - SIMPLIFIED VERSION
class MfalmeUsers(models.Model):
    email = models.EmailField(unique=True)
    password = models.TextField() 
    username = models.CharField(max_length=30)
    phone = models.CharField(max_length=30)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    soldier_id = models.IntegerField(unique=True, null=True, blank=True)
    
    # User status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.email} : {self.username}'
    
    def save(self, *args, **kwargs):
        # Auto-generate soldier ID for new users
        if not self.pk and not self.soldier_id:
            last_user = MfalmeUsers.objects.all().order_by('-id').first()
            if last_user and last_user.soldier_id:
                self.soldier_id = last_user.soldier_id + 1
            else:
                self.soldier_id = 1001  # Starting soldier ID
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

# Verification Code model - SIMPLIFIED
class VerificationCode(models.Model):
    user = models.ForeignKey(MfalmeUsers, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.user.email} - {self.code}'
    
    def save(self, *args, **kwargs):
        # Auto-set expiry (15 minutes from creation)
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=15)
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