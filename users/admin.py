from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.authtoken.models import TokenProxy as DRFToken
from utils.admin_tools import StaffViewPermissionMixin
from users.models import CustomUser, VerificationCode

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'name', 'phone_number', 'profile_image', 'grade', 'exams')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'name', 'phone_number', 'profile_image', 'grade', 'exams')

class CustomUserAdmin(StaffViewPermissionMixin, BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    readonly_fields = ('date_joined', 'last_login', 'last_password_reset')
    fieldsets = (
        (None, {'fields': ('email',)}),
        (_('Personal info'), {'fields': ('name', 'phone_number', 'profile_image', 'grade', 'exams')}),
        (_('Subscription info'), {'fields': ('subscription_end_date',)}),
        (_('Permissions'), {'fields': ('is_verified', 'is_staff', 'is_superuser',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_password_reset')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'grade', 'exams'),
        }),
    )
    list_display = ('id', 'email', 'name', 'phone_number', 'grade', 'is_verified', 'subscription_end_date')
    search_fields = ('email', 'name', )
    ordering = ('email',)

    def has_add_permission(self, request, obj=None):
        return False

admin.site.register(CustomUser, CustomUserAdmin)
# admin.site.register(VerificationCode)
admin.site.unregister(Group)
admin.site.unregister(DRFToken)
admin.site.unregister(OutstandingToken)
admin.site.unregister(BlacklistedToken)
