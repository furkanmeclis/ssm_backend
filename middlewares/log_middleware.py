from django.utils.deprecation import MiddlewareMixin
import datetime
import logging
from django.utils import timezone

logger = logging.getLogger('django')

class LogRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = timezone.localtime()

    def process_response(self, request, response):
        return response

    def process_exception(self, request, exception):
        request_path = request.path
        request_method = request.method
        request_time = getattr(request, 'start_time', timezone.localtime()).isoformat()
        client_ip = self.get_client_ip(request)
        user_info = self.get_user_info(request)

        logger.error(
            "Unhandled exception: %s | Path: %s | Method: %s | Time: %s | Client IP: %s | User: %s",
            exception,
            request_path,
            request_method,
            request_time,
            client_ip,
            user_info
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_user_info(self, request):
        if request.user.is_authenticated:
            user_id = request.user.id
            user_email = request.user.email
            return f"ID: {user_id}, Email: {user_email}"
        return "Anonymous"
