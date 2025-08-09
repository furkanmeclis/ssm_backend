from django.contrib import admin
from .models import PaymentPlan, Payment
from django.utils.html import format_html
from django import forms
from utils.admin_tools import StaffPermissionMixin

class PaymentPlanAdmin(StaffPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'days', 'final_price', 'discount', 'total_price_display', 'is_active')
    list_filter = ('days', 'is_active')
    search_fields = ('title', 'description',)
    readonly_fields = ('total_price_display',)

    def total_price(self, obj):
        # Ensure both final_price and discount are handled correctly
        final_price = obj.final_price if obj.final_price is not None else 0
        discount = obj.discount if obj.discount is not None else 0
        return round(final_price + discount, 2)

    def total_price_display(self, obj):
        total_price = self.total_price(obj)  # Now this returns a calculated total price
        if obj.discount:
            return format_html('<strong>İndirimsiz Fiyat:</strong> {}', total_price)
        return total_price
    total_price_display.short_description = 'Toplam Fiyat'

    class Media:
        js = ('js/payment_plan.js',)

class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = '__all__'

class PaymentAdmin(StaffPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'payment_plan', 'merchant_oid', 'status_with_emoji', 'total_payment_amount', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at', 'currency')
    search_fields = ('merchant_oid', 'user__email', 'user__name')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields]
        return []

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def status_with_emoji(self, obj):
        if obj.status == 'ongoing':
            return '⏳ Devam Ediyor'
        elif obj.status == 'successful':
            return '✅ Başarılı'
        elif obj.status == 'denied':
            return '❌ Reddedildi'
    status_with_emoji.short_description = 'Durum'

admin.site.register(PaymentPlan, PaymentPlanAdmin)
admin.site.register(Payment, PaymentAdmin)
