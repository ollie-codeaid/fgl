from __future__ import absolute_import, unicode_literals

from .base import *

DEBUG = False
ALLOWED_HOSTS = ['olliefgl.pythonanywhere.com', ]

SECRET_KEY = os.environ['SECRET_KEY']
STATIC_ROOT = '/home/olliefgl/fglsite/static/'

EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
# EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_POST = 587
EMAIL_USE_TLS = True

try:
    from .local import *
except ImportError:
    pass
