from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from utils.user_tools import get_client_ip, get_user_info
from rest_framework_simplejwt.exceptions import InvalidToken
from django.conf import settings
import logging

logger = logging.getLogger('django')

class ApiResponse:
    """Utility class for generating standardized API responses."""

    @staticmethod
    def Success(message="İşlem başarılı oldu.", data=None, message_key="system"):
        response = {
            'success': True,
            'message': ApiResponse._format_message(message, message_key),
            'data': data,
            'status_code': status.HTTP_200_OK
        }
        return Response(response, status=status.HTTP_200_OK)

    @staticmethod
    def BadRequest(message="İşlem başarısız oldu.", message_key="system"):
        return Response({
            'success': False,
            'message': ApiResponse._format_message(message, message_key),
            'data': None,
            'status_code': status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def NotFound(message="Bulunamadı.", message_key="system"):
        return Response({
            'success': False,
            'message': ApiResponse._format_message(message, message_key),
            'data': None,
            'status_code': status.HTTP_404_NOT_FOUND
        }, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def UnAuthorized(message="Yetkiniz yok.", message_key="system"):
        return Response({
            'success': False,
            'message': ApiResponse._format_message(message, message_key),
            'data': None,
            'status_code': status.HTTP_401_UNAUTHORIZED
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def InternalServerError(message="Sunucu hatası.", message_key="system"):
        return Response({
            'success': False,
            'message': ApiResponse._format_message(message, message_key),
            'data': None,
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def Forbidden(message="Yasaklandı.", message_key="system"):
        return Response({
            'success': False,
            'message': ApiResponse._format_message(message, message_key),
            'data': None,
            'status_code': status.HTTP_403_FORBIDDEN
        }, status=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def _format_message(message, message_key="system"):
        """Ensure the message is returned as a dictionary with the specified key."""
        if isinstance(message, str):
            return {message_key: [message]}
        return message

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get('request')

    if response is None:
        if isinstance(exc, ObjectDoesNotExist):
            return ApiResponse.NotFound(message=str(exc))

        request_path = getattr(request, 'path', 'unknown')
        request_method = getattr(request, 'method', 'unknown')
        request_time = getattr(request, 'start_time', timezone.localtime()).isoformat()
        client_ip = get_client_ip(request)
        user_info = get_user_info(request)

        log_message = (
            "Unhandled exception: %s | Path: %s | Method: %s | Time: %s | Client IP: %s | User: %s" %
            (exc, request_path, request_method, request_time, client_ip, user_info)
        )

        logger.error(log_message)

        if settings.DEBUG:
            print(log_message)

        return ApiResponse.InternalServerError(message='Bilinmeyen bir hata oluştu.')

    if isinstance(exc, InvalidToken):
        return ApiResponse.UnAuthorized(message="Token geçersiz veya süresi dolmuş.")

    if isinstance(exc, APIException):
        status_code_to_api_response = {
            404: ApiResponse.NotFound,
            403: ApiResponse.Forbidden,
            401: ApiResponse.UnAuthorized,
            400: ApiResponse.BadRequest,
            500: ApiResponse.InternalServerError
        }
        response_data = response.data if hasattr(response, 'data') else {'detail': 'Bilinmeyen bir hata oluştu.'}
        detailed_error = response_data.get('detail', 'Bilinmeyen bir hata oluştu.')

        if settings.DEBUG:
            print(f"APIException: {detailed_error}")

        return status_code_to_api_response.get(response.status_code, ApiResponse.BadRequest)(
            message=detailed_error
        )

    return response
