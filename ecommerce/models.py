import requests
import stripe
from decouple import config
from django.conf import settings
from django.db import models
from django.utils import timezone


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    preco_socio = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    has_variations = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class VariacaoProduto(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name='variacoes')
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    preco_socio = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(
        upload_to='produtos/variacoes/', blank=True, null=True)

    def __str__(self):
        return f'{self.produto.nome} - {self.nome}'


class ProdutoPedido(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name='produtos')
    variacao = models.ForeignKey(
        VariacaoProduto, on_delete=models.CASCADE, related_name='variacoes', null=True, blank=True)
    quantidade = models.IntegerField(default=1)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    preco_socio = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)

    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome} - {self.user.socio.nome}'

    def get_price(self):
        if self.variacao:
            self.preco = self.variacao.preco
            self.preco_socio = self.variacao.preco_socio
            self.save()
        else:
            self.preco = self.produto.preco
            self.preco_socio = self.produto.preco_socio
            self.save()

        if self.user.socio.is_socio:
            self.total = self.preco_socio * self.quantidade
            self.save()
            return self.preco_socio

        self.total = self.preco * self.quantidade
        self.save()
        return self.preco

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)


class Carrinho(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    produtos = models.ManyToManyField(ProdutoPedido, blank=True)
    total = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)

    stripe_checkout_id = models.CharField(
        max_length=150, null=True, blank=True)
    stripe_checkout_url = models.CharField(
        max_length=500, null=True, blank=True)

    stripe_short_checkout_url = models.CharField(
        max_length=400, null=True, blank=True)

    data_pedido = models.DateTimeField(auto_now_add=True)
    data_pago = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_cancelado = models.DateTimeField(null=True, blank=True)

    ordered = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=(
            ('criado', 'Criado'),
            ('aguardando', 'Aguardando pagamento'),
            ('pago', 'Pago'),
            ('entregue', 'Entregue'),
            ('cancelado', 'Cancelado'),
        ), default='criado')

    def __str__(self):
        return f'R$ {self.total} - {self.user.socio.nome}'

    def get_total(self):
        total = 0
        for produto in self.produtos.all():
            total += produto.get_price() * produto.quantidade
        self.total = total
        self.save()
        return total

    def set_short_stripe_link(self, long_url):
        if not self.stripe_short_checkout_url:
            url = "https://api-ssl.bitly.com/v4/shorten"
            headers = {
                "Host": "api-ssl.bitly.com",
                "Accept": "application/json",
                "Authorization": f"Bearer {config('BITLY_API_KEY')}"
            }
            payload = {
                "long_url": long_url
            }
            # constructing this request took a good amount of guess
            # and check. thanks Postman!
            r = requests.post(url, headers=headers, json=payload)
            self.stripe_short_checkout_url = r.json()[u'id']
            self.save()

    def create_stripe_checkout_session(self, api_key=settings.STRIPE_API_KEY):
        stripe.api_key = api_key
        session = stripe.checkout.Session.create(
            success_url='https://aaafuria.site/',
            cancel_url='https://aaafuria.site/carrinho',
            mode='payment',
            line_items=[
                {
                    'name': produto.produto.nome,
                    'quantity': produto.quantidade,
                    'currency': 'BRL',
                    'amount': int(produto.get_price() * 100),
                } for produto in self.produtos.all()
            ],
            customer=self.user.socio.stripe_customer_id,
            allow_promotion_codes=True
        )

        self.status = 'aguardando'
        self.stripe_checkout_id = session.id
        self.stripe_checkout_url = session.url

    def set_paid(self):
        for produto_pedido in self.produtos.all():
            if not produto_pedido.produto.has_variations:
                produto_pedido.produto.estoque -= produto_pedido.quantidade
                produto_pedido.produto.save()
            else:
                produto_pedido.variacao.estoque -= produto_pedido.quantidade
                produto_pedido.variacao.save()

            produto_pedido.ordered = True
            produto_pedido.save()

        self.status = 'pago'
        self.ordered = True
        self.data_pago = timezone.now()

        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Pagamento(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    data_pagamento = models.DateTimeField(auto_now_add=True)
    carrinho = models.ForeignKey(
        Carrinho, on_delete=models.CASCADE, related_name='pagamentos')
    forma_pagamento = models.CharField(
        max_length=20, choices=(
            ('cartao', 'Cartão de crédito'),
            ('especie', 'Espécie'),
            ('pix', 'PIX'),
        ), default='cartao')

    status = models.CharField(
        max_length=20, choices=(
            ('criado', 'Criado'),
            ('aguardando', 'Aguardando pagamento'),
            ('pago', 'Pago'),
            ('cancelado', 'Cancelado'),
        ), default='criado')

    def __str__(self):
        return f'{self.valor} - {self.user.socio.nome}'
