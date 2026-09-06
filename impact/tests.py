from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from events.tests import cria_evento
from users.models import CustomUser

from .models import ImpactReport


class ImpactReportModelTest(TestCase):

    def test_str_identifica_o_evento(self):
        evento = cria_evento(titulo='Mutirão Guaianases')
        relatorio = ImpactReport.objects.create(
            event=evento, lixo_kg=Decimal('250.00'), numero_participantes=42
        )
        self.assertEqual(str(relatorio), 'Impacto: Mutirão Guaianases')

    def test_relatorio_e_acessivel_a_partir_do_evento(self):
        evento = cria_evento()
        ImpactReport.objects.create(
            event=evento, lixo_kg=Decimal('10.00'), numero_participantes=3
        )
        evento.refresh_from_db()
        self.assertEqual(evento.impact_report.numero_participantes, 3)


class RegistroDeImpactoTest(TestCase):
    """Registrar impacto é atribuição de administrador e encerra o mutirão."""

    def setUp(self):
        self.evento = cria_evento(status='planejado')
        CustomUser.objects.create_user(
            username='gestor', password='senha-de-teste', perfil='admin'
        )
        CustomUser.objects.create_user(
            username='ajudante', password='senha-de-teste', perfil='voluntario'
        )
        self.dados = {
            'lixo_kg': '320.50',
            'numero_participantes': 28,
            'sacos_coletados': 45,
            'observacoes': 'Boa adesão da comunidade.',
        }

    def test_voluntario_nao_registra_impacto(self):
        self.client.login(username='ajudante', password='senha-de-teste')
        resposta = self.client.post(
            reverse('impact:registrar', args=[self.evento.pk]), self.dados
        )
        self.assertRedirects(resposta, reverse('events:detalhe', args=[self.evento.pk]))
        self.assertEqual(ImpactReport.objects.count(), 0)

    def test_administrador_registra_impacto(self):
        self.client.login(username='gestor', password='senha-de-teste')
        self.client.post(reverse('impact:registrar', args=[self.evento.pk]), self.dados)
        self.assertEqual(ImpactReport.objects.count(), 1)
        self.assertEqual(ImpactReport.objects.get().lixo_kg, Decimal('320.50'))

    def test_registrar_impacto_marca_o_evento_como_realizado(self):
        self.client.login(username='gestor', password='senha-de-teste')
        self.client.post(reverse('impact:registrar', args=[self.evento.pk]), self.dados)
        self.evento.refresh_from_db()
        self.assertEqual(self.evento.status, 'realizado')

    def test_segundo_registro_redireciona_para_a_edicao(self):
        ImpactReport.objects.create(
            event=self.evento, lixo_kg=Decimal('1.00'), numero_participantes=1
        )
        self.client.login(username='gestor', password='senha-de-teste')
        resposta = self.client.get(reverse('impact:registrar', args=[self.evento.pk]))
        self.assertRedirects(
            resposta, reverse('impact:editar', args=[self.evento.pk])
        )

    def test_lista_de_relatorios_exige_login(self):
        resposta = self.client.get(reverse('impact:lista'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)
