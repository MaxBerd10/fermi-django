from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
    VerifyEmailView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/verify-email", VerifyEmailView.as_view()),
    path("auth/password-reset-request", PasswordResetRequestView.as_view()),
    # Matches the frontend's own call (api/auth.ts::resetPassword posts to
    # "auth/password-reset", not "-confirm") -- fixed here rather than
    # there since the frontend is the real, unmodified source of truth for
    # what the site actually calls.
    path("auth/password-reset", PasswordResetConfirmView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
]
