from django.contrib import admin

from members.models import Attachment, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'nickname', 'email', 'phone',
                    'rg', 'cpf', 'has_active_membership')
    search_fields = ('email', 'name', 'registration',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'title', 'content', 'file')
    search_fields = ('member__email', 'member__name',
                     'member__registration', 'title', 'content')
