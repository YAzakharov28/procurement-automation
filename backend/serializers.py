from decimal import Decimal

from rest_framework import serializers

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    OrderStatusChoices,
    Product,
    ProductInfo,
    Shop,
)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ("id", "name", "url", "is_accepting_orders")
        read_only_fields = ("id",)
        extra_kwargs = {
            "url": {"write_only": True},
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")
        read_only_fields = ("id",)


class ProductInfoSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    class Meta:
        model = ProductInfo
        fields = (
            "shop",
            "model",
            "quantity",
            "price",
            "price_rrc",
            "parameters",
        )

    def get_parameters(self, value: ProductInfo):
        return {
            product_parameter.parameter.name: product_parameter.value
            for product_parameter in value.product_parameters.select_related(
                "parameter"
            ).all()
        }


class ProductSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(source="active_product_infos", many=True)

    class Meta:
        model = Product
        fields = ("id", "name", "category", "product_info")
        read_only_fields = ("id",)


class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source="product_info.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ("id", "product_info", "quantity", "price")
        read_only_fields = ("id", "price")


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "dt", "status", "order_items", "total_amount")
        read_only_fields = fields

    def get_total_amount(self, obj):
        total = Decimal("0.00")
        for item in obj.order_items.all():
            total += item.quantity * item.product_info.price
        return total


class CartItemCreateSerializer(serializers.Serializer):
    product_info = serializers.PrimaryKeyRelatedField(
        queryset=ProductInfo.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        user = self.context["request"].user
        order, _ = Order.objects.get_or_create(
            user=user,
            status=OrderStatusChoices.BASKET,
        )

        product_info = validated_data["product_info"]
        quantity = validated_data["quantity"]

        item, created = OrderItem.objects.get_or_create(
            order=order,
            product_info=product_info,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return item


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("quantity",)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
            "phone",
        )
        read_only_fields = ("id",)


class OrderConfirmSerializer(serializers.Serializer):
    cart_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.filter(status=OrderStatusChoices.BASKET)
    )
    contact_id = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())

    def validate(self, attrs):
        request = self.context["request"]
        cart = attrs["cart_id"]
        contact = attrs["contact_id"]

        if cart.user != request.user:
            raise serializers.ValidationError(
                {"cart_id": "Корзина не принадлежит пользователю."}
            )

        if contact.user != request.user:
            raise serializers.ValidationError(
                {"contact_id": "Контакт не принадлежит пользователю."}
            )

        if not cart.order_items.exists():
            raise serializers.ValidationError({"cart_id": "Корзина пустая."})

        return attrs
