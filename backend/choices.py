from django.db.models import TextChoices


class UserRoleChoices(TextChoices):
    BUYER = "buyer", "Покупатель"
    SHOP = "shop", "Магазин"


class OrderStatusChoices(TextChoices):
    CREATED = "created", "Заказ оформлен"
    CONFIRMED = "confirmed", "Подтвержден"
    PROCESSING = "processing", "Заказ собирается"
    SHIPPED = "shipped", "Передан в доставку"
    DELIVERED = "delivered", "Получен"
    CANCELLED = "cancelled", "Отменен"


class ContactTypeChoices(TextChoices):
    TELEPHONE = "telephone", "Телефон"
    ADDRESS = "address", "Адрес"
