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

        refs = {
            'ST': stripe,
            'PX': pix,
        }

        return refs[self.method.title]()

    def get_checkout_url(self):
        def stripe():
            import stripe
            stripe.api_key = API_KEY

            attachment = Attachment.objects.filter(payment=self,
                                                   title='stripe_checkout_session_id').first()
            if attachment:
                stripe_checkout_id = attachment.content
                checkout_session = stripe.checkout.Session.retrieve(
                    stripe_checkout_id)

                return checkout_session['url']
            return f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"

        def pix():
            return f"https://aaafuria.site/bank/payment/{to_global_id('bank.schema.nodes.PaymentNode', self.pk)}"
        refs = {
            'ST': stripe,
            'PX': pix
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
