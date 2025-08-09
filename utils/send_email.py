
from django.core.mail import send_mail
from django.template.loader import render_to_string
from celery import shared_task
from users.models import CustomUser
from paytr.models import Payment
from utils.user_tools import check_user_resend_limit, generate_5_digit_verification_code
import os

@shared_task
def send_email_confirmation_task(user_id, verification_code):
    user = CustomUser.objects.get(id=user_id)

    subject = 'Doğrulama Kodu'
    message = render_to_string('acc_active_email.html', {
        'user': user,
        'code': verification_code,
    })
    from_email = os.environ.get('EMAIL_HOST_USER')
    send_mail(subject, message, from_email, [user.email], html_message=message, fail_silently=False)

@shared_task
def send_password_reset_task(user_id, verification_code):
    user = CustomUser.objects.get(id=user_id)

    subject = 'Şifre Sıfırlama Kodu'
    message = render_to_string('password_reset_email.html', {
        'user': user,
        'code': verification_code,
    })
    from_email = os.environ.get('EMAIL_HOST_USER')
    send_mail(subject, message, from_email, [user.email], html_message=message, fail_silently=False)

@shared_task
def send_payment_confirmed_task(user_id, payment_id):
    user = CustomUser.objects.get(id=user_id)
    payment = Payment.objects.get(id=payment_id)

    subject = 'Sınav Soruları Merkezi Ödeme Onaylandı'
    message = render_to_string('payment_confirm_email.html', {
        'user': user,
        'payment': payment,
    })
    from_email = os.environ.get('EMAIL_HOST_USER')
    send_mail(subject, message, from_email, [user.email], html_message=message, fail_silently=False)

@shared_task
def send_accountant_information_task(user_id, payment_id):
    user = CustomUser.objects.get(id=user_id)
    payment = Payment.objects.get(id=payment_id)

    accountant_email = os.environ.get('ACCOUNTANT_EMAIL')
    if accountant_email:
        subject = 'Sınav Soruları Merkezi Yeni Ödeme'
        payment_count = Payment.objects.filter(user=user, status="successful").count()
        message = render_to_string('accountant_information_email.html', {
            'user': user,
            'payment': payment,
            'payment_count': payment_count,
        })
        from_email = os.environ.get('EMAIL_HOST_USER')
        send_mail(subject, message, from_email, [accountant_email], html_message=message, fail_silently=False)

def check_resend_limit_and_send_confirmation(user):
    success, message = check_user_resend_limit(user, check_verified=True)
    if not success:
        return False, message
    verification_code = generate_5_digit_verification_code(user)

    # Call the Celery task to send the email
    send_email_confirmation_task.delay(user.id, verification_code)
    return True, 'Doğrulama kodu başarıyla gönderildi. Lütfen e-posta adresinizi kontrol edin.'

def check_resend_limit_and_send_password_reset(user):
    success, message = check_user_resend_limit(user, check_verified=False)
    if not success:
        return False, message
    verification_code = generate_5_digit_verification_code(user)

    # Call the Celery task to send the email
    send_password_reset_task.delay(user.id, verification_code)
    return True, 'Şifre sıfırlama kodu başarıyla gönderildi. Lütfen e-posta adresinizi kontrol edin.'
