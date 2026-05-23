from django.urls import path

from accounts.views import LoginView, RegisterView, ConfirmEmailView

urlpatterns = [
    path("registry/", RegisterView.as_view()),
    path("confirm-email/", ConfirmEmailView.as_view()),
    path("login/", LoginView.as_view()),
]
