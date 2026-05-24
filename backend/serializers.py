from rest_framework import serializers

from backend.models import (
    Parameter,
    Product,
    ProductParameter,
    Shop,
    Category,
    ProductInfo,
)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ("id", "name", "url")
        read_only_fields = ("id",)
        extra_kwargs = {
            "url": {"write_only": True},
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")
        read_only_fields = ("id",)


class ParameterInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    value = serializers.CharField(max_length=50)


class ProductInfoSerializer(serializers.ModelSerializer):
    parameters = ParameterInputSerializer(many=True, required=False)

    class Meta:
        model = ProductInfo
        fields = (
            "id",
            "shop",
            "external_id",
            "model",
            "quantity",
            "price",
            "price_rrc",
            "parameters",
        )
        read_only_fields = ("id",)
        extra_kwargs = {
            "external_id": {"write_only": True},
        }

    def create(self, validated_data):
        parameters_data = validated_data.pop("parameters", [])
        product_info = super().create(validated_data)

        for param_data in parameters_data:
            parameter, _ = Parameter.objects.get_or_create(name=param_data["name"])
            ProductParameter.objects.create(
                product_info=product_info,
                parameter=parameter,
                value=param_data["value"],
            )

        return product_info


class ProductInfoReadSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    class Meta:
        model = ProductInfo
        fields = (
            "shop",
            "external_id",
            "model",
            "quantity",
            "price",
            "price_rrc",
            "parameters",
        )
        extra_kwargs = {
            "external_id": {"write_only": True},
        }

    def get_parameters(self, obj):
        product_parameters = obj.product_parameters.all()
        return [
            {"name": pp.parameter.name, "value": pp.value} for pp in product_parameters
        ]


class ProductSerializer(serializers.ModelSerializer):
    product_infos = ProductInfoReadSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "product_infos",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        product_infos_data = validated_data.pop("product_infos")
        product = Product.objects.create(**validated_data)

        for product_info_data in product_infos_data:
            info_serializer = ProductInfoSerializer(
                data=product_info_data, context=self.context
            )
            info_serializer.is_valid(raise_exception=True)
            info_serializer.save(product=product)

        return product
