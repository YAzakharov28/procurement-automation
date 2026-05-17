from django.db.models import TextChoices

class UserRoleChoices(TextChoices):
    BUYER = "buyer", 'Покупатель'
    SHOP = 'shop', 'Магазин'