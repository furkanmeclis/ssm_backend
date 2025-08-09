from functools import wraps
from utils.api_responses import ApiResponse

def ip_whitelist(allowed_ips):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            ip = get_client_ip(request)
            if ip not in allowed_ips:
                return ApiResponse.Forbidden(message="IP address not allowed. This endpoint is restricted to certain IPs.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        # X-Forwarded-For header can contain multiple IPs, take the first one
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
