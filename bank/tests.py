from django.contrib.auth.models import User
from django.test import TestCase
from bank.models import Conta

from core.models import Socio


class ModelTestCase(TestCase):
    def setUp(self):
        Socio.objects.create(
            user=User.objects.create_user(
                username='00000000',
                password='000000'
            ),
            nome='Leonardo Nunes',
            apelido='Leo',
            stripe_customer_id='cus_123456789'
        )

    def test_add_calangos(self):
        socio = Socio.objects.get(user__username='00000000')
        conta, _ = Conta.objects.get_or_create(socio=socio)
        conta.calangos = int(((1490 / 100) // 10) * 100)
        self.assertEqual(socio.conta.calangos, 100)
        conta.calangos = int(((21490 / 100) // 10) * 100)
        self.assertEqual(socio.conta.calangos, 2100)
