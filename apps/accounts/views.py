from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer

User = get_user_model()


def _serialize_user(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        # The frontend's admin guard (AdminAuthContext) only ever checks
        # role === "admin" -- is_staff is Django's own "can reach an admin
        # surface" flag, so it's the natural source rather than a new field.
        "role": "admin" if user.is_staff else "user",
    }


def _issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "accessToken": str(refresh.access_token),
        "refreshToken": str(refresh),
        "user": _serialize_user(user),
    }


def _decode_uid_token(uid: str, token: str):
    """
    Shared by email verification and password reset — both are "prove you
    control this uid's inbox via a signed, time-limited token" flows using
    Django's own token machinery, just pointed at different follow-up
    actions. Returns the User on success, None on any failure (bad uid,
    unknown user, expired/forged/already-used token).
    """
    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user


class RegisterView(APIView):
    """
    Creates the account inactive and emails a verification link — the account
    only starts working, and tokens are only issued, once VerifyEmailView
    below succeeds. Same contract as the fix shipped on the old Yii2 site
    today, closing the same "unlimited unverified accounts" hole from day one
    here instead of needing to be retrofitted later.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_link = f"{settings.FRONTEND_URL}/email-tasdiqlash/{uid}/{token}"

        send_mail(
            subject="Hisobingizni tasdiqlang — FerMI",
            message=f"Hisobingizni faollashtirish uchun havolani bosing:\n\n{verify_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        return Response({"verificationRequired": True}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        user = _decode_uid_token(request.data.get("uid"), request.data.get("token"))
        if user is None:
            return Response({"detail": "Havola eskirgan yoki noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response(_issue_tokens(user))


class PasswordResetRequestView(APIView):
    """
    Always returns the same generic response whether or not the email is
    registered — confirming/denying an account's existence to an anonymous
    caller is its own (minor but real) privacy leak, so this endpoint never
    does, the same way the old site's equivalent form doesn't either.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        email = request.data.get("email", "")
        user = User.objects.filter(email=email, is_active=True).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.FRONTEND_URL}/parolni-tiklash/{uid}/{token}"
            send_mail(
                subject="Parolni tiklash — FerMI",
                message=f"Parolingizni tiklash uchun havolani bosing:\n\n{reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        return Response({"sent": True})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        user = _decode_uid_token(request.data.get("uid"), request.data.get("token"))
        if user is None:
            return Response({"detail": "Havola eskirgan yoki noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get("password", "")
        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            return Response({"detail": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save(update_fields=["password"])
        return Response(_issue_tokens(user))


class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data["refreshToken"]).blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    """POST /api/v1/auth/login -- replaces SimpleJWT's stock
    TokenObtainPairView so the response actually matches what the frontend
    expects (see api/auth.ts::login / AuthResult): accessToken/refreshToken/
    user, not SimpleJWT's bare access/refresh with no user payload at all."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Login yoki parol noto'g'ri."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(_issue_tokens(user))


class RefreshView(APIView):
    """POST /api/v1/auth/refresh -- same reasoning as LoginView: wraps
    SimpleJWT's own TokenRefreshSerializer (which already handles rotation
    + blacklisting per SIMPLE_JWT's settings) so the response is
    {accessToken, refreshToken}, not SimpleJWT's own {access} / {access,
    refresh}."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data={"refresh": request.data.get("refreshToken")})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Refresh token yaroqsiz."}, status=status.HTTP_401_UNAUTHORIZED)
        data = serializer.validated_data
        return Response({"accessToken": str(data["access"]), "refreshToken": str(data["refresh"])})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_serialize_user(request.user))
