import requests
import yaml
from celery import shared_task
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


@shared_task
def update_shop_positions_task(shop_id: int):
    try:
        shop = Shop.objects.get(id=shop_id)
    except Shop.DoesNotExist as err:
        raise ValueError(f"Магазин с ID={shop_id} не найден") from err

    URL = shop.url
    if not URL:
        raise ValueError("У магазина не указана ссылка")

    validate_url = URLValidator()
    try:
        validate_url(URL)
    except ValidationError as err:
        raise ValueError(f"Ошибка валидации ссылки: {str(err)}") from err

    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as err:
        raise ValueError(f"Ошибка загрузки файла: {err}") from err

    try:
        data = yaml.safe_load(response.content)
    except yaml.YAMLError as err:
        raise ValueError("Некорректный YAML-файл") from err

    if data.get("shop") != shop.name:
        raise ValueError("Неверное имя магазина")

    categories = data.get("categories", [])
    goods = data.get("goods", [])

    with transaction.atomic():
        for category in categories:
            category_object, _ = Category.objects.get_or_create(
                id=category["id"],
                defaults={"name": category["name"]},
            )
            if category_object.name != category["name"]:
                category_object.name = category["name"]
                category_object.save(update_fields=["name"])
            category_object.shops.add(shop)

        ProductInfo.objects.filter(shop=shop).delete()

        created_count = 0

        for item in goods:
            product, _ = Product.objects.get_or_create(
                name=item["name"],
                category_id=item["category"],
            )

            product_info = ProductInfo.objects.create(
                product=product,
                shop=shop,
                external_id=item["id"],
                model=item["model"],
                quantity=item["quantity"],
                price=item["price"],
                price_rrc=item["price_rrc"],
            )

            for name, value in item.get("parameters", {}).items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info=product_info,
                    parameter=parameter_object,
                    value=value,
                )

            created_count += 1

    return {"shop_id": shop_id, "created": created_count}