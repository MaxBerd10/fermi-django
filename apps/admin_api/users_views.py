"""admin/users -- UserListPage.tsx/UserFormPage.tsx / api/adminUsers.ts.

`status` has no direct model equivalent: the form offers Faol(10)/
Nofaol(9)/O'chirilgan(0), but User only has one boolean (`is_active`).
Both 9 and 0 map onto is_active=False on write; on read, only 10/9 are
ever returned (never 0 -- there's no separate "deleted" state, matching
the "accepted but inert" precedent used elsewhere for fields with no
full backing)."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User

from .common import AdminPagination, IsAdminStaff


class AdminUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "status", "role", "createdAt", "password"]

    def get_status(self, obj):
        return 10 if obj.is_active else 9

    def get_role(self, obj):
        return "admin" if obj.is_staff else "user"

    def get_createdAt(self, obj):
        return obj.date_joined.strftime("%Y-%m-%d %H:%M") if obj.date_joined else None

    def _apply_status_and_role(self, instance, data):
        status = data.get("status")
        if status is not None:
            instance.is_active = int(status) == 10
        role = data.get("role")
        if role is not None:
            instance.is_staff = role == "admin"

    @staticmethod
    def _check_password(password, user):
        """The staff-management form used to accept any password ("1", "123456") because set_password() runs
        no validators; these are the same rules Django applies everywhere else (AUTH_PASSWORD_VALIDATORS)."""
        try:
            validate_password(password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

    def create(self, validated_data):
        data = self.context["request"].data
        user = User(username=data.get("username", ""), email=data.get("email", ""))
        self._apply_status_and_role(user, data)
        password = data.get("password")
        if not password:
            raise serializers.ValidationError({"password": ["Parol kiriting."]})
        self._check_password(password, user)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        data = self.context["request"].data
        instance.username = data.get("username", instance.username)
        instance.email = data.get("email", instance.email)
        self._apply_status_and_role(instance, data)
        password = data.get("password")
        if password:
            self._check_password(password, instance)
            instance.set_password(password)
        instance.save()
        return instance


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(email__icontains=search))
        return queryset

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise ValidationError({"detail": "O'zingizni o'chira olmaysiz."})
        instance.delete()
