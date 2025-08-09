from django.urls import path
from users.views.auth_views import UserRegisterV1_1APIView, LoginV1_1APIView

urlpatterns = [
    path('register/', UserRegisterV1_1APIView.as_view(), name='register'),
    path('login/', LoginV1_1APIView.as_view(), name='login'),
]
