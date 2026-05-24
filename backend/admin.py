from django.contrib import admin

from backend.models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "url")
    list_filter = ("name",)
    search_fields = ("name", "user__email")
