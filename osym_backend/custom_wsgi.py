import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings

class AdminUploadLimiter:
    """
    WSGI middleware to temporarily adjust DATA_UPLOAD_MAX_NUMBER_FIELDS
    for admin panel requests.
    """
    def __init__(self, app):
        self.app = app
        ADMIN_URL = settings.ADMIN_URL
        self.admin_prefixes = [f'/{ADMIN_URL}/', f'/{ADMIN_URL}']

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # Check if the request is for the admin panel
        if any(path.startswith(prefix) for prefix in self.admin_prefixes):
            # Temporarily increase the limit
            original_limit = getattr(settings, 'DATA_UPLOAD_MAX_NUMBER_FIELDS', 1000)
            settings.DATA_UPLOAD_MAX_NUMBER_FIELDS = 30000

            try:
                return self.app(environ, start_response)
            finally:
                # Reset the limit after the request is processed
                settings.DATA_UPLOAD_MAX_NUMBER_FIELDS = original_limit
        else:
            # Use the default limit for non-admin requests
            return self.app(environ, start_response)

# Get the default Django WSGI application
application = get_wsgi_application()

# Wrap the application with the AdminUploadLimiter middleware
application = AdminUploadLimiter(application)
