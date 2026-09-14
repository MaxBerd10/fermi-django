from django.urls import path

from .views import ContactFormView, QabulFormView, VirtualReceptionFormView

urlpatterns = [
    path("forms/contact", ContactFormView.as_view()),
    path("forms/qabul", QabulFormView.as_view()),
    path("forms/virtual-reception", VirtualReceptionFormView.as_view()),
]
