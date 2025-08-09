from django.db import models

class PaymentPlan(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True, verbose_name="Başlık")
    description = models.TextField(null=True, blank=True, verbose_name="Açıklama")
    days = models.PositiveIntegerField(verbose_name="Gün Sayısı", help_text="Kullanıcıların ödeme sonrası abonelik süresine eklenecek ekstra gün sayısı.")
    final_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Son Fiyat", help_text="Kullanıcıların ödeyeceği toplam ücret. İndirim miktarı bunu etkilemez. Son fiyat.")
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="İndirim", help_text="Toplam fiyat üzerinden yapılacak indirim. Girilmezse indirim yapılmaz.")
    is_active = models.BooleanField(default=True, verbose_name="Aktif Mi?")

    def __str__(self):
        return f"{self.title} - {self.days} Gün"

    def total_price(self):
        if self.discount:
            return round(self.final_price + self.discount, 2)
        return self.total_price

    class Meta:
        verbose_name = "Ödeme Planı"
        verbose_name_plural = "Ödeme Planları"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Devam Ediyor'),
        ('successful', 'Başarılı'),
        ('denied', 'Reddedildi'),
    ]

    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, verbose_name="Kullanıcı")
    user_address = models.TextField(verbose_name="Kullanıcı Adresi")
    payment_plan = models.ForeignKey('PaymentPlan', on_delete=models.SET_NULL, null=True, verbose_name="Ödeme Planı")
    merchant_oid = models.CharField(max_length=20, unique=True, verbose_name="Eşşiz İşlem Numarası")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ongoing', verbose_name="Durum")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    user_ip = models.GenericIPAddressField(verbose_name="Kullanıcı IP Adresi")
    user_basket = models.TextField(verbose_name="Kullanıcı Sepeti")
    total_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Ödeme Miktarı")
    currency = models.CharField(max_length=3, default='TL', verbose_name="Para Birimi")
    installment_info = models.CharField(max_length=255, verbose_name="Taksit Bilgisi")
    subscription_end_date_before_payment = models.DateTimeField(null=True, blank=True, verbose_name="Ödeme Öncesi Abonelik Bitiş Tarihi")
    subscription_end_date_after_payment = models.DateTimeField(null=True, blank=True, verbose_name="Ödeme Sonrası Abonelik Bitiş Tarihi")

    def __str__(self):
        return f"Ödeme {self.merchant_oid} - {self.status}"

    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
