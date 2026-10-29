from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("admissions/", include("admissions.urls")),
    path("learn/", include("learning.urls")),
    path("academics/", include("academics.urls")),
    path("finance/", include("finance.urls")),
    path("", include("core.urls")),
]
