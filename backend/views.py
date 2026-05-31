from celery.result import AsyncResult
from django.db import transaction
from django.db.models import Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from backend.filters import ProductFilter
from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    OrderStatusChoices,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)
from backend.permissions import IsShopOwnerOrAdminOrReadOnly
from backend.serializers import (
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CategorySerializer,
    ContactSerializer,
    OrderConfirmSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
    ShopSerializer,
)
from backend.signals import order_confirmed
from backend.tasks import update_shop_positions_task


class ShopViewSet(ModelViewSet):
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]
    permission_classes = [IsShopOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer: ShopSerializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Shop.objects.none()
        if user.is_superuser:
            return Shop.objects.all()
        return Shop.objects.filter(
            Q(user=user) | Q(is_accepting_orders=True)
        ).distinct()

    @action(methods=["patch"], detail=True)
    def positions(self, request: Request, pk: int | None = None):
        shop = self.get_object()
        self.check_object_permissions(request, shop)
        task = update_shop_positions_task.delay(shop.id)
        return Response(
            {"task_id": task.id, "status": "started"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        methods=["get"],
        detail=False,
        url_path=r"positions/(?P<task_id>[^/.]+)",
    )
    def task_status(self, request, task_id=None):
        result = AsyncResult(task_id)
        data = {
            "task_id": task_id,
            "state": result.state,
        }

        if result.state == "SUCCESS":
            data["result"] = result.result
            return Response(data, status=status.HTTP_200_OK)

        if result.state == "FAILURE":
            error = result.result
            data["error"] = str(error)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def orders(self, request):
        orders = (
            Order.objects.filter(
                order_items__product_info__shop__user_id=request.user.id
            )
            .exclude(status="basket")
            .prefetch_related(
                "order_items__product_info__product__category",
                "order_items__product_info__product_parameters__parameter",
            )
            .select_related("contact", "user")
            .distinct()
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name"]


class ProductViewSet(ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        return (
            Product.objects.filter(product_infos__shop__is_accepting_orders=True)
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "product_infos",
                    queryset=(
                        ProductInfo.objects.filter(shop__is_accepting_orders=True)
                        .select_related("shop")
                        .prefetch_related(
                            Prefetch(
                                "product_parameters",
                                queryset=ProductParameter.objects.select_related(
                                    "parameter"
                                ),
                            )
                        )
                    ),
                    to_attr="active_product_infos",
                )
            )
            .distinct()
        )


class CartViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_order(self):
        order, _ = Order.objects.get_or_create(
            user=self.request.user,
            status=OrderStatusChoices.BASKET,
        )
        return order

    def get_order_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
            status=OrderStatusChoices.BASKET,
        ).prefetch_related(
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.select_related("product_info"),
            )
        )

    def list(self, request):
        order = self.get_order_queryset().first() or self.get_order()
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request):
        order = self.get_order()
        order.order_items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="items")
    def items(self, request):
        serializer = CartItemCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(
            OrderItemSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["patch"], url_path="items/(?P<pk>[^/.]+)")
    def update_item(self, request, pk=None):
        order = self.get_order()
        item = OrderItem.objects.get(pk=pk, order=order)
        serializer = CartItemUpdateSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderItemSerializer(item).data)

    @action(detail=False, methods=["delete"], url_path="items/(?P<pk>[^/.]+)")
    def delete_item(self, request, pk=None):
        order = self.get_order()
        item = OrderItem.objects.get(pk=pk, order=order)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm(self, request):
        serializer = OrderConfirmSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        cart = serializer.validated_data["cart_id"]
        contact = serializer.validated_data["contact_id"]

        with transaction.atomic():
            cart.contact = contact
            cart.status = OrderStatusChoices.CREATED
            cart.save(update_fields=["contact", "status"])

            transaction.on_commit(
                lambda: order_confirmed.send(
                    sender=Order,
                    order=cart,
                )
            )

        return Response(
            {
                "order_id": cart.id,
                "status": cart.status,
                "contact_id": contact.id,
            },
            status=status.HTTP_200_OK,
        )


class ContactViewSet(ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserOrderViewSet(ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
        ).exclude(
            status=OrderStatusChoices.BASKET
        ).prefetch_related(
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.select_related("product_info"),
            )
        )
