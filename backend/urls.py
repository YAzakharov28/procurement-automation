from rest_framework.routers import DefaultRouter

from backend import views

router = DefaultRouter()
router.register("shops", views.ShopViewSet)
router.register("categories", views.CategoryViewSet)
router.register("products", views.ProductViewSet)

urlpatterns = router.urls
