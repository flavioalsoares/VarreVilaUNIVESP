import re
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


class AcessibilidadeTest(TestCase):
    """
    Camada estática da acessibilidade — o que precisa funcionar sem JavaScript.

    O comportamento dos controles vive em static/js/preferencias.js e não é
    coberto por esta suíte: testar JavaScript exigiria Jest ou Vitest, e a
    decisão foi não trazer npm ao projeto. O que se garante aqui é que a
    marcação de que o script depende continua sendo entregue.
    """

    def setUp(self):
        self.html = self.client.get(reverse('public:home')).content.decode()

    def test_pagina_oferece_atalho_para_o_conteudo(self):
        self.assertIn('class="pular-conteudo"', self.html)
        self.assertIn('href="#conteudo"', self.html)

    def test_alvo_do_atalho_existe(self):
        self.assertIn('id="conteudo"', self.html)

    def test_barra_de_preferencias_e_entregue(self):
        self.assertIn('data-barra-acessibilidade', self.html)

    def test_barra_e_um_grupo_rotulado(self):
        self.assertIn('aria-label="Preferências de acessibilidade"', self.html)

    def test_controles_de_fonte_e_contraste_existem(self):
        for acao in ('diminuir-fonte', 'restaurar-fonte', 'aumentar-fonte',
                     'alternar-contraste'):
            self.assertIn(f'data-acao="{acao}"', self.html)

    def test_botao_de_contraste_expoe_o_estado(self):
        self.assertIn('aria-pressed="false"', self.html)

    def test_ha_regiao_viva_para_anunciar_a_mudanca(self):
        self.assertIn('role="status"', self.html)
        self.assertIn('data-aviso-preferencia', self.html)

    def test_todos_os_botoes_declaram_o_tipo(self):
        """Botão sem type age como submit e envia formulário sem querer."""
        botoes = re.findall(r'<button[^>]*>', self.html)
        self.assertTrue(botoes, 'a página não tem botão algum — teste sem valor')
        for botao in botoes:
            self.assertIn('type=', botao, f'botão sem type declarado: {botao}')

    def test_modulo_de_preferencias_e_carregado(self):
        self.assertIn('js/preferencias.js', self.html)

    def test_preferencias_carrega_sem_defer_para_evitar_piscada(self):
        """
        Precisa aplicar a preferência antes da primeira pintura, então é script
        clássico e bloqueante — não módulo, que é adiado por definição.
        """
        for pagina in ('public:home', 'public:sobre', 'public:acoes', 'public:contato'):
            html = self.client.get(reverse(pagina)).content.decode()
            self.assertNotIn('type="module" src="/static/js/preferencias.js"', html)
            self.assertIn('<script src="/static/js/preferencias.js">', html)


class SitePublicoJavaScriptTest(TestCase):

    def test_paginas_publicas_referenciam_o_modulo_de_navegacao(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertIn('js/navegacao.js', html)

    def test_menu_nao_depende_mais_de_handler_inline(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertNotIn('onclick=', html)
