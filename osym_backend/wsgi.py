"""
WSGI config for osym_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from .custom_wsgi import application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osym_backend.settings')
