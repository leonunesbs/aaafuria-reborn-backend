from django.contrib import admin

from .models import Attachment, Conta, Movimentacao, Payment, PaymentMethod


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    pass


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    pass


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ['socio', 'saldo', 'calangos', ]
    search_fields = ['socio__nome', 'socio__apelido',
                     'socio__matricula', 'socio__email', 'socio__stripe_customer_id']


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'conta_origem',
                    'conta_destino',  'valor']
    search_fields = ['descricao', 'conta_origem__socio__nome',
                     'conta_origem__socio__matricula', 'conta_origem__socio__email']
