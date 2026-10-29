from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("programmes/", views.programmes, name="programmes"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.simple_page("core/privacy.html"), name="privacy"),
    path("terms/", views.simple_page("core/terms.html"), name="terms"),
]
