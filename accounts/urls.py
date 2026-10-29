from django.contrib.auth import views as auth
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
    path("login/", auth.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth.PasswordResetView.as_view(template_name="registration/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path("password/change/", auth.PasswordChangeView.as_view(template_name="registration/password_change.html", success_url=reverse_lazy("password_change_done")), name="password_change"),
    path("password/changed/", auth.PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
