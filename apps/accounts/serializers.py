from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        # Mirrors the fix shipped on the old Yii2 site today: create inactive,
        # never issue tokens until the email link is clicked.
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,
        )
