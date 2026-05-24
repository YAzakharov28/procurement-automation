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
    shop = Shop.objects.get(id=shop_id)
    URL = shop.url
    if not URL:
        return Response(
            {"message": "У магазина не указана ссылка"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    validate_url = URLValidator()
    try:
        validate_url(URL)
    except ValidationError as err:
        return Response(
            data={"message": {str(err)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as err:
        return Response(
            {"message": f"Ошибка загрузки файла: {err}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = yaml.safe_load(response.content)
    except yaml.YAMLError:
        return Response(
            {"message": "Некорректный YAML-файл"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if data["shop"] != shop.name:
        return Response(
            data={"message": "Неверное имя магазина"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        for category in data.get("categories", []):
            category_object, _ = Category.objects.get_or_create(
                id=category["id"],
                defaults={"name": category["name"]},
            )
            if category_object.name != category["name"]:
                category_object.name = category["name"]
                category_object.save()
            category_object.shops.add(shop)

        ProductInfo.objects.filter(shop=shop).delete()

        for item in data.get("goods", []):
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
