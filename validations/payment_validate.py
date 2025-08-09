from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from paytr.models import PaymentPlan
from utils.ip_whitelist import get_client_ip

def validate_request_data(request):
    user_ip = get_client_ip(request)
    user_address = request.data.get('user_address')
    payment_plan_id = request.data.get('payment_plan_id')

    if not user_ip:
        raise ValidationError("user_ip adresi gereklidir.")

    # Validate user_address
    if not user_address:
        raise ValidationError("'user_address' gereklidir ve geçerli bir string olmalıdır.")
    user_address = str(user_address)
    if len(user_address) > 400:
        raise ValidationError("'user_address' 400 karakterden az olmalıdır.")

    if not payment_plan_id:
        raise ValidationError("'payment_plan_id' gereklidir.")

    payment_plan = get_object_or_404(PaymentPlan, id=payment_plan_id, is_active=True)
    payment_amount = int(payment_plan.final_price)

    return user_ip, payment_amount * 100, user_address, payment_plan # Convert payment amount to pennies for PayTR
