from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from rest_framework import serializers

User = get_user_model()


def _validate_password(password: str):
    try:
        password_validation.validate_password(password)
        return password
    except Exception as password_error:
        error_array = []
        # noinspection PyTypeChecker
        for item in password_error:
            error_array.append(item)
        raise serializers.ValidationError(", ".join(error_array))


class UserRegistrySerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    password = serializers.CharField(min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
        )
        read_only_fields = ("id",)
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_password(self, value: str):
        return _validate_password(value)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.is_active = False
        user.set_password(password)
        user.save()
        return user


class ConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    key = serializers.CharField(max_length=64)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=8)

    def validate_password(self, value):
        return _validate_password(value)
