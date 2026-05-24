import django_filters
from backend.models import Product


class ProductFilter(django_filters.FilterSet):
    shop = django_filters.NumberFilter(
        field_name="product_infos__shop",
        lookup_expr="exact",
    )
    shop_id = django_filters.NumberFilter(
        field_name="product_infos__shop__id",
        lookup_expr="exact",
    )
    category = django_filters.NumberFilter(
        field_name="category",
        lookup_expr="exact",
    )
    category_id = django_filters.NumberFilter(
        field_name="category__id",
        lookup_expr="exact",
    )

    class Meta:
        model = Product
        fields = ["shop", "shop_id"]
