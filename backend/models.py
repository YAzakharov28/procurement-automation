from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.choices import UserRoleChoices


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.BUYER,
    )


class Shop(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)


