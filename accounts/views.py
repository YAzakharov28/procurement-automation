from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from accounts.models import ConfirmEmailToken
from accounts.serializers import (
    ConfirmEmailSerializer,
    LoginSerializer,
    UserRegistrySerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Пользователь создан. Проверьте email для подтверждения.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConfirmEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = ConfirmEmailToken.objects.filter(
            user__email=serializer.data["email"],
            key=serializer.data["key"],
        ).first()
        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()
            return Response(
                data={"message": f"Почта {serializer.data['email']} подтверждена"}
            )
        return Response(data={"message": "Неправильно указан токен или email"})


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.data["email"],
            password=serializer.data["password"],
        )

        if user is not None:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return Response(data={"token": token.key})
        return Response(data={"message": "Неправильно указан email или пароль"})
