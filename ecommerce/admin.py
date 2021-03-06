from django.contrib import admin

import ecommerce.models as ecommerce_models


@admin.register(ecommerce_models.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'preco_socio',
                    'estoque', 'has_variations', 'plantao_only', 'is_active']


@admin.register(ecommerce_models.ProdutoPedido)
class ProdutoPedidoAdmin(admin.ModelAdmin):
    list_display = ['get_socio', 'get_socio_turma', 'produto',
                    'variacao', 'observacoes', 'quantidade', 'ordered']
    list_filter = ['ordered', 'variacao__nome', 'produto__nome']
    search_fields = ['user__socio__nome', 'user__socio__email', 'user__socio__apelido',
                     'user__socio__matricula', 'produto__nome', 'variacao__nome']

    def get_socio(self, obj):
        return obj.user.socio

    def get_socio_turma(self, obj):
        return obj.user.socio.turma

    get_socio.short_description = 'User'
    get_socio_turma.short_description = 'Turma'


@admin.register(ecommerce_models.Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ['get_socio', 'total', 'data_pago', 'ordered']
    list_filter = ['ordered']

    def get_socio(self, obj):
        return obj.user.socio

    get_socio.short_description = 'Sócio'


@admin.register(ecommerce_models.VariacaoProduto)
class VariacaoProdutoAdmin(admin.ModelAdmin):
    list_display = ['get_produto_nome', 'nome', 'preco', 'preco_socio',
                    'estoque']
    list_filter = ['produto__nome']
    search_fields = ['produto__nome']

    def get_produto_nome(self, obj):
        return obj.produto.nome

    get_produto_nome.short_description = 'Produto'


@admin.register(ecommerce_models.Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ['get_socio', 'valor',
                    'data_pagamento', 'forma_pagamento', 'status']
    list_filter = ['status', 'forma_pagamento', 'data_pagamento']

    def get_socio(self, obj):
        return obj.user.socio

    get_socio.short_description = 'Sócio'
