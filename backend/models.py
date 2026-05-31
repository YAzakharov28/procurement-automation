from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class OrderStatusChoices(models.TextChoices):
    BASKET = "basket", "Корзина"
    CREATED = "created", "Заказ оформлен"
    CONFIRMED = "confirmed", "Подтвержден"
    PROCESSING = "processing", "Заказ собирается"
    SHIPPED = "shipped", "Передан в доставку"
    DELIVERED = "delivered", "Получен"
    CANCELLED = "cancelled", "Отменен"


class Shop(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_accepting_orders = models.BooleanField(default=True)


class Category(models.Model):
    name = models.CharField(max_length=50)
    shops = models.ManyToManyField(Shop, related_name="categories")


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=150)


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
    external_id = models.PositiveIntegerField(db_index=True)
    model = models.CharField(max_length=50)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "external_id"],
                name="unique_shop_external_id",
            )
        ]


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


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=50,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.BASKET,
    )
    contact = models.ForeignKey(
        "Contact",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="orders",
    )
    dt = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    product_info = models.ForeignKey(
        ProductInfo,
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()


class Contact(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contacts",
        blank=True,
        on_delete=models.CASCADE,
    )
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=15, blank=True)
    structure = models.CharField(max_length=15, blank=True)
    building = models.CharField(max_length=15, blank=True)
    apartment = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=20)
