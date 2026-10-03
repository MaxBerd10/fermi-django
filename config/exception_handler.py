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
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = ValidationError(exc.message_dict)
        else:
            exc = ValidationError(list(exc.messages))
    return drf_exception_handler(exc, context)
