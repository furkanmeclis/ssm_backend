from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.utils import timezone
from exams.models import Exam
from grades.models import GradeLevel
import uuid
import os
import random

@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.sub_path, filename)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('E-posta adresi zorunludur.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('phone_number') is None:
            # Generate a random 10-digit phone number if not provided
            random_phone_number = ''.join(["%s" % random.randint(0, 9) for num in range(0, 10)])
            extra_fields.setdefault('phone_number', random_phone_number)
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, error_messages={'unique': "Geçersiz e-posta adresi."}, verbose_name="E-posta")
    name = models.CharField(max_length=50, verbose_name="İsim")
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="Telefon Numarası")
    profile_image = models.URLField(max_length=255, null=True, blank=True, verbose_name="Profil Resmi")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Katılma Tarihi")
    is_staff = models.BooleanField(default=False, verbose_name="Personel mi?")
    is_verified = models.BooleanField(default=False, verbose_name="Doğrulandı mı?")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    last_password_reset = models.DateTimeField(null=True, blank=True, verbose_name="Son Şifre Sıfırlama")
    exams = models.ManyToManyField(Exam, related_name='users', blank=True, verbose_name="Sınavlar")
    grade = models.PositiveSmallIntegerField(choices=GradeLevel.choices, null=True, blank=True, verbose_name="Sınıf")
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Abonelik Bitiş Tarihi")
    device_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="Device ID")
    is_anonymous_user = models.BooleanField(default=False, verbose_name="Anonymous User")

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number']
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"

class VerificationCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    code = models.CharField(max_length=5, verbose_name="Kod")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    expires_at = models.DateTimeField(verbose_name="Son Kullanma Tarihi")

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.localtime() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.localtime() > self.expires_at
    
    @staticmethod
    def is_limit_reached(user):
        resend_limit = settings.EMAIL_RESEND_LIMIT
        time_limit = timezone.localtime() - timezone.timedelta(minutes=30)
        recent_requests_count = VerificationCode.objects.filter(user=user, created_at__gte=time_limit).count()
        return recent_requests_count >= resend_limit

    def __str__(self):
        return f'{self.user.email} - {self.code}'
