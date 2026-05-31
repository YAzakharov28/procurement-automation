from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backend import views

router = DefaultRouter()
router.register(r"shops", views.ShopViewSet, basename="shops")
router.register(r"categories", views.CategoryViewSet, basename="categories")
router.register(r"products", views.ProductViewSet, basename="products")
router.register(r"cart", views.CartViewSet, basename="cart")
router.register(r"contacts", views.ContactViewSet, basename="contacts")
router.register(r"orders", views.UserOrderViewSet, basename="user-orders")

urlpatterns = router.urls
