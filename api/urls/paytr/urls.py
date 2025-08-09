from django.urls import path
from paytr.views.paytr_views import paytr_notification, paytr_payment_request, fetch_user_payments, fetch_payment_plans
from paytr.views.static_views import paytr_success_view, paytr_failed_view

urlpatterns = [
    path('paytr/notification/', paytr_notification, name='paytr_notification'),
    path('paytr/payment/', paytr_payment_request, name='paytr_payment'),
    path('paytr/payments/', fetch_user_payments, name='paytr_payments'),
    path('paytr/payment_plans/', fetch_payment_plans, name='paytr_payment_plans'),
    path('paytr/static/success/', paytr_success_view, name='paytr_success'),
    path('paytr/static/failed/', paytr_failed_view, name='paytr_failed'),
]
