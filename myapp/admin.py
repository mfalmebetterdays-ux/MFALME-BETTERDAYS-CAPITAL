# myapp/admin.py
from django.contrib import admin
from .models import MfalmeUsers, VerificationCode

@admin.register(MfalmeUsers)
class MfalmeUsersAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'soldier_id', 'email_verified', 'date_joined')
    list_filter = ('email_verified', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'phone')
    ordering = ('-date_joined',)

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'is_expired', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'code')
    ordering = ('-created_at',)