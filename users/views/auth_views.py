from django.contrib.auth import logout as django_logout
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from validations.user_validate import validate_user_verification_code, VerificationError
from utils.send_email import check_resend_limit_and_send_confirmation, check_resend_limit_and_send_password_reset
from utils.api_responses import ApiResponse
from serializers.users_serializers import UserRegistrationSerializer, PasswordChangeSerializer, ResendVerificationCodeSerializer, VerifyCodeSerializer, LoginSerializer, PasswordResetRequestSerializer, PasswordResetSerializer, AnonymousUserRegistrationSerializer, AnonymousUserUpgradeSerializer
from users.models import CustomUser, VerificationCode

class UserRegisterV1_1APIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            success, message = check_resend_limit_and_send_confirmation(user)
            if success:
                user.save()
                return ApiResponse.Success(message="Kayıt başarılı. Giriş yapabilirsiniz.")
            else:
                return ApiResponse.BadRequest(message=message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class UserRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            success, message = check_resend_limit_and_send_confirmation(user)
            if success:
                return ApiResponse.Success(message='Kayıt başarılı. Lütfen e-posta adresinize gönderilen doğrulama bağlantısını kullanarak e-posta adresinizi doğrulayın. Gereksiz ve spam kutularını kontrol etmeyi unutmayın.')
            else:
                return ApiResponse.BadRequest(message=message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class ResendVerificationCodeAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)
            success, message = check_resend_limit_and_send_confirmation(user)
            if success:
                return ApiResponse.Success(message='Doğrulama kodu başarıyla tekrar gönderildi. Lütfen e-posta adresinizi kontrol edin.  Gereksiz ve spam kutularını kontrol etmeyi unutmayın.')
            else:
                return ApiResponse.BadRequest(message=message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class VerifyVerificationCodeAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            try:
                user, verification_code = validate_user_verification_code(code, email)
                user.is_verified = True
                user.save()
                verification_code.delete()
                return ApiResponse.Success(message="E-posta başarıyla doğrulandı. Giriş yapabilirsiniz.")
            except VerificationError as e:
                return ApiResponse.BadRequest(message=e.message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class LoginV1_1APIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            response = ApiResponse.Success(
                message='Giriş başarılı.',
                data={'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
            )

            response.set_cookie(
                key='refresh_token', 
                value=str(refresh), 
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            return response
        else:
            return ApiResponse.BadRequest("E-posta adresi veya şifre hatalı. Lütfen tekrar deneyin.")

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if not user.is_verified:
                success, message = check_resend_limit_and_send_confirmation(user)
                if success:
                    return ApiResponse.Forbidden('E-posta adresinizi doğrulamadınız. Lütfen e-posta adresinize gönderilen doğrulama kodunu kullanarak e-posta adresinizi doğrulayın. Gereksiz ve spam kutularını kontrol etmeyi unutmayın.')
                else:
                    return ApiResponse.BadRequest("E-posta adresinizi doğrulamadınız. Doğrulama kodu gönderme limitine ulaştınız. Lütfen daha sonra tekrar deneyin.")

            refresh = RefreshToken.for_user(user)

            response = ApiResponse.Success(
                message='Giriş başarılı.',
                data={'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
            )

            response.set_cookie(
                key='refresh_token', 
                value=str(refresh), 
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            return response
        else:
            return ApiResponse.BadRequest("E-posta adresi veya şifre hatalı. Lütfen tekrar deneyin.")

class NewAccessTokenAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                # Validate and create a new token
                token_obj = RefreshToken(refresh_token)
                # Generate new access token
                access_token = str(token_obj.access_token)
                # Return new access token
                return ApiResponse.Success(message='Başarıyla yeni bir access token oluşturuldu.', data={'access_token': access_token})
            except Exception as e:
                return ApiResponse.UnAuthorized("Refresh token süresi doldu veya geçersiz.")
        else:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token_scheme, refresh_token = auth_header.split(' ', 1)
                    if token_scheme.lower() != 'bearer':
                        return ApiResponse.BadRequest("Invalid token scheme. Expected 'Bearer'.")
                    token_obj = RefreshToken(refresh_token)
                    access_token = str(token_obj.access_token)
                    return ApiResponse.Success(message='Başarıyla yeni bir access token oluşturuldu.', data={'access_token': access_token})
                except Exception as e:
                    return ApiResponse.UnAuthorized("Refresh token süresi doldu veya geçersiz.")
        
        return ApiResponse.BadRequest("Refresh token gönderilmedi.")

class LogoutAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # Check for refresh token in cookies
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token_obj = RefreshToken(refresh_token)
                token_obj.blacklist()

                django_logout(request)

                response = ApiResponse.Success(message='Başarıyla çıkış yapıldı.')
                response.delete_cookie('refresh_token')
                return response
            except Exception as e:
                # Handle exception (e.g., token is expired, invalid, or error in blacklisting)
                return ApiResponse.UnAuthorized(str(e))
        
        # Check for refresh token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token_scheme, refresh_token = auth_header.split(' ', 1)
                if token_scheme.lower() != 'bearer':
                    return ApiResponse.BadRequest("Geçersiz token düzeni. Beklenen: 'Bearer'.")

                token_obj = RefreshToken(refresh_token)
                token_obj.blacklist()

                django_logout(request)

                response = ApiResponse.Success(message='Başarıyla çıkış yapıldı.')
                return response
            except Exception as e:
                # Handle exception (e.g., token is expired, invalid, or error in blacklisting)
                return ApiResponse.UnAuthorized(str(e))

        return ApiResponse.BadRequest("Refresh token gönderilmedi.")

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']

            user.set_password(new_password)
            user.save()

            # Invalidate all existing tokens
            tokens = OutstandingToken.objects.filter(user_id=user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            # Generate a new refresh token
            refresh = RefreshToken.for_user(user)
            new_access_token = str(refresh.access_token)
            
            # Create response with new access token
            response = ApiResponse.Success(
                message='Password successfully changed.', 
                data={'access_token': new_access_token, 'refresh_token': str(refresh)}
            )
            response.set_cookie(
                key='refresh_token', 
                value=str(refresh), 
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            return response
        else:
            return ApiResponse.BadRequest(serializer.errors)

class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)

            success, message = check_resend_limit_and_send_password_reset(user)
            if success:
                return ApiResponse.Success(message='Şifre sıfırlama kodu başarıyla gönderildi. Lütfen e-posta adresinizi kontrol edin.')
            else:
                return ApiResponse.BadRequest(message=message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class PasswordResetAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']

            try:
                user, verification_code = validate_user_verification_code(code, email)
                user.set_password(new_password)
                user.is_verified = True
                user.save()
                verification_code.delete()
                return ApiResponse.Success(message="Şifreniz başarıyla sıfırlandı. Yeni şifrenizle giriş yapabilirsiniz.")
            except VerificationError as e:
                return ApiResponse.BadRequest(message=e.message)
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class AnonymousUserRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AnonymousUserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            device_id = serializer.validated_data.get('device_id')
            
            try:
                user = CustomUser.objects.get(device_id=device_id)
                
                if not user.is_anonymous_user:
                    return ApiResponse.Forbidden(
                        message="Bu cihaz zaten bir kullanıcıya ait. Lütfen giriş yapın veya yeni bir hesap oluşturun."
                    )
                
                refresh = RefreshToken.for_user(user)
                
                response = ApiResponse.Success(
                    message='Anonim kullanıcı girişi başarılı.',
                    data={'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
                )
                
                response.set_cookie(
                    key='refresh_token', 
                    value=str(refresh), 
                    httponly=True,
                    secure=True,
                    samesite='Strict'
                )
                return response
                
            except CustomUser.DoesNotExist:
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                
                response = ApiResponse.Success(
                    message='Anonim kullanıcı kaydı başarılı.',
                    data={'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
                )
                
                response.set_cookie(
                    key='refresh_token', 
                    value=str(refresh), 
                    httponly=True,
                    secure=True,
                    samesite='Strict'
                )
                return response
        else:
            return ApiResponse.BadRequest(message=serializer.errors)

class AnonymousUserUpgradeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if not user.is_anonymous_user:
            return ApiResponse.BadRequest(message="Bu işlem sadece anonim kullanıcılar içindir.")
            
        serializer = AnonymousUserUpgradeSerializer(data=request.data)
        if serializer.is_valid():
            # Update anonymous user with provided info
            user.email = serializer.validated_data.get('email')
            user.name = serializer.validated_data.get('name')
            user.phone_number = serializer.validated_data.get('phone_number')
            user.set_password(serializer.validated_data.get('password'))
            user.is_anonymous_user = False
            user.is_verified = True
            user.save()
            
            # Blacklist current tokens
            tokens = OutstandingToken.objects.filter(user_id=user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            
            # Generate new tokens
            refresh = RefreshToken.for_user(user)
            
            response = ApiResponse.Success(
                message='Kayıt başarılı.',
                data={'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
            )
            
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            return response
        else:
            return ApiResponse.BadRequest(message=serializer.errors)
