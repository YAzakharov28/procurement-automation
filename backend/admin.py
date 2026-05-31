from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    OrderStatusChoices,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'is_accepting_orders', 'url', 'products_count')
    list_display_links = ('id', 'name')
    list_filter = ('is_accepting_orders', 'user')
    search_fields = ('name', 'user__email')
    list_editable = ('is_accepting_orders',)
    readonly_fields = ('products_count',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'url', 'user')
        }),
        ('Статус', {
            'fields': ('is_accepting_orders',)
        }),
        ('Статистика', {
            'fields': ('products_count',),
            'classes': ('collapse',)
        }),
    )

    def products_count(self, obj):
        count = obj.product_infos.count()
        url = reverse('admin:backend_productinfo_changelist') + f'?shop__id={obj.id}'
        return format_html('<a href="{}">{} товаров</a>', url, count)

    products_count.short_description = 'Количество товаров'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('product_infos')
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'products_count', 'shops_count')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    filter_horizontal = ('shops',)
    readonly_fields = ('products_count', 'shops_count')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'shops')
        }),
        ('Статистика', {
            'fields': ('products_count', 'shops_count'),
            'classes': ('collapse',)
        }),
    )

    def products_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:backend_product_changelist') + f'?category__id={obj.id}'
        return format_html('<a href="{}">{} товаров</a>', url, count)

    products_count.short_description = 'Количество товаров'

    def shops_count(self, obj):
        return obj.shops.count()

    shops_count.short_description = 'Количество магазинов'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('products'),
            shops_count=Count('shops')
        )


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1
    autocomplete_fields = ('parameter',)
    fields = ('parameter', 'value')
    readonly_fields = ('parameter_id',)


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_link', 'shop_link', 'external_id', 'model',
                    'quantity', 'price', 'price_rrc', 'has_parameters')
    list_display_links = ('id', 'product_link')
    list_filter = ('shop', 'product__category')
    search_fields = ('model', 'external_id', 'product__name', 'shop__name')
    list_editable = ('quantity', 'price', 'price_rrc')
    readonly_fields = ('has_parameters',)
    inlines = [ProductParameterInline]

    fieldsets = (
        ('Товар и магазин', {
            'fields': ('product', 'shop', 'external_id')
        }),
        ('Характеристики', {
            'fields': ('model', 'quantity', 'price', 'price_rrc')
        }),
        ('Статус', {
            'fields': ('has_parameters',),
            'classes': ('collapse',)
        }),
    )

    def product_link(self, obj):
        url = reverse('admin:backend_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = 'Товар'

    def shop_link(self, obj):
        url = reverse('admin:backend_shop_change', args=[obj.shop.id])
        return format_html('<a href="{}">{}</a>', url, obj.shop.name)

    shop_link.short_description = 'Магазин'

    def has_parameters(self, obj):
        return obj.product_parameters.count() > 0

    has_parameters.boolean = True
    has_parameters.short_description = 'Есть параметры'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'shop')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_link', 'product_infos_count', 'has_offers')
    list_display_links = ('id', 'name')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    readonly_fields = ('product_infos_count', 'has_offers')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'category')
        }),
        ('Статистика', {
            'fields': ('product_infos_count', 'has_offers'),
            'classes': ('collapse',)
        }),
    )

    def category_link(self, obj):
        url = reverse('admin:backend_category_change', args=[obj.category.id])
        return format_html('<a href="{}">{}</a>', url, obj.category.name)

    category_link.short_description = 'Категория'

    def product_infos_count(self, obj):
        count = obj.product_infos.count()
        url = reverse('admin:backend_productinfo_changelist') + f'?product__id={obj.id}'
        return format_html('<a href="{}">{} предложений</a>', url, count)

    product_infos_count.short_description = 'Количество предложений'

    def has_offers(self, obj):
        return obj.product_infos.filter(quantity__gt=0).exists()

    has_offers.boolean = True
    has_offers.short_description = 'Есть в наличии'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_info_link', 'quantity', 'price_display', 'total_price')
    fields = ('product_info_link', 'quantity', 'price_display', 'total_price')
    can_delete = False
    show_change_link = True
    max_num = 0

    def product_info_link(self, obj):
        url = reverse('admin:backend_productinfo_change', args=[obj.product_info.id])
        return format_html('<a href="{}">{} - {}</a>',
                           url,
                           obj.product_info.product.name,
                           obj.product_info.shop.name)

    product_info_link.short_description = 'Товар'

    def price_display(self, obj):
        return f"{obj.product_info.price} ₽"

    price_display.short_description = 'Цена'

    def total_price(self, obj):
        total = obj.quantity * obj.product_info.price
        return f"{total} ₽"

    total_price.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'status_colored', 'contact_link',
                    'dt', 'items_count', 'total_amount_display')
    list_display_links = ('id',)
    list_filter = ('status', 'dt', 'user')
    search_fields = ('user__email', 'user__username', 'contact__phone')
    readonly_fields = ('dt', 'total_amount_display', 'items_count')
    inlines = [OrderItemInline]
    date_hierarchy = 'dt'

    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'status', 'contact', 'dt')
        }),
        ('Статистика', {
            'fields': ('items_count', 'total_amount_display'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped',
               'mark_as_delivered', 'mark_as_cancelled']

    def user_link(self, obj):
        if obj.user:
            return format_html('{}', obj.user.email)
        return '-'

    user_link.short_description = 'Пользователь'

    def contact_link(self, obj):
        if obj.contact:
            url = reverse('admin:backend_contact_change', args=[obj.contact.id])
            return format_html('<a href="{}">{}, {}</a>',
                               url,
                               obj.contact.city,
                               obj.contact.phone)
        return '-'

    contact_link.short_description = 'Контакт'

    def status_colored(self, obj):
        colors = {
            OrderStatusChoices.BASKET: 'gray',
            OrderStatusChoices.CREATED: 'orange',
            OrderStatusChoices.CONFIRMED: 'blue',
            OrderStatusChoices.PROCESSING: 'purple',
            OrderStatusChoices.SHIPPED: 'green',
            OrderStatusChoices.DELIVERED: 'darkgreen',
            OrderStatusChoices.CANCELLED: 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                           color,
                           obj.get_status_display())

    status_colored.short_description = 'Статус'

    def items_count(self, obj):
        return obj.order_items.count()

    items_count.short_description = 'Количество товаров'

    def total_amount_display(self, obj):
        total = sum(item.quantity * item.product_info.price
                    for item in obj.order_items.select_related('product_info'))
        return f"{total:.2f} ₽"

    total_amount_display.short_description = 'Общая сумма'

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.exclude(status=OrderStatusChoices.BASKET).update(
            status=OrderStatusChoices.CONFIRMED
        )
        self.message_user(request, f'{updated} заказов подтверждено.')

    mark_as_confirmed.short_description = 'Подтвердить выбранные заказы'

    def mark_as_processing(self, request, queryset):
        updated = queryset.filter(status=OrderStatusChoices.CONFIRMED).update(
            status=OrderStatusChoices.PROCESSING
        )
        self.message_user(request, f'{updated} заказов в обработке.')

    mark_as_processing.short_description = 'Отправить в обработку'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status=OrderStatusChoices.PROCESSING).update(
            status=OrderStatusChoices.SHIPPED
        )
        self.message_user(request, f'{updated} заказов отправлено.')

    mark_as_shipped.short_description = 'Отметить как отправленные'

    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status=OrderStatusChoices.SHIPPED).update(
            status=OrderStatusChoices.DELIVERED
        )
        self.message_user(request, f'{updated} заказов доставлено.')

    mark_as_delivered.short_description = 'Отметить как доставленные'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(status=OrderStatusChoices.DELIVERED).update(
            status=OrderStatusChoices.CANCELLED
        )
        self.message_user(request, f'{updated} заказов отменено.')

    mark_as_cancelled.short_description = 'Отменить заказы'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'contact')

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление заказов со статусом delivered
        if obj and obj.status == OrderStatusChoices.DELIVERED:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'product_info_link', 'quantity', 'price_display', 'total_price')
    list_display_links = ('id',)
    list_filter = ('order__status', 'product_info__shop')
    search_fields = ('order__user__email', 'product_info__product__name')
    readonly_fields = ('price_display', 'total_price')

    def order_link(self, obj):
        url = reverse('admin:backend_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Заказ #{}</a>', url, obj.order.id)

    order_link.short_description = 'Заказ'

    def product_info_link(self, obj):
        url = reverse('admin:backend_productinfo_change', args=[obj.product_info.id])
        return format_html('<a href="{}">{} - {}</a>',
                           url,
                           obj.product_info.product.name,
                           obj.product_info.shop.name)

    product_info_link.short_description = 'Товар'

    def price_display(self, obj):
        return f"{obj.product_info.price} ₽"

    price_display.short_description = 'Цена'

    def total_price(self, obj):
        total = obj.quantity * obj.product_info.price
        return f"{total} ₽"

    total_price.short_description = 'Сумма'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'product_info__product', 'product_info__shop'
        )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'city', 'street', 'house', 'phone', 'full_address')
    list_display_links = ('id',)
    list_filter = ('city', 'user')
    search_fields = ('city', 'street', 'phone', 'user__email')
    readonly_fields = ('full_address',)

    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Адрес', {
            'fields': ('city', 'street', 'house', 'structure', 'building', 'apartment')
        }),
        ('Контактные данные', {
            'fields': ('phone',)
        }),
        ('Полный адрес', {
            'fields': ('full_address',),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        if obj.user:
            return format_html('{}', obj.user.email)
        return '-'

    user_link.short_description = 'Пользователь'

    def full_address(self, obj):
        parts = [obj.city, obj.street, f"д. {obj.house}"]
        if obj.structure:
            parts.append(f"стр. {obj.structure}")
        if obj.building:
            parts.append(f"корп. {obj.building}")
        if obj.apartment:
            parts.append(f"кв. {obj.apartment}")
        return ", ".join(parts)

    full_address.short_description = 'Полный адрес'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'products_count')
    search_fields = ('name',)
    readonly_fields = ('products_count',)

    def products_count(self, obj):
        return obj.product_parameters.count()

    products_count.short_description = 'Количество товаров с параметром'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count=Count('product_parameters')
        )


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_info_link', 'parameter_link', 'value')
    list_display_links = ('id',)
    list_filter = ('parameter', 'product_info__shop')
    search_fields = ('value', 'parameter__name', 'product_info__product__name')

    def product_info_link(self, obj):
        url = reverse('admin:backend_productinfo_change', args=[obj.product_info.id])
        return format_html('<a href="{}">{} - {}</a>',
                           url,
                           obj.product_info.product.name,
                           obj.product_info.shop.name)

    product_info_link.short_description = 'Товар'

    def parameter_link(self, obj):
        url = reverse('admin:backend_parameter_change', args=[obj.parameter.id])
        return format_html('<a href="{}">{}</a>', url, obj.parameter.name)

    parameter_link.short_description = 'Параметр'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product_info__product', 'product_info__shop', 'parameter'
        )