from django.db import models

# Create your models here.
from backend.choices import UserRoleChoices


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.BUYER,
    )


