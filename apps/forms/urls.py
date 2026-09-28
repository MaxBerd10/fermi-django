from django.urls import path

from .views import ContactFormView, ContestFormView, QabulFormView, VirtualReceptionFormView

urlpatterns = [
    path("forms/contact", ContactFormView.as_view()),
    path("forms/qabul", QabulFormView.as_view()),
    path("forms/virtual-reception", VirtualReceptionFormView.as_view()),
    path("forms/contest", ContestFormView.as_view()),
]
