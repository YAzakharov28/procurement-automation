from celery.result import AsyncResult
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import Category, Shop
from backend.permissions import IsCategoryOwnerOrAdminOrReadOnly, IsShopOwnerOrAdminOrReadOnly
from backend.serializers import CategorySerializer, ShopSerializer
from backend.tasks import update_shop_positions_task


class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]
    permission_classes = [IsShopOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer: ShopSerializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Shop.objects.none()
        return Shop.objects.all()

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


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]
    permission_classes = [IsCategoryOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer: CategorySerializer):
        category = serializer.save()
        shop = Shop.objects.get(user=self.request.user)
        category.shops.add(shop)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Category.objects.none()
        return Category.objects.all()
