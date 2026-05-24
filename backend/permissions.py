from rest_framework import permissions


class BaseAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return getattr(request.user, "role", None) == "shop"


class IsShopOwnerOrAdminOrReadOnly(BaseAPIPermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return (
                getattr(request.user, "role", None) == "shop" and obj.user == request.user
        )


class IsCategoryOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if getattr(request.user, "role", None) != "shop":
            return False
        return obj.shops.filter(user=request.user).exists()
