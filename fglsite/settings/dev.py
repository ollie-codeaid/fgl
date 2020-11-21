from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = [
    "127.0.0.1",
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "s$pnz4r%$4v@%h9@!hbky$h^zwed7z(3ar&0r@o15ia-+y812x"


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
# EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
# EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_POST = 587
EMAIL_USE_TLS = True


try:
    from .local import *
except ImportError:
    pass
