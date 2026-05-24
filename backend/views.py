from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import Shop
from backend.permissions import IsShopOwnerOrAdminOrReadOnly
from backend.serializers import ShopSerializer
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
        update_shop_positions_task.delay(shop.id)
        return Response({"message": "Импорт запущен"}, status=status.HTTP_202_ACCEPTED)
