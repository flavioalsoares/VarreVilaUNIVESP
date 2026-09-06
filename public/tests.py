from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from events.tests import cria_evento
from impact.models import ImpactReport
from users.models import CustomUser


class PaginasPublicasTest(TestCase):
    """As quatro páginas institucionais abrem sem login — é a vitrine da organização."""

    def test_home_abre_para_visitante(self):
        self.assertEqual(self.client.get(reverse('public:home')).status_code, 200)

    def test_sobre_abre_para_visitante(self):
        self.assertEqual(self.client.get(reverse('public:sobre')).status_code, 200)

    def test_acoes_abre_para_visitante(self):
        self.assertEqual(self.client.get(reverse('public:acoes')).status_code, 200)

    def test_contato_abre_para_visitante(self):
        self.assertEqual(self.client.get(reverse('public:contato')).status_code, 200)


class IndicadoresPublicosTest(TestCase):
    """Os números da home somam apenas mutirões realizados."""

    def setUp(self):
        realizado = cria_evento(titulo='Já aconteceu', status='realizado')
        ImpactReport.objects.create(
            event=realizado, lixo_kg=Decimal('320.50'),
            numero_participantes=28, sacos_coletados=45,
        )
        cria_evento(titulo='Ainda vai acontecer', status='planejado')

    def test_home_conta_so_os_mutiroes_realizados(self):
        contexto = self.client.get(reverse('public:home')).context
        self.assertEqual(contexto['total_mutiroes'], 1)

    def test_home_soma_o_lixo_recolhido(self):
        contexto = self.client.get(reverse('public:home')).context
        self.assertEqual(contexto['total_lixo'], Decimal('320.50'))
        self.assertEqual(contexto['total_sacos'], 45)

    def test_home_lista_os_proximos_mutiroes(self):
        contexto = self.client.get(reverse('public:home')).context
        self.assertEqual(
            [e.titulo for e in contexto['proximos']], ['Ainda vai acontecer']
        )

    def test_indicadores_ficam_zerados_sem_dados(self):
        ImpactReport.objects.all().delete()
        contexto = self.client.get(reverse('public:home')).context
        self.assertEqual(contexto['total_lixo'], 0)
        self.assertEqual(contexto['total_sacos'], 0)


class PainelInternoTest(TestCase):

    def test_dashboard_exige_login(self):
        resposta = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)

    def test_dashboard_renderiza_para_usuario_autenticado(self):
        CustomUser.objects.create_user(username='logado', password='senha-de-teste')
        self.client.login(username='logado', password='senha-de-teste')
        resposta = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resposta.status_code, 200)

    def test_dashboard_referencia_os_modulos_de_javascript(self):
        """Guarda a extração do JS inline: os módulos precisam continuar sendo servidos."""
        CustomUser.objects.create_user(username='logado', password='senha-de-teste')
        self.client.login(username='logado', password='senha-de-teste')
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertIn('js/grafico-mensal.js', html)
        self.assertIn('js/mapa-eventos.js', html)


class SitePublicoJavaScriptTest(TestCase):

    def test_paginas_publicas_referenciam_o_modulo_de_navegacao(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertIn('js/navegacao.js', html)

    def test_menu_nao_depende_mais_de_handler_inline(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertNotIn('onclick=', html)
