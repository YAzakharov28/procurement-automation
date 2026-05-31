from collections import defaultdict
from decimal import Decimal

import requests
import yaml
from celery import shared_task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import URLValidator
from django.db import transaction
from django.template.loader import render_to_string

from backend.models import (
    Category,
    Order,
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


@shared_task
def send_order_confirmed_emails_task(order_id):
    order = (
        Order.objects.select_related("user", "contact")
        .prefetch_related(
            "order_items__product_info__shop__user",
            "order_items__product_info",
        )
        .get(id=order_id)
    )

    items = list(order.order_items.all())

    total_amount = Decimal("0.00")
    for item in items:
        item.line_total = item.quantity * item.product_info.price
        total_amount += item.line_total

    user_subject = f"Заказ #{order.id} оформлен"
    user_context = {"order": order, "total_amount": total_amount}
    user_html_content = render_to_string(
        "emails/order_confirmed_user.html",
        context=user_context,
    )
    user_text_content = render_to_string(
        "emails/order_confirmed_user.txt",
        context=user_context,
    )

    user_msg = EmailMultiAlternatives(
        subject=user_subject,
        body=user_text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[order.user.email],
    )
    user_msg.attach_alternative(user_html_content, "text/html")
    user_msg.send()

    shop_groups = defaultdict(list)
    for item in items:
        shop_groups[item.product_info.shop].append(item)

    for shop, shop_items in shop_groups.items():
        shop_total = Decimal("0.00")
        for item in shop_items:
            item.line_total = item.quantity * item.product_info.price
            shop_total += item.line_total

        shop_subject = f"Новый заказ #{order.id}"
        shop_context = {
            "order": order,
            "shop": shop,
            "items": shop_items,
            "shop_total": shop_total,
        }
        shop_html_content = render_to_string(
            "emails/order_confirmed_shop.html",
            context=shop_context,
        )
        shop_text_content = render_to_string(
            "emails/order_confirmed_shop.txt",
            context=shop_context,
        )

        shop_msg = EmailMultiAlternatives(
            subject=shop_subject,
            body=shop_text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[shop.user.email],
        )
        shop_msg.attach_alternative(shop_html_content, "text/html")
        shop_msg.send()
