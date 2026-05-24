from rest_framework.routers import DefaultRouter

from backend.views import ShopViewSet

router = DefaultRouter()
router.register("shops", ShopViewSet)

urlpatterns = router.urls
