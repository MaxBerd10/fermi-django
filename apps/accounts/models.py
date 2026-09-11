from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model set up from day one (Django makes this painful to
    retrofit later). is_active gates login exactly like the fix shipped on
    the old Yii2 site today: a fresh registration is created inactive, and
    only actionEmailVerify-equivalent flips it to active — never issued
    tokens immediately.
    """

    email = models.EmailField(unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]
