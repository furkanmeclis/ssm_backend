import json
import requests
import base64
from rest_framework.exceptions import ValidationError
from paytr.models import Payment

def send_payment_request(params):
    result = requests.post('https://www.paytr.com/odeme/api/get-token', params)
    return json.loads(result.text)

def handle_payment_response(user, response, payment_params):
    if response['status'] == 'success':
        Payment.objects.create(
            user=user,
            merchant_oid=payment_params['merchant_oid'],
            payment_plan=payment_params['payment_plan'],
            user_address=payment_params['user_address'],
            status='ongoing',
            user_ip=payment_params['user_ip'],
            user_basket=payment_params['detailed_item'],
            total_payment_amount=payment_params['payment_amount'] / 100, # Convert pennies back to TL 
            currency=payment_params['currency'],
            installment_info=f"{payment_params['no_installment']} installments - {payment_params['max_installment']} max installments",
        )
        return f"https://www.paytr.com/odeme/guvenli/{response['token']}"
    else:
        raise ValidationError(f"Payment request failed: {response.get('reason', 'Unknown error')}")

def user_basket_encode(payment_plan):
    # Detailed format for internal use or debugging
    detailed_item = {
        "payment_plan_id": payment_plan.id,
        "days": payment_plan.days,
        "total_price": str(payment_plan.total_price),
        "discount": str(payment_plan.discount) if payment_plan.discount else "0",
        "final_price": str(payment_plan.final_price),
    }

    # Simplified format for PayTR submission
    simplified_item = [
        payment_plan.id,
        str(payment_plan.final_price),  # Final price (as string, formatted correctly)
        payment_plan.title,         # Item title
    ]

    # We'll base64 encode only the simplified format as required by PayTR
    user_basket = json.dumps([simplified_item])
    encoded_basket = base64.b64encode(user_basket.encode())

    return encoded_basket, detailed_item
