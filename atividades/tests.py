from core.models import Socio
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Competidor, Modalidade, Programacao

from django.core import mail
from django.conf import settings


class ModelTestCase(TestCase):
    def setUp(self):
        Socio.objects.create(
            user=User.objects.create_user(
                username='00000000',
                password='000000'
            ),
            nome='Leonardo Nunes',
            apelido='Leo',
            stripe_customer_id='cus_123456789',
        )

        Socio.objects.create(
            user=User.objects.create_user(
                username='11111111',
                password='111111'
            ),
            nome='Denise Almeida',
            apelido='Deni',
            stripe_customer_id='cus_123456789',
        )

        Socio.objects.create(
            user=User.objects.create_user(
                username='33333333',
                password='333333'
            ),
            nome='Jemima Kretli',
            apelido='Jems',
            stripe_customer_id='cus_123456789',
        )

    def test_create_competidor(self):
        print('test_create_competidor')
        competidor = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )
        competidor.save()
        self.assertEqual(competidor.socio.nome, 'LEONARDO NUNES')

    def test_create_modalidade(self):
        print('test_create_modalidade')
        modalidade = Modalidade.objects.create(
            nome='Carabina',
            categoria='Bateria'
        )
        modalidade.save()
        self.assertEqual(modalidade.nome, 'Carabina')
        self.assertEqual(modalidade.categoria, 'Bateria')

    def test_add_competidor_to_modalidade(self):
        print('test_add_competidor_to_modalidade')
        modalidade = Modalidade.objects.create(
            nome='Carabina',
            categoria='Bateria'
        )
        modalidade.save()
        competidor = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )
        competidor.save()
        modalidade.competidores.add(competidor)
        self.assertEqual(modalidade.competidores.count(), 1)

    def test_create_programacao(self):
        print('test_create_programacao')
        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
        )
        programacao.save()
        self.assertEqual(programacao.modalidade.nome, 'Carabina')

    def test_check_status_agendado(self):
        print('test_check_status_agendado')
        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
        )

        self.assertEqual(programacao.checar_estado(), 'Agendado')

    def test_check_status_confirmado(self):
        print('test_check_status_confirmado ')
        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
            competidores_minimo=2
        )
        competidor_1 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )
        competidor_2 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='11111111'),
        )

        programacao.competidores_confirmados.add(competidor_1)
        self.assertEqual(programacao.checar_estado(),
                         'Aguardando')
        programacao.competidores_confirmados.add(competidor_2)
        self.assertEqual(programacao.checar_estado(), 'Confirmado')

    def test_check_status_cheio(self):
        print('test_check_status_cheio')
        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
            competidores_minimo=2,
            competidores_maximo=3
        )
        competidor_1 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )
        competidor_2 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='11111111'),
        )
        competidor_3 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='33333333'),
        )

        programacao.competidores_confirmados.add(competidor_1)
        self.assertEqual(programacao.checar_estado(),
                         'Aguardando')
        programacao.competidores_confirmados.add(competidor_2)
        self.assertEqual(programacao.checar_estado(), 'Confirmado')
        programacao.competidores_confirmados.add(competidor_3)
        self.assertEqual(programacao.checar_estado(), 'Cheio')

    def test_checar_modalidades_participadas(self):
        print('test_checar_modalidades_participadas')
        competidor = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )

        modalidade_1 = Modalidade.objects.create(
            nome='Carabina',
            categoria='Bateria'
        )
        modalidade_2 = Modalidade.objects.create(
            nome='Futsal',
            categoria='Esporte'
        )
        modalidade_3 = Modalidade.objects.create(
            nome='Basquete',
            categoria='Esporte'
        )

        modalidade_1.competidores.add(competidor)
        modalidade_2.competidores.add(competidor)
        modalidade_3.competidores.add(competidor)

        self.assertEqual(competidor.modalidades.all().count(), 3)

    def test_confirmar_competidor_em_programacao(self):
        print('test_confirmar_competidor_em_programacao')
        socio = Socio.objects.get(user__username='00000000')
        competidor, _ = Competidor.objects.get_or_create(
            socio=socio,
        )

        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
            competidores_minimo=2
        )

        programacao.competidores_confirmados.add(competidor)
        self.assertEqual(programacao.competidores_confirmados.count(), 1)

    def test_notificar_responsavel_programacao_confirmado(self):
        competidor_1 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='00000000'),
        )
        competidor_2 = Competidor.objects.create(
            socio=Socio.objects.get(user__username='11111111'),
        )

        programacao = Programacao.objects.create(
            modalidade=Modalidade.objects.get_or_create(
                nome='Carabina', categoria='Bateria')[0],
            local='Estacionamento UNINOVAFAPI',
            competidores_minimo=2
        )

        programacao.competidores_confirmados.add(competidor_1)
        programacao.competidores_confirmados.add(competidor_2)

        self.assertEqual(programacao.checar_estado(), 'Confirmado')

        if (programacao.checar_estado() == 'Confirmado'):
            programacao.notificar_confirmacao()

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, 'Programação confirmada')
