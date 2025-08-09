from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from utils.api_responses import ApiResponse
from datetime import timedelta
from django.utils import timezone
from utils.unique_merchant_oid import generate_unique_merchant_oid
from utils.ip_whitelist import ip_whitelist
from validations.payment_validate import validate_request_data
from utils.fetch_queries import get_merchant_credentials
from utils.http_utils import send_payment_request, handle_payment_response, user_basket_encode
from utils.api_responses import custom_exception_handler
from django.http import Http404
from utils.send_email import send_payment_confirmed_task, send_accountant_information_task
from pagination.custom_pagination import CustomPagination
from serializers.payment_serializers import PaymentPlanSerializer
from paytr.models import Payment, PaymentPlan
import base64
import hashlib
import hmac

# List of allowed IP addresses for PayTR notifications
ALLOWED_IPS = ['185.187.184.84', '212.252.97.250', '213.74.97.150']

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
@authentication_classes([])
@ip_whitelist(ALLOWED_IPS)
def paytr_notification(request):
    # Please visit https://dev.paytr.com/iframe-api/iframe-api-2-adim for more information

    post = request.POST
    merchant_id, merchant_key, merchant_salt = get_merchant_credentials()

    ''' 
    Verify PayTR hash to confirm the request's authenticity and prevent financial loss.
    Return an error if the hashes do not match.
    '''

    hash_str = post['merchant_oid'] + merchant_salt + post['status'] + post['total_amount']
    hash = base64.b64encode(hmac.new(merchant_key.encode(), hash_str.encode(), hashlib.sha256).digest()).decode()

    if hash != post['hash']:
        return HttpResponse(str('PAYTR notification failed: bad hash'))

    try:
        payment = Payment.objects.get(merchant_oid=post['merchant_oid'])
    except Payment.DoesNotExist:
        return HttpResponse(str('PAYTR notification failed: payment not found'))
    
    # This is done to prevent processing an already processed payment. It has been mentioned in the documentation that PayTR could send multiple notifications for the same payment.
    if payment.status == 'successful' or payment.status == 'denied':
        return HttpResponse(str('OK'))

    if post['status'] == 'success':  # Payment is confirmed
        # Extend the user's license end date by the number of days in the payment plan
        payment.subscription_end_date_before_payment = payment.user.subscription_end_date
        if payment.user.subscription_end_date and payment.user.subscription_end_date > timezone.localtime(): # User's license has not expired
            payment.user.subscription_end_date += timedelta(days=payment.payment_plan.days)
        else:
            payment.user.subscription_end_date = timezone.localtime() + timedelta(days=payment.payment_plan.days) # User's license has expired
        payment.status = 'successful'
        payment.user.save()
        payment.subscription_end_date_after_payment = payment.user.subscription_end_date
        payment.save()
        send_payment_confirmed_task(payment.user.id, payment.id)
        send_accountant_information_task(payment.user.id, payment.id)
    else:  # Payment is not confirmed
        payment.status = 'denied'
        payment.save()

    # Notify PayTR that the request has been received and processed
    return HttpResponse(str('OK'))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def paytr_payment_request(request):
    # Please visit https://dev.paytr.com/iframe-api/iframe-api-1-adim for more information
    try:
        user_ip, payment_amount, user_address, payment_plan = validate_request_data(request)
        merchant_id, merchant_key, merchant_salt = get_merchant_credentials()
        payment_params = prepare_payment_params(request, user_ip, payment_amount, user_address, payment_plan, merchant_id, merchant_key, merchant_salt)
        response = send_payment_request(payment_params)
        payment_response = handle_payment_response(request.user, response, payment_params)
    except ValidationError as e:
        error_message = str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)
        return ApiResponse.BadRequest(error_message)
    except Http404 as e:
        return ApiResponse.NotFound("Ödeme planı bulunamadı.")
    except Exception as e:
        print(e)
        return ApiResponse.InternalServerError("Beklenmeyen bir hata oluştu.")
    return ApiResponse.Success(message=payment_response)

def prepare_payment_params(request, user_ip, payment_amount, user_address, payment_plan, merchant_id, merchant_key, merchant_salt):
    if not request.user.email:
        raise ValidationError("Kullanıcı e-postası bulunamadı. Lütfen e-posta adresinizi ayarlayın.")
    if not request.user.phone_number:
        raise ValidationError("Kullanıcı telefon numarası bulunamadı. Lütfen telefon numaranızı ayarlayın.")
    if not request.user.name:
        raise ValidationError("Kullanıcı isim bilgisi bulunamadı. Lütfen isminizi ayarlayın.")

    email = request.user.email
    user_phone = request.user.phone_number
    user_name = request.user.name
    currency = 'TL'
    no_installment = '1'  # 1 for cash payment, 0 for installment. (Decided by the accounting department)
    max_installment = '0'  # Maximum number of installments. 0 is for maximum installments
    timeout_limit = '30'  # Timeout limit for payment. 30 minutes
    encoded_basket, detailed_item = user_basket_encode(payment_plan)
    merchant_oid = generate_unique_merchant_oid()
    merchant_ok_url = 'https://api.sinavsorularimerkezi.com/api/v1/paytr/static/success/' # Customer will be redirected to this page after successful payment
    merchant_fail_url = 'https://api.sinavsorularimerkezi.com/api/v1/paytr/static/fail/' # Customer will be redirected to this page after failed payment
    debug_on = '1' # 1 for debugging, 0 for production
    test_mode = '1' # 1 for testing, 0 for production

    hash_str = f"{merchant_id}{user_ip}{merchant_oid}{email}{payment_amount}{encoded_basket.decode()}{no_installment}{max_installment}{currency}{test_mode}"
    paytr_token = base64.b64encode(hmac.new(merchant_key.encode(), hash_str.encode() + merchant_salt.encode(), hashlib.sha256).digest()).decode('utf-8')

    return {
        'merchant_id': merchant_id,
        'user_ip': user_ip,
        'merchant_oid': merchant_oid,
        'email': email,
        'payment_amount': payment_amount,
        'paytr_token': paytr_token,
        'user_basket': encoded_basket,
        'debug_on': debug_on,
        'no_installment': no_installment,
        'max_installment': max_installment,
        'user_name': user_name,
        'user_address': user_address,
        'user_phone': user_phone,
        'merchant_ok_url': merchant_ok_url,
        'merchant_fail_url': merchant_fail_url,
        'timeout_limit': timeout_limit,
        'currency': currency,
        'test_mode': test_mode,
        'payment_plan': payment_plan,
        'detailed_item': detailed_item
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_user_payments(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at').values()
    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(payments, request)
    return paginator.get_paginated_response(result_page)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_payment_plans(request):
    payment_plans = PaymentPlan.objects.filter(is_active=True)
    serializer = PaymentPlanSerializer(payment_plans, many=True)
    return ApiResponse.Success(data=serializer.data)
