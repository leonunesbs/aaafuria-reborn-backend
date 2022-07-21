
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from store.models import Cart, Ticket


class ModelsTest(TestCase):
    def test_create_ticket(self):
        cart = Cart.objects.create(
            user=User.objects.create(username='teste', password='teste'),

        )
        cart.ordered = True
        cart.save()
        print(Ticket.objects.all())
