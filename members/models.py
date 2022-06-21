from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


def get_description(self):
    return f'({self.member.registration}) {self.member.name}'


User.add_to_class("__str__", get_description)


def member_avatar_dir(instance, filename):
    return 'members/avatars/{0}/{1}'.format(instance.user.username, filename)


class Member(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    registration = models.CharField(max_length=8, default='00000000')
    group = models.CharField(max_length=7, default='MED: 00')

    name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=124)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=15)
    birth_date = models.DateField()

    avatar = models.ImageField(
        upload_to=member_avatar_dir, blank=True, null=True)
    rg = models.CharField(max_length=15, blank=True, null=True)
    cpf = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = 'membro'
        verbose_name_plural = 'membros'
        ordering = ['name']

    def __str__(self):
        return f'({self.registration}) {self.name}'

    @property
    def has_active_membership(self):
        from memberships.models import Membership
        membership = Membership.objects.filter(
            member=self, is_active=True).first()
        if membership and membership.is_active:
            return True
        return False

    @property
    def active_membership(self):
        return self.get_active_membership()

    @property
    def first_teamer(self):
        from atividades.models import Modalidade
        for modalidade in Modalidade.objects.all():
            if not self.user.socio.competidor:
                return False
            if self.user.socio.competidor in modalidade.competidores.all():
                return True
        return False

    def get_active_membership(self):
        from memberships.models import Membership
        membership = Membership.objects.filter(
            member=self, is_active=True).first()
        if membership and membership.is_active:
            return membership
        return None

    def clean(self):
        self.name = self.name.upper()
        self.nickname = self.nickname.upper()
        self.email = self.email.lower()
        self.phone = self.phone.replace(
            '(', '').replace(')', '').replace('-', '').replace(' ', '')
        self.rg = self.rg.replace('.', '').replace(
            '-', '') if self.rg else None
        self.cpf = self.cpf.replace('.', '').replace(
            '-', '') if self.cpf else None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


@receiver(models.signals.post_save, sender=Member)
def create_stripe_profile(sender, instance, created, **kwargs):
    import stripe
    from django.conf import settings

    stripe.api_key = settings.STRIPE_API_KEY

    if not instance.attachments.filter(title='stripe_customer_id').exists():
        customer = stripe.Customer.list(
            limit=1,
            email=instance.email,
        )
        if customer['data']:
            instance.attachments.create(
                title='stripe_customer_id',
                content=customer['data'][0]['id'],
            )
        else:
            customer = stripe.Customer.create(
                email=instance.email,
                name=instance.name,
                description=f'{instance.name} - {instance.registration}',
                metadata={
                    'registration': instance.registration,
                    'group': instance.group,
                },
            )
            instance.attachments.create(
                title='stripe_customer_id',
                content=customer['id'],
            )
    else:
        customer = stripe.Customer.retrieve(
            instance.attachments.filter(title='stripe_customer_id')[0].content
        )
        if customer['email'] != instance.email:
            customer.email = instance.email
            customer.save()


class Attachment(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255, editable=False)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to='members/attachments/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
