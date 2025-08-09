from users.models import VerificationCode, CustomUser
from django.core.exceptions import ObjectDoesNotExist

class VerificationError(Exception):
    def __init__(self, message):
        self.message = message

def validate_user_verification_code(code, email):
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        raise VerificationError("Geçersiz e-posta adresi.")
    
    try:
        verification_code = VerificationCode.objects.get(user=user, code=code)
    except VerificationCode.DoesNotExist:
        raise VerificationError("Geçersiz doğrulama kodu.")

    if verification_code.is_expired():
        raise VerificationError("Doğrulama kodunun süresi dolmuş.")

    return user, verification_code
