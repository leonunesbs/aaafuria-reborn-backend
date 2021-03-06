from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html

import core.models as core_models


def linkify(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return '-'
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f'admin:{app_label}_{model_name}_change'
        link_url = reverse(view_name, args=[linked_obj.pk])
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name  # Sets column name
    return _linkify


class CustomUserAdmin(admin.ModelAdmin):
    @admin.action(description='Definir selecionados como Staff')
    def set_staff(self, request, queryset):
        queryset.update(is_staff=True)

    actions = [set_staff]
    form = UserChangeForm
    fieldsets = UserAdmin.fieldsets

    list_display = ('username', 'email', 'is_staff',
                    'is_superuser', 'is_active')
    search_fields = ['username', 'email', 'socio__nome']


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(core_models.Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('apelido', 'is_socio', 'is_atleta', 'nome',
                    'turma', 'matricula', 'whatsapp_url_link', 'data_fim')
    list_filter = ('turma', 'is_socio')
    search_fields = ('apelido', 'nome', 'matricula',
                     'stripe_customer_id', 'email')

    def whatsapp_url_link(self, obj):
        return format_html("<a href='{url}' target='_blank'>{url}</a>", url=obj.whatsapp_url)

    def is_atleta(self, obj):
        return obj.is_atleta

    is_atleta.boolean = True


@admin.register(core_models.Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['socio', 'tipo_plano', 'status', 'data_pagamento']
    search_fields = ['socio__matricula', 'socio__email', 'socio__nome']
    list_filter = ['tipo_plano', 'status']


@admin.register(core_models.TipoPlano)
class TipoPlanoAdmin(admin.ModelAdmin):
    pass


@admin.register(core_models.FeaturePost)
class FeaturePostAdmin(admin.ModelAdmin):
    pass
