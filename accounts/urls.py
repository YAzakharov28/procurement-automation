from django.urls import path

from accounts import views

urlpatterns = [
    path("registry/", views.RegisterView.as_view()),
    path("confirm/", views.ConfirmEmailView.as_view()),
    path("login/", views.LoginView.as_view()),
]
