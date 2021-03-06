from decouple import config
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext as _
from graphql_relay import to_global_id
from memberships.models import Membership
from store.models import Cart

API_KEY = settings.STRIPE_API_KEY


class Conta(models.Model):
    socio = models.OneToOneField(
        'core.Socio', on_delete=models.CASCADE, related_name='conta')
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    calangos = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.socio}'

    class Meta:
        verbose_name = 'conta'
        verbose_name_plural = 'contas'


# Model for transfering money between accounts
class Movimentacao(models.Model):
    conta_origem = models.ForeignKey(
        Conta, on_delete=models.CASCADE, related_name='transferencias_origem', blank=True, null=True)
    conta_destino = models.ForeignKey(
        Conta, on_delete=models.SET_NULL, related_name='transferencias_destino', blank=True, null=True)
    descricao = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolvida = models.BooleanField(default=False)
    resolvida_em = models.DateTimeField(null=True, blank=True)
    estornada = models.BooleanField(default=False)
    estornada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'movimentação'
        verbose_name_plural = 'movimentações'

    def __str__(self):
        return self.descricao

    def resolver(self):
        self.conta_origem.saldo -= self.valor
        self.conta_destino.saldo += self.valor

        self.resolvida = True
        self.resolvida_em = timezone.now()

        self.conta_destino.save()
        self.conta_origem.save()
        self.save()

    def estornar(self):
        self.conta_origem.saldo += self.valor
        self.conta_destino.saldo -= self.valor

        self.estornada = True
        self.estornada_em = timezone.now()

        self.conta_destino.save()
        self.conta_origem.save()
        self.save()

    def save(self, *args, **kwargs):
        super(Movimentacao, self).save(*args, **kwargs)

        if self.resolvida:
            if self.resolvida_em is None:
                self.resolver()


class PaymentMethod(models.Model):
    title = models.CharField(max_length=2)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='payments')
    method = models.ForeignKey(
        'PaymentMethod', on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    currency = models.CharField(max_length=3, default='BRL')
    status = models.CharField(max_length=50, default='PENDENTE')
    description = models.CharField(max_length=255)
    paid = models.BooleanField(default=False)
    expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.description

    def set_expired(self,  description):
        self.paid = False
        self.expired = True
        self.description = description
        self.status = 'EXPIRADO'

        self.save()

    def set_paid(self, description):
        self.paid = True
        self.description = description
        self.status = 'PAGO'
        self.save()

        membership = Membership.objects.filter(payment=self).first()
        cart = Cart.objects.filter(payment=self).first()

        if membership:
            membership.refresh()
            membership.save()
        if cart:
            cart.set_paid()
            cart.refresh()
            cart.save()

    def checkout(self, mode, items, discounts=[], payment_method_types=['card'], **kwargs):
        def stripe():
            import stripe
            stripe.api_key = API_KEY
            checkout_session = stripe.checkout.Session.create(
                customer=self.user.member.attachments.filter(
                    title='stripe_customer_id').first().content,
                success_url=f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}",
                cancel_url="https://aaafuria.site",
                line_items=items,
                mode=mode,
                discounts=discounts,
                payment_method_types=payment_method_types,
                expires_at=timezone.now() + timezone.timedelta(minutes=60)
            )

            attachment, created = Attachment.objects.get_or_create(
                payment=self, title='stripe_checkout_session_id')
            attachment.content = checkout_session.id
            attachment.save()

            return {
                'url': checkout_session['url']
            }

        def pix():
            return {
                'url': f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"
            }

        def pagseguro():
            from xml.etree import ElementTree

            import requests
            import xmltodict

            url = f'https://ws.pagseguro.uol.com.br/v2/checkout?email=leonunesbs.dev@gmail.com&token={config("PAGSEGURO_TOKEN")}'

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            count = 1
            total = 0
            items_obj = {}
            for item in items:
                items_obj[f'itemId{count}'] = count
                items_obj[f'itemDescription{count}'] = item['name']
                items_obj[f'itemAmount{count}'] = '%.2f' % float(
                    item['amount'] / 100),
                items_obj[f'itemQuantity{count}'] = item['quantity']
                items_obj[f'itemWeight{count}'] = 1000

                count += 1
                total += float(item['amount'] / 100)

            payload = {
                'senderName': self.user.member.name,
                'senderAreaCode': self.user.member.phone[:2],
                'senderPhone': self.user.member.phone[3:],
                'senderCPF': self.user.member.cpf,
                'senderBornDate': self.user.member.birth_date.strftime('%d/%m/%Y'),
                'senderEmail': self.user.member.email,

                'currency': 'BRL',
                'shippingAddressRequired': 'false',
                'redirectURL': 'https://aaafuria.site',
                'notificationURL': 'https://backend.aaafuria.site/bank/wh/',
                'maxUses': 3,
                'maxAge': 3000,
                'timeout': 20,
                'shippingCost': '1.00',
                'reference': to_global_id('bank.schema.nodes.PaymentNode', self.pk),
                'extraAmount': '%.2f' % float(total * 0.045),
                'excludePaymentMethodGroup': 'BOLETO'
            } | items_obj

            response = requests.post(url, data=payload, headers=headers)
            string_xml = response.content
            xml_tree = ElementTree.fromstring(string_xml)

            obj = xmltodict.parse(ElementTree.tostring(
                xml_tree, encoding='utf8').decode('utf8'))

            if 'errors' in obj:
                return print(obj)

            checkout_code = obj['checkout']['code']

            self.attachments.create(
                title='pagseguro_checkout_code', content=checkout_code)

            return {
                'url': f"https://pagseguro.uol.com.br/v2/checkout/payment.html?code={checkout_code}"
            }

        refs = {
            'ST': stripe,
            'PX': pix,
            'PS': pagseguro,
        }

        return refs[self.method.title]()

    def get_checkout_url(self):
        def stripe():
            import stripe
            stripe.api_key = API_KEY

            attachment = self.attachments.filter(
                title='stripe_checkout_session_id').first()
            if attachment:
                stripe_checkout_id = attachment.content
                checkout_session = stripe.checkout.Session.retrieve(
                    stripe_checkout_id)

                return checkout_session['url']
            return f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"

        def pix():
            return f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"

        def pagseguro():
            attachment = self.attachments.filter(
                title='pagseguro_checkout_code').first()

            if attachment:
                return f"https://pagseguro.uol.com.br/v2/checkout/payment.html?code={attachment.content}"

            return f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"

        refs = {
            'ST': stripe,
            'PX': pix,
            'PS': pagseguro
        }

        return refs[self.method.title]()


@receiver(models.signals.post_save, sender=Payment)
def recycle_payments(sender, instance, created, **kwargs):
    for payment in Payment.objects.all():
        if payment.expired and not payment.paid and payment.updated_at < timezone.now() - timezone.timedelta(days=1):
            cart = Cart.objects.filter(payment=payment).first()
            if cart:
                if not cart.ordered:
                    cart.delete()
            payment.delete()


class Attachment(models.Model):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255, editable=False)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to='bank/attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
