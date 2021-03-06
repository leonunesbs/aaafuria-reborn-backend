import requests
import stripe
from bank.models import Conta
from decouple import config
from django.conf import settings
from django.db import models
from django.utils import timezone

API_KEY = settings.STRIPE_API_KEY


class Produto(models.Model):
    nome = models.CharField(max_length=100, verbose_name='nome do produto')
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    preco_socio = models.DecimalField(max_digits=8, decimal_places=2)
    preco_atleta = models.DecimalField(max_digits=8, decimal_places=2)
    preco_staff = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, verbose_name='preço diretor')
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/')
    has_variations = models.BooleanField(default=False)
    has_observacoes = models.BooleanField(default=False)
    plantao_only = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    exclusivo_competidor = models.BooleanField(default=False)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        if self.estoque == 0:
            self.is_active = False

        super().save(*args, *kwargs)


class VariacaoProduto(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name='variacoes')
    nome = models.CharField(max_length=100, verbose_name='variação')
    preco = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)
    preco_socio = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)
    preco_atleta = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)
    preco_staff = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name='preço diretor')
    estoque = models.IntegerField(default=0)
    imagem = models.ImageField(
        upload_to='produtos/variacoes/', blank=True, null=True)

    def __str__(self):
        return f'{self.produto.nome} - {self.nome}'

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        super().save(*args, *kwargs)


class ProdutoPedido(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name='produtos')
    variacao = models.ForeignKey(
        VariacaoProduto, on_delete=models.CASCADE, related_name='variacoes', null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    quantidade = models.IntegerField(default=1)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    preco = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    preco_socio = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)
    preco_atleta = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)
    preco_staff = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)

    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome} - {self.user.socio.nome}'

    def set_price(self):
        if self.variacao:
            self.preco = self.variacao.preco if self.variacao.preco else self.produto.preco
            self.preco_socio = self.variacao.preco_socio if self.variacao.preco_socio else self.produto.preco_socio
            self.preco_atleta = self.variacao.preco_atleta if self.variacao.preco_atleta else self.produto.preco_atleta
            self.preco_staff = self.variacao.preco_staff if self.variacao.preco_staff else self.produto.preco_staff
        else:
            self.preco = self.produto.preco
            self.preco_socio = self.produto.preco_socio
            self.preco_atleta = self.produto.preco_atleta
            self.preco_staff = self.produto.preco_staff

    def get_price(self):
        if self.user.is_staff:
            self.total = self.preco_staff * self.quantidade
            self.save()
            return self.preco_staff

        if self.user.socio.is_socio:
            if self.user.socio.is_atleta:
                self.total = self.preco_atleta * self.quantidade
                self.save()
                return self.preco_atleta
            else:
                self.total = self.preco_socio * self.quantidade
                self.save()
                return self.preco_socio

        self.total = self.preco * self.quantidade
        self.save()
        return self.preco

    def save(self, *args, **kwargs):
        self.set_price()
        super().save(*args, **kwargs)


class Carrinho(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    produtos = models.ManyToManyField(ProdutoPedido, blank=True)
    total = models.DecimalField(
        max_digits=8, decimal_places=2, default=0)

    stripe_checkout_id = models.CharField(
        max_length=150, null=True, blank=True)
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

    @property
    def stripe_checkout_url(self, api_key=API_KEY):
        stripe.api_key = api_key
        session = stripe.checkout.Session.retrieve(self.stripe_checkout_id)

        return session.url

    def get_total(self):
        total = 0
        for produto in self.produtos.all():
            total += produto.get_price() * produto.quantidade
        self.total = total
        self.save()
        return total

    def set_short_stripe_link(self, long_url):
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

    def create_stripe_checkout_session(self, api_key=API_KEY):
        stripe.api_key = api_key
        session = stripe.checkout.Session.create(
            success_url='https://aaafuria.site/pagamento-confirmado',
            cancel_url='https://aaafuria.site/carrinho',
            mode='payment',
            line_items=[
                {
                    'name': produto.produto.nome,
                    'quantity': produto.quantidade,
                    'currency': 'BRL',
                    'amount': int(produto.get_price() * 100),
                    'tax_rates': ['txr_1KT7puH8nuTtWMpP8U05kbNZ']
                } for produto in self.produtos.all()
            ],
            customer=self.user.socio.stripe_customer_id,
            payment_method_types=['card'],
            allow_promotion_codes=True,
        )

        self.status = 'aguardando'
        self.stripe_checkout_id = session.id

    def set_paid(self):
        for produto_pedido in self.produtos.all():
            if produto_pedido.produto.has_variations:
                produto_pedido.produto.estoque -= produto_pedido.quantidade
                produto_pedido.variacao.estoque -= produto_pedido.quantidade
                produto_pedido.produto.save()
                produto_pedido.variacao.save()
            else:
                produto_pedido.produto.estoque -= produto_pedido.quantidade
                produto_pedido.produto.save()

            produto_pedido.ordered = True
            produto_pedido.save()

        self.status = 'pago'
        self.ordered = True
        self.data_pago = timezone.now()

        conta, _ = Conta.objects.get_or_create(socio=self.user.socio)
        if conta.socio.is_socio:
            conta.calangos += int(
                (self.total // 5) * 50)
        conta.save()

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
