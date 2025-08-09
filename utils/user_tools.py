from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import VerificationCode
from django.utils import timezone
import random

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_info(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user_email = request.user.email
        return f"ID: {user_id}, Email: {user_email}"
    return "Anonymous"

def get_user_from_token(request):
    """
    Manually authenticate the token to set the user.
    """
    jwt_authentication = JWTAuthentication()
    try:
        auth_result = jwt_authentication.authenticate(request)
        if auth_result is not None:
            request.user, request.auth = auth_result
    except AuthenticationFailed:
        pass

def check_user_resend_limit(user, check_verified=True):
    """
    Check if the user has reached the resend limit for the verification code.
    """
    if VerificationCode.is_limit_reached(user):
        return False, "Doğrulama kodu gönderme limitine ulaştınız. Lütfen daha sonra tekrar deneyin."
    elif check_verified and user.is_verified:
        return False, "E-posta adresiniz zaten doğrulanmış."
    return True, ""

def generate_5_digit_verification_code(user):
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    VerificationCode.objects.create(user=user, code=verification_code)
    return verification_code

def check_subscription_validity(user):
    if user.subscription_end_date and user.subscription_end_date >= timezone.localtime():
        return True, "Abonelik geçerli."
    elif user.subscription_end_date and user.subscription_end_date < timezone.localtime():
        return False, "Abonelik süresi dolmuş ve ücretsiz deneme hakkı kalmamış."
    else:
        return False, "Abonelik geçerli değil."
