from django.contrib import admin

from store.models import Attachment, Cart, CartItem, Item, Ticket


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    pass


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'item', 'description',
                    'quantity', 'ordered', 'checked_out')
    list_filter = ('cart', 'item', 'ordered')
    search_fields = ('cart', 'item', 'cart__user__username',
                     'cart__user__email', 'cart__user__member__name',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'ordered',
        'checked_out',
        'created_at',
        'updated_at',
    ]
    list_filter = [
        'ordered',
        'checked_out',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'user__member__name',
    ]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    pass
