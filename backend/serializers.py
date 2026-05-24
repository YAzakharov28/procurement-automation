from rest_framework import serializers

from backend.models import Shop, Category


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
