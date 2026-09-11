from django.urls import path
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import LogoutView, MeView, RegisterView, VerifyEmailView


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/verify-email", VerifyEmailView.as_view()),
    # TokenObtainPairView uses Django's own authenticate(), which already
    # refuses is_active=False users — an unverified account simply cannot
    # log in, no extra check needed here.
    path("auth/login", ThrottledTokenObtainPairView.as_view()),
    path("auth/refresh", TokenRefreshView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
]
