from django.urls import path
from users.views.auth_views import AnonymousUserRegisterAPIView, AnonymousUserUpgradeAPIView

urlpatterns = [
    path('anonymous/register/', AnonymousUserRegisterAPIView.as_view(), name='anonymous_register'),
    path('anonymous/upgrade/', AnonymousUserUpgradeAPIView.as_view(), name='anonymous_upgrade'),
]
