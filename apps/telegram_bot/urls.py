from django.urls import path

from .views import TelegramWebhookView
from .webapp import MeView, RegisterView, SubmissionsView, SubmitView, UploadView

urlpatterns = [
    path("telegram/webhook/", TelegramWebhookView.as_view()),
    # the Mini App (frontend/src/tg): see webapp.py
    path("telegram/app/me", MeView.as_view()),
    path("telegram/app/register", RegisterView.as_view()),
    path("telegram/app/submissions", SubmissionsView.as_view()),
    path("telegram/app/upload", UploadView.as_view()),
    path("telegram/app/submit", SubmitView.as_view()),
]
