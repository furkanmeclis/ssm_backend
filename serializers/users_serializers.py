from rest_framework import serializers
from email_validator import validate_email as external_validate_email, EmailNotValidError
from users.models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from services.digitalocean_service import process_image_and_upload_to_digitalocean
from serializers.exam_serializers import SimpleExamSerializer
from grades.models import GradeLevel
import uuid
import random

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)
    profile_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('email', 'profile_image', 'phone_number', 'password', 'password_confirmation', 'name')

    def validate_email(self, value):
        try:
            external_validate_email(value)
        except EmailNotValidError as e:
            raise serializers.ValidationError(f"Geçersiz e-posta adresi: {e}")
        return value

    def validate_phone_number(self, value):
        cleaned_phone_number = value.replace(" ", "").replace("-", "").replace("+", "")
        if not cleaned_phone_number.isdigit() or len(cleaned_phone_number) > 15:
            raise serializers.ValidationError("Geçersiz telefon numarası.")
        return cleaned_phone_number

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation', None)
        profile_image = validated_data.pop('profile_image', None)
        user = CustomUser.objects.create_user(**validated_data)

        if profile_image:
            image_url = process_image_and_upload_to_digitalocean(profile_image, "profile_images", 1000, 1000)
            if image_url:
                user.profile_image = image_url
                user.save()

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("E-posta adresi veya şifre hatalı. Lütfen tekrar deneyin.")
        
        data['user'] = user
        return data

class ResendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            external_validate_email(value)
        except EmailNotValidError as e:
            raise serializers.ValidationError("Geçersiz e-posta adresi.")

        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Geçersiz e-posta adresi.")
        
        return value

class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=5)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Doğrulama kodu sadece rakamlardan oluşmalıdır.")
        return value
    
class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mevcut şifreniz hatalı.')
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")
        return data
    
class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True, required=False)
    exams = SimpleExamSerializer(many=True, read_only=True)
    grade = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'name', 'phone_number',
            'profile_image', 'date_joined', 'is_staff', 'is_verified', 'subscription_end_date',
            'last_password_reset', 'exams', 'grade', 'device_id', 'is_anonymous_user'
        ]
        read_only_fields = ['id', 'email', 'phone_number', 'date_joined', 'is_staff', 'is_verified', 'device_id', 'is_anonymous_user']

    def validate_email(self, value):
        instance = self.instance
        if instance and instance.email != value:
            raise serializers.ValidationError("E-posta adresi güncellenemez.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add profile image URL to the response data if it exists
        data['profile_image'] = instance.profile_image if instance.profile_image else None
        return data

    def get_grade(self, obj):
        return {'id': obj.grade, 'name': GradeLevel(obj.grade).label} if obj.grade else None

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            external_validate_email(value)
        except EmailNotValidError as e:
            raise serializers.ValidationError("Geçersiz e-posta adresi.")

        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Geçersiz e-posta adresi.")
        
        return value

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=5)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Doğrulama kodu sadece rakamlardan oluşmalıdır.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")
        return data

    def validate_email(self, value):
        try:
            external_validate_email(value)
        except EmailNotValidError as e:
            raise serializers.ValidationError("Geçersiz e-posta adresi.")

        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Geçersiz e-posta adresi.")
        
        return value

class AnonymousUserRegistrationSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(max_length=255, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['device_id']
        
    def create(self, validated_data):
        device_id = validated_data.get('device_id')
        
        # Generate random values for required fields
        random_email = f"misafir_{uuid.uuid4().hex}@misafir.com"
        random_password = uuid.uuid4().hex
        random_name = "Misafir"
        random_phone_number = ''.join(["%s" % random.randint(0, 9) for num in range(0, 10)])
        
        user = CustomUser.objects.create_user(
            email=random_email,
            password=random_password,
            name=random_name,
            phone_number=random_phone_number,
            device_id=device_id,
            is_anonymous_user=True,
            is_verified=True
        )
        
        return user

class AnonymousUserUpgradeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'password', 'password_confirmation', 'phone_number']
    
    def validate_email(self, value):
        try:
            external_validate_email(value)
        except EmailNotValidError as e:
            raise serializers.ValidationError(f"Geçersiz e-posta adresi: {e}")
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu e-posta adresi zaten kullanılıyor.")
            
        return value
    
    def validate_phone_number(self, value):
        cleaned_phone_number = value.replace(" ", "").replace("-", "").replace("+", "")
        if not cleaned_phone_number.isdigit() or len(cleaned_phone_number) > 15:
            raise serializers.ValidationError("Geçersiz telefon numarası.")
        return cleaned_phone_number
    
    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Şifreler eşleşmiyor.")
        return data
