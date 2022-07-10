from django.contrib import admin
from django.utils.html import format_html

from members.models import Attachment, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'nickname', 'email', 'phone', 'whatsapp_url',
                    'rg', 'cpf', 'has_active_membership')
    search_fields = ('email', 'name', 'registration',)

    def whatsapp_url(self, obj):
        return format_html("<a href='{url}' target='_blank'>{url}</a>", url=f'https://wa.me/55{obj.phone}')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'title', 'content', 'file')
    search_fields = ('member__email', 'member__name',
                     'member__registration', 'title', 'content')
