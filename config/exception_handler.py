"""DRF exception handler that also turns Django model-validation errors into
400s.

Model.full_clean() / ContentBlock.full_clean() raise
django.core.exceptions.ValidationError, which DRF's default handler does not
know about -- it propagates as an unhandled exception and the client gets an
HTML 500 page. In the admin panel that meant a half-filled form (e.g. a leader
saved without a category, which StaffMember.clean() rejects) failed with an
opaque "Request failed (500)" instead of a readable message under the field.
Mapping them here gives every admin endpoint the same {"field": ["message"]}
400 body the forms already know how to display, without each view having to
wrap its own full_clean() call.
"""
import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# The admin panel is used by non-technical staff in Uzbek; DRF/Django's stock validation messages are English.
# Only the common stock messages are translated -- a message a view wrote itself is left exactly as it is.
_UZ_MESSAGES = {
    "This field is required.": "Bu maydon to'ldirilishi shart.",
    "This field may not be blank.": "Bu maydon bo'sh bo'lmasligi kerak.",
    "This field may not be null.": "Bu maydon to'ldirilishi shart.",
    "Enter a valid URL.": "To'g'ri havola kiriting (https:// bilan boshlansin).",
    "Enter a valid email address.": "To'g'ri elektron pochta manzilini kiriting.",
    "A valid integer is required.": "Butun son kiriting.",
    "A valid number is required.": "Son kiriting.",
    "Not a valid string.": "Matn kiriting.",
    "A user with that username already exists.": "Bunday login allaqachon mavjud.",
    "Authentication credentials were not provided.": "Tizimga qaytadan kiring.",
    "You do not have permission to perform this action.": "Bu amal uchun ruxsat yo'q.",
    "Not found.": "Topilmadi.",
    "This password is too common.": "Bu parol juda oddiy (osongina topiladi). Boshqasini tanlang.",
    "This password is entirely numeric.": "Parol faqat raqamlardan iborat bo'lmasin.",
    "The password is too similar to the username.": "Parol loginga juda o'xshash. Boshqasini tanlang.",
    "The password is too similar to the email address.": "Parol pochtaga juda o'xshash. Boshqasini tanlang.",
}
_UZ_PATTERNS = [
    (re.compile(r"This password is too short\. It must contain at least (\d+) characters?\."), r"Parol juda qisqa: kamida \1 ta belgi bo'lsin."),
    (re.compile(r"Ensure this field has no more than (\d+) characters\."), r"Eng ko'pi bilan \1 ta belgi kiritish mumkin."),
    (re.compile(r"Ensure this field has at least (\d+) characters\."), r"Kamida \1 ta belgi kiriting."),
    (re.compile(r"Invalid pk .* object does not exist\."), "Tanlangan yozuv topilmadi."),
    (re.compile(r".* is not a valid choice\."), "Noto'g'ri tanlov."),
    (re.compile(r"Request was throttled\..*"), "Juda ko'p so'rov yuborildi. Birozdan so'ng qayta urinib ko'ring."),
]

PROTECTED_MESSAGE = (
    "Bu yozuvni o'chirib bo'lmaydi: u saytning boshqa joyida ishlatilmoqda. "
    "Avval o'sha joydan olib tashlang, so'ng qayta urinib ko'ring."
)


def _translate(value):
    if isinstance(value, str):
        if value in _UZ_MESSAGES:
            return _UZ_MESSAGES[value]
        for pattern, replacement in _UZ_PATTERNS:
            if pattern.fullmatch(value):
                return pattern.sub(replacement, value)
        return value
    if isinstance(value, list):
        return [_translate(item) for item in value]
    if isinstance(value, dict):
        return {key: _translate(item) for key, item in value.items()}
    return value


def exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        # Deleting something another record still points at (an image used as a video poster, a document
        # a schedule needs...) used to be a bare 500; it is a normal, explainable 400.
        return Response({"detail": PROTECTED_MESSAGE}, status=400)
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = ValidationError(exc.message_dict)
        else:
            exc = ValidationError(list(exc.messages))
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = _translate(response.data)
    return response
