# myapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    MfalmeUsers, VerificationCode, PaymentTransaction, Subscription,
    Package, EducationProgram, UserEducationEnrollment,
    PartnershipProgram, UserPartnership, Testimonial, FAQ,
    CommunityTier, UserCommunityMembership, Brokerage,
    ContactSubmission, SiteContent, SiteContentVersion,
    Statistic, Notification, ActivityLog, SystemSettings,
    SupportTicket, TicketReply, UserSession, HeroSlider,
    AboutSection, PaymentMethod, ContactInfo, Logo,
    TrainingVideo, UserVideoAccess, Course, UserCourse,
    MentorshipProgram, UserActivity
)

# ==================== CUSTOM USER ADMIN ====================

@admin.register(MfalmeUsers)
class MfalmeUsersAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'soldier_id', 'elite_rank', 'email_verified', 
                    'account_balance', 'is_active', 'date_joined')
    list_filter = ('email_verified', 'is_active', 'is_staff', 'is_superuser', 
                   'elite_rank', 'account_status', 'date_joined')
    search_fields = ('email', 'username', 'phone', 'soldier_id', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('soldier_id', 'referral_code', 'date_joined', 'last_login', 
                       'password_changed_at', 'updated_at', 'view_referrals')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'password', 'username', 'phone', 
                      'first_name', 'last_name')
        }),
        ('Soldier Profile', {
            'fields': ('soldier_id', 'elite_rank', 'profile_image', 'bio')
        }),
        ('Verification Status', {
            'fields': ('email_verified', 'verification_sent_at', 'verified_at', 'account_status')
        }),
        ('Contact Information', {
            'fields': ('whatsapp_number', 'telegram_username', 'country', 'city', 'address')
        }),
        ('Trading Information', {
            'fields': ('trading_experience', 'investment_amount', 'preferred_package',
                      'trading_platform', 'broker_name', 'account_balance')
        }),
        ('Referral System', {
            'fields': ('referral_code', 'referred_by', 'referral_count', 
                      'referral_earnings', 'view_referrals')
        }),
        ('Statistics', {
            'fields': ('total_deposits', 'total_withdrawals', 'total_profit', 
                      'total_loss', 'success_rate')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login', 'last_activity', 
                      'registration_time', 'updated_at')
        }),
        ('Technical Info', {
            'fields': ('registration_ip', 'user_agent', 'registration_device', 
                      'registration_location', 'admin_notes')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone', 'password1', 'password2'),
        }),
    )
    
    def view_referrals(self, obj):
        if obj.referral_count > 0:
            url = reverse('admin:myapp_mfalmeusers_changelist') + f'?referred_by__id__exact={obj.id}'
            return format_html('<a href="{}">{} Referrals</a>', url, obj.referral_count)
        return "No referrals"
    view_referrals.short_description = "Referrals"

# ==================== VERIFICATION CODE ADMIN ====================

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'code_type', 'is_used', 'is_expired', 'created_at', 'expires_at')
    list_filter = ('is_used', 'code_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'code', 'transaction_ref')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at', 'time_remaining')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

# ==================== PAYMENT TRANSACTION ADMIN ====================

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'amount', 'currency', 'status', 
                    'payment_type', 'payment_method', 'created_at', 'is_verified')
    list_filter = ('status', 'payment_type', 'payment_method', 'currency', 'created_at')
    search_fields = ('reference', 'user__email', 'user__username', 
                    'customer_email', 'customer_phone', 'external_reference')
    readonly_fields = ('reference', 'external_reference', 'created_at', 'updated_at',
                      'initiated_at', 'paid_at', 'completed_at', 'failed_at',
                      'net_amount', 'view_user')
    list_per_page = 50
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('reference', 'external_reference', 'user', 'view_user', 
                      'amount', 'currency', 'status', 'payment_type', 'payment_method')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'customer_phone', 'customer_name')
        }),
        ('Service Details', {
            'fields': ('package_type', 'package_name', 'program_type', 'program_name',
                      'partnership_tier', 'partnership_name', 'description')
        }),
        ('Payment Processing', {
            'fields': ('transaction_fee', 'net_amount', 'authorization_url', 
                      'access_code', 'paystack_status', 'paystack_message')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'initiated_at', 'paid_at', 'completed_at', 
                      'failed_at', 'updated_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'notes', 'ip_address', 'user_agent', 'paystack_data')
        }),
    )
    
    def view_user(self, obj):
        if obj.user:
            url = reverse('admin:myapp_mfalmeusers_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return "No user"
    view_user.short_description = "User Profile"
    
    def has_add_permission(self, request):
        return False

# ==================== SUBSCRIPTION ADMIN ====================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'plan_type', 'status', 'amount', 
                    'next_payment_date', 'is_active', 'created_at')
    list_filter = ('status', 'plan_type', 'service_type')
    search_fields = ('user__email', 'user__username', 'plan_name', 
                    'paystack_subscription_code')
    readonly_fields = ('created_at', 'updated_at', 'next_payment_date', 'end_date')
    
    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    is_active.short_description = 'Active'

# ==================== PACKAGE ADMIN ====================

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'package_type', 'price', 'discounted_price', 
                    'is_featured', 'is_popular', 'is_active', 'total_sales', 'order')
    list_editable = ('price', 'is_featured', 'is_popular', 'is_active', 'order')
    list_filter = ('is_active', 'package_type', 'is_featured', 'is_popular')
    search_fields = ('name', 'short_description', 'full_description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('total_sales', 'total_revenue', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'package_type', 'short_description', 'full_description')
        }),
        ('Pricing', {
            'fields': ('price', 'original_price', 'discount_percentage', 'discounted_price')
        }),
        ('Media', {
            'fields': ('image', 'thumbnail')
        }),
        ('Features', {
            'fields': ('features', 'benefits')
        }),
        ('Duration & Access', {
            'fields': ('duration_days', 'is_recurring', 'recurrence_interval',
                      'minimum_investment', 'required_experience')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active', 'is_popular', 'order')
        }),
        ('Payment', {
            'fields': ('payment_url', 'payment_options')
        }),
        ('Statistics', {
            'fields': ('total_sales', 'total_revenue')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# ==================== EDUCATION PROGRAM ADMIN ====================

@admin.register(EducationProgram)
class EducationProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'program_type', 'price_1_month', 'price_12_months', 
                    'discount_percentage', 'is_popular', 'is_featured', 'is_active', 'order')
    list_editable = ('price_1_month', 'price_12_months', 'is_popular', 'is_featured', 
                    'is_active', 'order')
    list_filter = ('is_active', 'program_type', 'is_popular', 'is_featured')
    search_fields = ('name', 'short_description', 'full_description')
    prepopulated_fields = {'slug': ('program_type', 'name')}
    readonly_fields = ('enrolled_count', 'completion_rate', 'created_at', 'updated_at')
    
    def discount_percentage(self, obj):
        discount = obj.get_discount_percentage('1_month')
        if discount > 0:
            return f"{discount}%"
        return "0%"
    discount_percentage.short_description = 'Discount'

# ==================== USER EDUCATION ENROLLMENT ADMIN ====================

@admin.register(UserEducationEnrollment)
class UserEducationEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'enrollment_type', 'status', 'progress_percentage',
                    'enrolled_at', 'days_remaining', 'certificate_issued')
    list_filter = ('status', 'enrollment_type', 'program__program_type')
    search_fields = ('user__email', 'user__username', 'program__name')
    readonly_fields = ('enrolled_at', 'progress_percentage', 'days_remaining',
                      'certificate_issued_at', 'completed_at')
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Remaining'

# ==================== PARTNERSHIP PROGRAM ADMIN ====================

@admin.register(PartnershipProgram)
class PartnershipProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'price', 'minimum_investment', 'risk_level',
                    'is_active', 'order', 'total_partners', 'total_investment')
    list_editable = ('price', 'is_active', 'order')
    list_filter = ('is_active', 'tier', 'risk_level')
    search_fields = ('name', 'short_description')
    readonly_fields = ('total_partners', 'total_investment', 'created_at', 'updated_at')

# ==================== USER PARTNERSHIP ADMIN ====================

@admin.register(UserPartnership)
class UserPartnershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'investment_amount', 'status', 'start_date',
                    'duration_months', 'actual_returns', 'contract_signed')
    list_filter = ('status', 'program__tier', 'start_date')
    search_fields = ('user__email', 'user__username', 'program__name', 'contract_number')
    readonly_fields = ('contract_number', 'created_at', 'updated_at', 'months_remaining')
    
    def months_remaining(self, obj):
        return obj.months_remaining
    months_remaining.short_description = 'Months Remaining'

# ==================== TESTIMONIAL ADMIN ====================

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'rating', 'program', 'is_featured', 
                    'is_verified', 'is_active', 'order', 'created_at')
    list_editable = ('is_featured', 'is_verified', 'is_active', 'order')
    list_filter = ('is_active', 'is_featured', 'is_verified', 'program', 'rating')
    search_fields = ('name', 'title', 'content', 'company')
    readonly_fields = ('created_at', 'updated_at', 'verified_at')

# ==================== FAQ ADMIN ====================

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_featured', 'is_active', 'order',
                    'views_count', 'helpful_count')
    list_editable = ('is_featured', 'is_active', 'order')
    list_filter = ('category', 'is_active', 'is_featured')
    search_fields = ('question', 'answer')
    readonly_fields = ('views_count', 'helpful_count', 'not_helpful_count',
                      'created_at', 'updated_at')

# ==================== COMMUNITY TIER ADMIN ====================

@admin.register(CommunityTier)
class CommunityTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'access_level', 'member_count', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'tier', 'access_level')
    search_fields = ('name', 'description')
    readonly_fields = ('member_count', 'created_at', 'updated_at')

# ==================== USER COMMUNITY MEMBERSHIP ADMIN ====================

@admin.register(UserCommunityMembership)
class UserCommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'status', 'joined_at', 'days_remaining',
                    'access_granted')
    list_filter = ('status', 'community__tier', 'access_granted')
    search_fields = ('user__email', 'user__username', 'community__name')
    readonly_fields = ('joined_at', 'days_remaining', 'access_granted_at')
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Remaining'

# ==================== BROKERAGE ADMIN ====================

@admin.register(Brokerage)
class BrokerageAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'trust_score', 'regulation_score', 
                    'platform_score', 'overall_score', 'is_recommended', 'is_active')
    list_editable = ('is_recommended', 'is_active')
    list_filter = ('region', 'is_recommended', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('overall_score', 'referral_count', 'created_at', 'updated_at')

# ==================== CONTACT SUBMISSION ADMIN ====================

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'package', 'status', 'priority',
                    'created_at', 'assigned_to', 'view_message')
    list_filter = ('status', 'priority', 'created_at', 'package', 'program')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    readonly_fields = ('name', 'email', 'phone', 'package', 'program', 'subject',
                      'message', 'ip_address', 'user_agent', 'created_at', 'updated_at')
    list_editable = ('status', 'priority', 'assigned_to')
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']
    
    def view_message(self, obj):
        if obj.message:
            return format_html('<details><summary>View Message</summary><p>{}</p></details>', 
                             obj.message)
        return "No message"
    view_message.short_description = 'Message'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read')
        self.message_user(request, f'{updated} submissions marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_replied(self, request, queryset):
        updated = queryset.update(status='replied', replied_at=timezone.now())
        self.message_user(request, f'{updated} submissions marked as replied.')
    mark_as_replied.short_description = "Mark selected as replied"
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} submissions marked as archived.')
    mark_as_archived.short_description = "Mark selected as archived"

# ==================== SITE CONTENT ADMIN ====================

@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ('section', 'title', 'is_active', 'version', 'created_at')
    list_filter = ('section', 'is_active')
    search_fields = ('title', 'subtitle', 'content')
    readonly_fields = ('version', 'created_at', 'updated_at')

@admin.register(SiteContentVersion)
class SiteContentVersionAdmin(admin.ModelAdmin):
    list_display = ('content', 'version', 'updated_by', 'created_at')
    list_filter = ('content__section', 'created_at')
    search_fields = ('content__title', 'content_text')
    readonly_fields = ('content', 'version', 'updated_by', 'created_at')

# ==================== STATISTIC ADMIN ====================

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'suffix', 'color', 'is_active', 'order')
    list_editable = ('value', 'suffix', 'color', 'is_active', 'order')
    list_filter = ('is_active', 'color')
    search_fields = ('title', 'description')

# ==================== NOTIFICATION ADMIN ====================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'is_important',
                    'created_at', 'read_at')
    list_filter = ('notification_type', 'is_read', 'is_important', 'created_at')
    search_fields = ('user__email', 'user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected as read"

# ==================== ACTIVITY LOG ADMIN ====================

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'severity', 'created_at', 'ip_address')
    list_filter = ('action', 'severity', 'created_at')
    search_fields = ('user__email', 'user__username', 'description', 'ip_address')
    readonly_fields = ('created_at',)

# ==================== SYSTEM SETTINGS ADMIN ====================

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'category', 'setting_type', 'is_public', 'is_active')
    list_filter = ('category', 'setting_type', 'is_public', 'is_active')
    search_fields = ('key', 'description', 'value')
    readonly_fields = ('version', 'created_at', 'updated_at')

# ==================== SUPPORT TICKET ADMIN ====================

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'subject', 'category', 'status',
                    'priority', 'created_at', 'assigned_to')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_number', 'user__email', 'user__username', 'subject')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.ticket_number:
            obj.ticket_number = f"TICKET{timezone.now().strftime('%Y%m%d')}{obj.user.id:06d}"
        super().save_model(request, obj, form, change)

# ==================== TICKET REPLY ADMIN ====================

@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'is_internal', 'is_read', 'created_at')
    list_filter = ('is_internal', 'is_read', 'created_at')
    search_fields = ('ticket__ticket_number', 'user__email', 'user__username', 'message')
    readonly_fields = ('created_at', 'updated_at', 'read_at')

# ==================== USER SESSION ADMIN ====================

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'device_type', 'country', 'is_active',
                    'login_at', 'last_activity', 'duration')
    list_filter = ('is_active', 'device_type', 'country', 'login_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'device_name')
    readonly_fields = ('login_at', 'last_activity', 'logout_at', 'duration')
    
    def duration(self, obj):
        return obj.duration
    duration.short_description = 'Session Duration'

# ==================== HERO SLIDER ADMIN ====================

@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')

# ==================== ABOUT SECTION ADMIN ====================

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')

# ==================== PAYMENT METHOD ADMIN ====================

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

# ==================== CONTACT INFO ADMIN ====================

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('phone', 'email', 'hours')

# ==================== LOGO ADMIN ====================

@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name',)

# ==================== TRAINING VIDEO ADMIN ====================

@admin.register(TrainingVideo)
class TrainingVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'duration', 'view_count',
                    'allow_download', 'is_active', 'order', 'created_at')
    list_editable = ('price', 'duration', 'allow_download', 'is_active', 'order')
    list_filter = ('category', 'is_active', 'allow_download')
    search_fields = ('title', 'description')
    readonly_fields = ('view_count', 'created_at')

# ==================== USER VIDEO ACCESS ADMIN ====================

@admin.register(UserVideoAccess)
class UserVideoAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'unlocked_at', 'has_payment')
    list_filter = ('unlocked_at', 'video__category')
    search_fields = ('user__email', 'user__username', 'video__title')
    readonly_fields = ('unlocked_at',)
    
    def has_payment(self, obj):
        return obj.payment is not None
    has_payment.boolean = True
    has_payment.short_description = 'Paid'

# ==================== COURSE ADMIN ====================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'duration_weeks', 'is_active', 'created_at')
    list_editable = ('price', 'duration_weeks', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

# ==================== USER COURSE ADMIN ====================

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'progress', 'is_completed')
    list_filter = ('enrolled_at', 'course')
    search_fields = ('user__email', 'user__username', 'course__title')
    readonly_fields = ('enrolled_at', 'progress')
    
    def is_completed(self, obj):
        return obj.progress >= 100
    is_completed.boolean = True
    is_completed.short_description = 'Completed'

# ==================== MENTORSHIP PROGRAM ADMIN ====================

@admin.register(MentorshipProgram)
class MentorshipProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentor_name', 'mentor_role', 'price',
                    'sessions_per_week', 'duration_months', 'is_available', 'is_active')
    list_editable = ('price', 'sessions_per_week', 'duration_months', 
                    'is_available', 'is_active')
    list_filter = ('is_available', 'is_active')
    search_fields = ('title', 'mentor_name', 'description')
    readonly_fields = ('created_at',)

# ==================== USER ACTIVITY ADMIN ====================

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'description', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'user__username', 'description', 'ip_address')
    readonly_fields = ('created_at',)

# ==================== CUSTOM ADMIN SITE ====================

class MfalmeAdminSite(admin.AdminSite):
    site_header = "MFALME BETTERDAYS CAPITAL Administration"
    site_title = "MFALME Admin Portal"
    index_title = "Dashboard"
    
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_list = super().get_app_list(request)
        
        # Sort the models within each app
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
        
        return app_list

# Create custom admin site instance
admin_site = MfalmeAdminSite(name='mfalme_admin')

# Unregister default admin models if they were registered
try:
    admin.site.unregister(Group)
except:
    pass

# Register all models with the custom admin site
models_to_register = [
    (MfalmeUsers, MfalmeUsersAdmin),
    (VerificationCode, VerificationCodeAdmin),
    (PaymentTransaction, PaymentTransactionAdmin),
    (Subscription, SubscriptionAdmin),
    (Package, PackageAdmin),
    (EducationProgram, EducationProgramAdmin),
    (UserEducationEnrollment, UserEducationEnrollmentAdmin),
    (PartnershipProgram, PartnershipProgramAdmin),
    (UserPartnership, UserPartnershipAdmin),
    (Testimonial, TestimonialAdmin),
    (FAQ, FAQAdmin),
    (CommunityTier, CommunityTierAdmin),
    (UserCommunityMembership, UserCommunityMembershipAdmin),
    (Brokerage, BrokerageAdmin),
    (ContactSubmission, ContactSubmissionAdmin),
    (SiteContent, SiteContentAdmin),
    (SiteContentVersion, SiteContentVersionAdmin),
    (Statistic, StatisticAdmin),
    (Notification, NotificationAdmin),
    (ActivityLog, ActivityLogAdmin),
    (SystemSettings, SystemSettingsAdmin),
    (SupportTicket, SupportTicketAdmin),
    (TicketReply, TicketReplyAdmin),
    (UserSession, UserSessionAdmin),
    (HeroSlider, HeroSliderAdmin),
    (AboutSection, AboutSectionAdmin),
    (PaymentMethod, PaymentMethodAdmin),
    (ContactInfo, ContactInfoAdmin),
    (Logo, LogoAdmin),
    (TrainingVideo, TrainingVideoAdmin),
    (UserVideoAccess, UserVideoAccessAdmin),
    (Course, CourseAdmin),
    (UserCourse, UserCourseAdmin),
    (MentorshipProgram, MentorshipProgramAdmin),
    (UserActivity, UserActivityAdmin),
]

# Register all models
for model, admin_class in models_to_register:
    admin_site.register(model, admin_class)

# Also register Group for permissions
admin_site.register(Group)

# ==================== ADMIN DASHBOARD CUSTOMIZATION ====================

# Override the default admin site
admin.site = admin_site
admin.autodiscover()