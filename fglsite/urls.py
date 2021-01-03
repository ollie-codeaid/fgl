from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("fglsite.common.urls")),
    path("bets/", include("fglsite.bets.urls")),
    path("bets/", include("fglsite.gambling.urls")),
    path("admin/", admin.site.urls),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
