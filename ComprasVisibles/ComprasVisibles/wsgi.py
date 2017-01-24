"""
WSGI config for ComprasVisibles project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ComprasVisibles.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
