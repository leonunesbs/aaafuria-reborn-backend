import stripe
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def avatar_dir(instance, filename):
    return f'socios/avatares/{instance.user.username}/'


class Socio(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=8, default="00000000")
    turma = models.CharField(max_length=10, default="MED: 00")
    nome = models.CharField(max_length=100)
    email = models.CharField(max_length=100, null=True, blank=True)
    apelido = models.CharField(max_length=100, null=True, blank=True)
    avatar = models.ImageField(
        upload_to=avatar_dir, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    whatsapp = models.CharField(max_length=25, null=True, blank=True)
    whatsapp_url = models.CharField(max_length=50, null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    is_socio = models.BooleanField(default=False)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)

    stripe_customer_id = models.CharField(max_length=50, null=True, blank=True)
    stripe_subscription_id = models.CharField(
        max_length=250, null=True, blank=True)
    stripe_portal_url = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f'{self.matricula}: {self.apelido or self.nome}'

    def set_matricula(self):
        if self.matricula == "00000000":
            self.matricula = self.user.username

    def set_wa_link(self):
        if self.whatsapp:
            self.whatsapp_url = f'https://wa.me/55{self.sanitize_number_string(self.whatsapp)}'

    def sanitize_number_string(self, number_string):
        if number_string:
            sanitized_number = number_string.replace('.', '').replace('-', '')
            sanitized_number = sanitized_number.replace(
                '(', '').replace(')', '').replace(' ', '')

            return sanitized_number

    def sanitize_fields(self):
        self.nome = self.nome.upper()
        self.email = self.user.email.lower()

        self.cpf = self.sanitize_number_string(self.cpf)
        self.rg = self.sanitize_number_string(self.rg)

    def create_stripe_customer(self, api_key=settings.STRIPE_API_KEY, *args, **kwargs):
        if not self.stripe_customer_id:
            stripe.api_key = api_key
            customer = stripe.Customer.create(
                name=self.nome,
                email=self.user.email,
                phone=self.whatsapp,
            )
            self.stripe_customer_id = customer.id

    def create_stripe_portal_url(self, api_key=settings.STRIPE_API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        session = stripe.billing_portal.Session.create(
            customer=self.stripe_customer_id,
            return_url="https://aaafuria.site/areasocio",
            locale='pt-BR'
        )
        self.stripe_portal_url = session.url

    def notificar(self, metodo, subject, text_template, html_template, context):
        def email():
            from_email = settings.EMAIL_HOST_USER
            to = self.user.email

            text_content = render_to_string(text_template, context)
            html_content = render_to_string(html_template, context)

            msg = EmailMultiAlternatives(subject, text_content, from_email, [
                                         to])

            msg.attach_alternative(
                html_content, "text/html")

            return msg.send(fail_silently=False)

        def sms():
            return 'Enviando sms...'

        def whatsapp():
            return 'Enviando whatsapp...'

        metodos = {
            'email': email,
            'sms': sms,
            'whatsapp': whatsapp
        }

        return metodos[metodo]()

    def save(self, *args, **kwargs):
        self.sanitize_fields()
        self.set_matricula()
        self.set_wa_link()
        self.create_stripe_customer()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class Pagamento(models.Model):
    socio = models.ForeignKey(
        Socio, on_delete=models.CASCADE, related_name='pagamentos')
    tipo_plano = models.ForeignKey('core.TipoPlano', on_delete=models.CASCADE)
    checkout_id = models.CharField(
        max_length=100, null=True, blank=True)
    checkout_url = models.CharField(max_length=400, null=True, blank=True)

    data_pagamento = models.DateField(default=timezone.now)

    status = models.CharField(
        max_length=15, default='Pendente')

    def __str__(self):
        return f'{self.socio}'

    def create_stripe_checkout(self, api_key=settings.STRIPE_API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        checkout_session = stripe.checkout.Session.create(
            customer=self.socio.stripe_customer_id,
            success_url="https://aaafuria.site/areasocio",
            cancel_url="https://aaafuria.site/",
            line_items=[
                {
                    'price': f'{self.tipo_plano.stripe_price_id}',
                    'quantity': 1,
                },
            ],
            mode='subscription',
            discounts=[
                {} if self.socio.data_inicio else {
                    'coupon': 'PRIMEIRAASSOCIACAO',
                }
            ]
        )

        self.checkout_url = checkout_session.url
        self.checkout_id = checkout_session.id

    def check_status(self, api_key=settings.STRIPE_API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        try:
            checkout = stripe.checkout.Session.retrieve(self.checkout_id)
            self.status = checkout.status
            if self.status == 'complete':
                self.socio.is_active = True
        except Exception as e:
            self.status = 'Cancelado'

    def save(self, *args, **kwargs):
        if not self.checkout_id:
            self.create_stripe_checkout()
        super().save(*args, **kwargs)


# Class named TipoPlano that represents the type of plan.
class TipoPlano(models.Model):
    nome = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nome
