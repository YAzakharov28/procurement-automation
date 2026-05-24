from django.contrib import admin

from backend.models import Category, Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "url")
    list_filter = ("name",)
    search_fields = ("name", "user__email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    list_filter = ("name",)
    search_fields = ("name", "shops__user__email")
