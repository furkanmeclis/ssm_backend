from django.urls import path
from users.views.auth_views import UserRegisterAPIView, ResendVerificationCodeAPIView, VerifyVerificationCodeAPIView, LoginAPIView, NewAccessTokenAPIView, LogoutAPIView, ChangePasswordAPIView, PasswordResetRequestAPIView, PasswordResetAPIView
from users.views.profile_views import UserProfileView, DeleteAccountView

urlpatterns = [
    path('register/', UserRegisterAPIView.as_view(), name='register'),
    path('verification-code/resend/', ResendVerificationCodeAPIView.as_view(), name='resend_verification_code'),
    path('verification-code/verify/', VerifyVerificationCodeAPIView.as_view(), name='verify_verification_code'),
    path('password/reset/request/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('password/reset/', PasswordResetAPIView.as_view(), name='password-reset'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('refresh/token/', NewAccessTokenAPIView.as_view(), name='new_access_token'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('password/change/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('account/', DeleteAccountView.as_view(), name='delete_account'),
]
