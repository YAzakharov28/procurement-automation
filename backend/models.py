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


class Category(models.Model):
    name = models.CharField(max_length=50)
    shops = models.ManyToManyField(Shop, related_name="categories")


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=50)


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="product_infos",
    )
    model = models.CharField(max_length=50)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)


class Parameter(models.Model):
    name = models.CharField(max_length=50)


class ProductParameter(models.Model):
    parameter = models.ForeignKey(
        Parameter,
        on_delete=models.CASCADE,
        related_name="product_parameters",
    )
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        related_name="product_parameters",
    )
    value = models.CharField(max_length=50)
