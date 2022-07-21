from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext as _


class Item(models.Model):
    ref_item = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='variations',
    )
    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    membership_price = models.FloatField(blank=True, null=True)
    staff_price = models.FloatField(blank=True, null=True)

    image = models.ImageField(
        upload_to='store/images/items', blank=True, null=True, help_text=_('Image ratio: 1:1'))
    stock = models.IntegerField(default=0)

    is_variation = models.BooleanField(default=False, editable=False)
    has_variations = models.BooleanField(
        default=False, help_text=_('By checking this box, size variations will be created for this item.'))

    is_digital = models.BooleanField(
        default=True, help_text=_('Should this item be sold online?'))
    is_analog = models.BooleanField(
        default=True, help_text=_('Should this item be sold in person?'))
    is_event = models.BooleanField(
        default=False, help_text=_('Is this item an event?'))

    is_active = models.BooleanField(default=True)

    membership_exclusive = models.BooleanField(
        default=False, help_text=_('Should this item be sold only to members?'))
    max_per_user = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_('Maximum number of items per user'),
    )
    max_per_member = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_('Maximum number of items per member'),
    )
    disabled_payment_methods = models.ManyToManyField(
        'bank.PaymentMethod',
        blank=True,
        help_text=_(
            'Payment methods that will not be available for this item.'),
    )

    class Meta:
        ordering = ['is_variation']

    def __str__(self):
        return self.name if not self.ref_item else f'{self.ref_item.name} ({self.name})'

    @property
    def is_digital_only(self):
        return self.is_digital and not self.is_analog

    @property
    def is_analog_only(self):
        return self.is_analog and not self.is_digital

    def get_is_variation(self):
        self.is_variation = self.ref_item is not None
        return self.is_variation

    @property
    def is_available(self):
        return self.stock > 0

    def __str__(self):
        if self.ref_item:
            return f'{self.ref_item} ({self.name})'
        return self.name

    def save(self, *args, **kwargs):
        self.is_variation = self.get_is_variation()

        super().save(*args, **kwargs)


@receiver(models.signals.post_save, sender=Item)
def create_item_variations(sender, instance, created, **kwargs):
    if created and instance.has_variations:
        variations = [
            'PP BBLK',
            'P BBLK',
            'M BBLK',
            'G BBLK',
            'GG BBLK',
            'PP',
            'P',
            'M',
            'G',
            'GG',
        ]
        for variation in variations:
            sender.objects.create(
                ref_item=instance,
                name=variation,
                price=instance.price,
                description=instance.description,
                membership_price=instance.membership_price,
                staff_price=instance.staff_price,
                image=instance.image,
                is_digital=instance.is_digital,
                is_analog=instance.is_analog,
                is_active=instance.is_active
            )


class Attachment(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to='store/attachments/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class CartItem(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE)
    cart = models.ForeignKey(
        'Cart', on_delete=models.CASCADE, related_name='items')
    quantity = models.IntegerField(default=1)
    description = models.TextField(blank=True, null=True)

    ordered = models.BooleanField(default=False)
    checked_out = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.item} - {self.quantity}'

    def get_sub_total(self):
        total = 0

        if self.cart.user.is_staff:
            attached_price = Attachment.objects.filter(
                item=self.item, title='staff_price').first()
            if attached_price:
                total += float(attached_price.content) * self.quantity
                return total

        if self.cart.user.member.has_active_membership:
            attached_price = Attachment.objects.filter(
                item=self.item, title='membership_price').first()
            if attached_price:
                total += float(attached_price.content) * self.quantity
                return total

        total += self.item.price * self.quantity

        return total


class Ticket(models.Model):
    cart = models.ForeignKey(
        'store.Cart', on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=255)
    remaining_uses = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{str(self.cart)} [{self.title}]'

    @property
    def paid(self) -> bool:
        return self.cart.ordered

    def is_valid(self) -> bool:
        return True if self.remaining_uses > 0 else False

    def use(self):
        self.remaining_uses -= 1
        self.save()


class Cart(models.Model):
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='carts')
    payment = models.OneToOneField(
        'bank.Payment', on_delete=models.SET_NULL, blank=True, null=True, related_name='cart')

    ordered = models.BooleanField(default=False)
    checked_out = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f'{self.user.member.name}'

    def deliver(self):
        self.delivered = True
        for cart_item in self.items.all():
            cart_item.delivered = True
            cart_item.save()

    def set_paid(self):
        for item in self.items.all():
            item.item.stock -= item.quantity
            if item.item.ref_item:
                item.item.ref_item.stock -= item.quantity
                item.item.ref_item.save()
            item.item.save()

    def get_total(self):
        total = 0
        for item in self.items.all():
            total += item.get_sub_total()

    def refresh(self):
        if self.payment and self.payment.paid:
            self.ordered = True
            for cart_item in self.items.all():
                cart_item.ordered = True
                cart_item.save()

    def checkout(self, payment):
        self.payment = payment
        self.checked_out = True
        for cart_item in self.items.all():
            cart_item.checked_out = True
            cart_item.save()

    def get_total(self) -> float:
        total = 0

        for cart_item in self.items.all():
            total += cart_item.get_sub_total()
        return total


@receiver(models.signals.post_save, sender='store.Cart')
def create_ticket(sender, instance, created, **kwargs):
    if instance.ordered and not instance.tickets.all().count() > 0:
        for cart_item in instance.items.all():
            if cart_item.item.is_event:
                instance.tickets.create(
                    title=f'{cart_item.item.ref_item.name} ({cart_item.item.name})',
                    remaining_uses=cart_item.quantity
                )
