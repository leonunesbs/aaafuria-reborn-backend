import requests
import stripe
from decouple import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext as _


def socio_dir(instance, filename):
    filename = 'avatar' + '.' + filename.split('.')[-1]
    return f'socios/{instance.user.username}/{filename}'


API_KEY = settings.STRIPE_API_KEY


class Socio(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=8, default="00000000")
    turma = models.CharField(max_length=10, default="MED: 00")
    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, null=True, blank=True)
    verified_email = models.BooleanField(default=False)
    apelido = models.CharField(max_length=100, null=True, blank=True)
    avatar = models.ImageField(
        upload_to=socio_dir, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    whatsapp = models.CharField(max_length=25, null=True, blank=True)
    whatsapp_url = models.CharField(max_length=50, null=True, blank=True)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    is_socio = models.BooleanField(default=False)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)

    vaccine_card = models.FileField(
        upload_to=socio_dir, null=True, blank=True)
    declaracao_matricula = models.FileField(
        upload_to=socio_dir, null=True, blank=True)

    stripe_customer_id = models.CharField(
        max_length=50, null=True, blank=True)
    stripe_subscription_id = models.CharField(
        max_length=250, null=True, blank=True)

    def __str__(self):
        return f'{self.matricula}: {self.apelido or self.nome}'

    @ property
    def stripe_portal_url(self, api_key=API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        session = stripe.billing_portal.Session.create(
            customer=self.stripe_customer_id,
            return_url="https://aaafuria.site/areamembro",
            locale='pt-BR',
        )
        return session.url

    def sanitize_number_string(self, number_string):
        if number_string:
            sanitized_number = number_string.replace(
                '.', '').replace('-', '')
            sanitized_number = sanitized_number.replace(
                '(', '').replace(')', '').replace(' ', '')

            return sanitized_number

    def sanitize_fields(self):
        self.nome = self.nome.strip().upper()

        if self.apelido:
            self.apelido = self.apelido.strip()
        if self.email:
            self.email = self.user.email.strip().lower()
        if self.cpf:
            self.cpf = self.sanitize_number_string(self.cpf)
        if self.rg:
            self.rg = self.sanitize_number_string(self.rg)
        if self.whatsapp:
            self.whatsapp = self.sanitize_number_string(self.whatsapp)

    def create_stripe_customer(self, api_key=API_KEY, *args, **kwargs):
        if not self.stripe_customer_id:
            stripe.api_key = api_key
            retrieved_customer_list = stripe.Customer.list(
                limit=1, email=self.email).data

            if len(retrieved_customer_list) > 0:
                self.stripe_customer_id = retrieved_customer_list[0].id
            else:
                customer = stripe.Customer.create(
                    email=self.email,
                    name=self.nome,
                    metadata={'matricula': self.matricula,
                              'apelido': self.apelido},
                    phone=self.whatsapp,
                )
                self.stripe_customer_id = customer.id

    def notificar(self, metodo, text_template, subject=None, context=None, html_template=None):
        def email():
            plaintext = get_template(text_template)
            htmly = get_template(html_template)

            from_email, to = settings.EMAIL_HOST_USER, self.user.email

            text_content = plaintext.render(context)
            html_content = htmly.render(context)

            msg = EmailMultiAlternatives(subject, text_content, from_email, [
                to])

            msg.attach_alternative(
                html_content, "text/html")

            msg.send(fail_silently=False)

        def sms():
            from twilio.rest import Client
            account_sid = config("TWILIO_ACCOUNT_SID")
            auth_token = config("TWILIO_AUTH_TOKEN")
            client = Client(account_sid, auth_token)

            context.update({'socio': self})

            plaintext = get_template(text_template)
            text_content = plaintext.render(context)

            message_sms = client.messages.create(
                body=text_content,
                from_='+17655772714',
                to=f'+55{self.whatsapp}'
            )

            return message_sms.sid

        def whatsapp():
            from twilio.rest import Client
            account_sid = config("TWILIO_ACCOUNT_SID")
            auth_token = config("TWILIO_AUTH_TOKEN")
            client = Client(account_sid, auth_token)

            context.update({'socio': self})

            plaintext = get_template(text_template)
            text_content = plaintext.render(context)

            message_wpp = client.messages \
                .create(
                    body=text_content,
                    from_='whatsapp:+14155238886',
                    to=f'whatsapp:+55{self.whatsapp[:2] + self.whatsapp[3:]}'
                )

            return message_wpp.sid

        metodos = {
            'email': email,
            'sms': sms,
            'whatsapp': whatsapp
        }

        return metodos[metodo]()

    def clean(self):
        self.sanitize_fields()

        if self.matricula == "00000000":
            self.matricula = self.user.username
        if self.whatsapp:
            if self.whatsapp == '___________':
                raise ValidationError(
                    'O campo Whatsapp não pode ser vazio.')

            self.whatsapp_url = f'https://wa.me/55{self.whatsapp}'

    def adicionar_coupom_cheers(self):
        base = 180
        atleta = base
        socio = base + 5
        n_socio = base + 45

        url = 'https://cheersshop.com.br/codigo'
        obj = {
            "nome": self.cpf,
            "desconto_porcentagem": None,
            "desconto_reais": atleta if self.is_atleta else socio if self.is_socio else n_socio,
            "quantidade": "1",
            "maximo_usuario": "1",
            "vendedor": "1874",
            "ativo": True,
            "uso": "1",
            "usuario": 192061
        }

        return requests.post(url, data=obj, headers={
            'Authorization': f'Bearer {config("CHEERS_TOKEN")}'})

    def save(self, *args, **kwargs):
        self.clean()
        self.create_stripe_customer()

        super().save(*args, **kwargs)

        if self.stripe_customer_id and Socio.objects.filter(
                stripe_customer_id=self.stripe_customer_id).count() > 1:
            raise ValidationError('Já existe um usuário com esse email.')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    '''
    @receiver(post_save, sender='core.Socio')
    def socio_post_save(sender, instance, created, **kwargs):
        from memberships.models import Membership
        socio: Socio = instance

        if socio.is_socio and socio.data_fim and socio.stripe_subscription_id:
            if (socio.data_fim.day, socio.data_fim.month) < (30, 6):
                membership, created = Membership.objects.get_or_create(
                    ref=Membership.STRIPE,
                    member=socio.user.member,
                    membership_plan=MembershipPlan.objects.get(
                        title='MENSAL'),
                    is_active=True
                )
                if created:
                    Attachment.objects.get_or_create(
                        membership=membership,
                        title='stripe_subscription_id',
                        content=socio.stripe_subscription_id
                    )
                    membership.refresh()
    '''


class Pagamento(models.Model):
    socio = models.ForeignKey(
        Socio, on_delete=models.CASCADE, related_name='pagamentos')
    tipo_plano = models.ForeignKey('core.TipoPlano', on_delete=models.CASCADE)
    checkout_id = models.CharField(
        max_length=100, null=True, blank=True)
    data_pagamento = models.DateField(default=timezone.now)

    status = models.CharField(
        max_length=15, default='Pendente')

    def __str__(self):
        return f'{self.socio}'

    @property
    def checkout_url(self, api_key=API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        checkout_session = stripe.checkout.Session.retrieve(
            self.checkout_id,
        )
        return checkout_session.url

    def create_stripe_checkout(self, api_key=API_KEY, *args, **kwargs):
        stripe.api_key = api_key
        checkout_session = stripe.checkout.Session.create(
            customer=self.socio.stripe_customer_id,
            success_url="https://aaafuria.site/pagamento-confirmado",
            cancel_url="https://aaafuria.site/sejasocio",
            line_items=[
                {
                    'price': f'{self.tipo_plano.stripe_price_id}',
                    'quantity': 1,
                },
            ],
            mode='subscription',
            discounts=[
                {} if self.socio.data_inicio else {
                    'coupon': 'PRIMEIRAASSOCIACAO'
                }
            ],
            payment_method_types=['card', 'boleto'],
        )

        self.checkout_id = checkout_session.id

    def check_status(self, api_key=API_KEY, *args, **kwargs):
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


class TipoPlano(models.Model):
    nome = models.CharField(max_length=100)
    stripe_price_id = models.CharField(
        max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nome


class FeaturePost(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='feature_posts/')
    button_target = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            FeaturePost.objects.filter(active=True).update(active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('feature post')
        verbose_name_plural = _('feature posts')
