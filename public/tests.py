import re
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from datetime import date

from events.models import Event
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


class FiltrosDaPaginaDeAcoesTest(TestCase):
    """
    Marcação de que static/js/filtros.js depende.

    A página é entregue completa pelo Django e continua utilizável sem
    JavaScript — é o módulo que revela a barra de controles. Por isso os testes
    verificam duas coisas em par: que os dados estão nos atributos, e que os
    controles chegam escondidos.
    """

    def setUp(self):
        for i, (bairro, ano) in enumerate([
            ('Ermelino Matarazzo', 2024),
            ('Guaianases', 2025),
            ('Ermelino Matarazzo', 2025),
        ], 1):
            evento = cria_evento(
                titulo=f'Mutirão {i}',
                bairro=bairro,
                data=date(ano, 6, 10),
                status='realizado',
            )
            ImpactReport.objects.create(
                event=evento,
                lixo_kg=Decimal('100.00') * i,
                numero_participantes=10 * i,
                sacos_coletados=5 * i,
            )
        self.html = self.client.get(reverse('public:acoes')).content.decode()

    def test_modulo_de_filtros_e_carregado(self):
        self.assertIn('js/filtros.js', self.html)

    def test_barra_de_filtros_chega_escondida(self):
        """Controle que só funciona com JavaScript não aparece sem JavaScript."""
        barra = re.search(r'<form[^>]*data-filtros[^>]*>', self.html)
        self.assertIsNotNone(barra, 'a barra de filtros não foi renderizada')
        self.assertIn('hidden', barra.group())

    def test_cada_acao_carrega_os_dados_para_filtrar(self):
        linhas = re.findall(r'<div class="acao-linha"[^>]*>', self.html, re.S)
        self.assertEqual(len(linhas), 3)
        for linha in linhas:
            for atributo in ('data-titulo', 'data-bairro', 'data-local',
                             'data-ano', 'data-data', 'data-lixo'):
                self.assertIn(atributo, linha)

    def test_dados_de_ordenacao_sao_comparaveis(self):
        """data-data em ISO ordena por texto; data-lixo é número."""
        self.assertIn('data-data="2024-06-10"', self.html)
        self.assertIn('data-lixo="100.00"', self.html)

    def test_lista_e_alvo_de_reordenacao_estao_marcados(self):
        self.assertIn('data-lista-acoes', self.html)
        self.assertIn('data-sem-resultado', self.html)

    def test_controles_tem_rotulo_associado(self):
        for identificador in ('busca-acoes', 'filtro-bairro', 'filtro-ano', 'filtro-ordem'):
            self.assertIn(f'for="{identificador}"', self.html)
            self.assertIn(f'id="{identificador}"', self.html)

    def test_contagem_e_regiao_viva(self):
        self.assertIn('data-contagem', self.html)
        self.assertIn('aria-live="polite"', self.html)

    def test_sem_acoes_realizadas_nao_ha_barra_de_filtros(self):
        ImpactReport.objects.all().delete()
        Event.objects.all().delete()
        html = self.client.get(reverse('public:acoes')).content.decode()
        self.assertNotIn('data-filtros', html)
        self.assertIn('Nenhuma ação registrada ainda', html)


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

    O comportamento do painel vive em static/js (preferencias.js, leitura.js,
    guia-de-leitura.js, atalhos.js) e não é coberto por esta suíte: testar
    JavaScript exigiria Jest ou Vitest, e a decisão foi não trazer npm ao
    projeto. O que se garante aqui é que a marcação de que os módulos dependem
    continua sendo entregue, e que ela é semanticamente correta por si só.
    """

    TOGGLES = ('contraste', 'cinza', 'links', 'cursor',
               'espacamento', 'fonteLegivel', 'guia', 'movimento')

    def setUp(self):
        self.html = self.client.get(reverse('public:home')).content.decode()

    def test_pagina_oferece_atalho_para_o_conteudo(self):
        self.assertIn('class="pular-conteudo"', self.html)
        self.assertIn('href="#conteudo"', self.html)

    def test_alvo_do_atalho_existe(self):
        self.assertIn('id="conteudo"', self.html)

    def test_painel_e_entregue(self):
        self.assertIn('data-painel-acessibilidade', self.html)

    def test_painel_nasce_fechado(self):
        """Sem JavaScript o botão não abre nada, então o painel chega escondido."""
        painel = re.search(r'<div[^>]*id="painel-acessibilidade"[^>]*>', self.html)
        self.assertIsNotNone(painel)
        self.assertIn('hidden', painel.group())

    def test_botao_de_abrir_declara_o_que_controla(self):
        botao = re.search(r'<button[^>]*data-abrir-painel[^>]*>', self.html)
        self.assertIsNotNone(botao)
        self.assertIn('aria-expanded="false"', botao.group())
        self.assertIn('aria-controls="painel-acessibilidade"', botao.group())
        self.assertIn('aria-label=', botao.group())

    def test_painel_e_um_dialogo_rotulado(self):
        painel = re.search(r'<div[^>]*id="painel-acessibilidade"[^>]*>', self.html)
        self.assertIn('role="dialog"', painel.group())
        self.assertIn('aria-labelledby="painel-acessibilidade-titulo"', painel.group())
        self.assertIn('id="painel-acessibilidade-titulo"', self.html)

    def test_controles_de_fonte_existem(self):
        for acao in ('diminuir-fonte', 'restaurar-fonte', 'aumentar-fonte', 'restaurar-tudo'):
            self.assertIn(f'data-acao="{acao}"', self.html)

    def test_todas_as_alternancias_existem_e_expoem_o_estado(self):
        for chave in self.TOGGLES:
            with self.subTest(preferencia=chave):
                botao = re.search(rf'<button[^>]*data-alternar="{chave}"[^>]*>', self.html)
                self.assertIsNotNone(botao, f'falta o controle de {chave}')
                self.assertIn('aria-pressed="false"', botao.group())

    def test_leitura_em_voz_alta_tem_os_dois_controles(self):
        self.assertIn('data-leitura-acao="ler"', self.html)
        self.assertIn('data-leitura-acao="parar"', self.html)
        self.assertIn('data-leitura-estado', self.html)

    def test_ha_regiao_viva_para_anunciar_a_mudanca(self):
        self.assertIn('role="status"', self.html)
        self.assertIn('data-aviso-preferencia', self.html)

    def test_atalhos_de_teclado_sao_documentados_no_painel(self):
        """O eMAG pede que os atalhos estejam visíveis, não só implementados."""
        for atalho in ('<kbd>Alt</kbd>+<kbd>1</kbd>', '<kbd>Alt</kbd>+<kbd>2</kbd>',
                       '<kbd>Alt</kbd>+<kbd>3</kbd>'):
            self.assertIn(atalho, self.html)

    def test_todos_os_botoes_declaram_o_tipo(self):
        """Botão sem type age como submit e envia formulário sem querer."""
        botoes = re.findall(r'<button[^>]*>', self.html)
        self.assertTrue(botoes, 'a página não tem botão algum — teste sem valor')
        for botao in botoes:
            self.assertIn('type=', botao, f'botão sem type declarado: {botao}')

    def test_icones_decorativos_sao_ocultados_do_leitor_de_tela(self):
        icones = re.findall(r'<i class="bi [^"]*"[^>]*>', self.html)
        painel_ini = self.html.index('data-painel-acessibilidade')
        for icone in icones:
            if self.html.index(icone) > painel_ini:
                self.assertIn('aria-hidden="true"', icone, f'ícone sem aria-hidden: {icone}')

    def test_modulos_de_acessibilidade_sao_carregados(self):
        for modulo in ('preferencias', 'atalhos', 'guia-de-leitura', 'leitura', 'vlibras'):
            with self.subTest(modulo=modulo):
                self.assertIn(f'js/{modulo}.js', self.html)

    def test_preferencias_carrega_sem_defer_para_evitar_piscada(self):
        """
        Precisa aplicar a preferência antes da primeira pintura, então é script
        clássico e bloqueante — não módulo, que é adiado por definição.
        """
        for pagina in ('public:home', 'public:sobre', 'public:acoes', 'public:contato'):
            html = self.client.get(reverse(pagina)).content.decode()
            self.assertNotIn('type="module" src="/static/js/preferencias.js"', html)
            self.assertIn('<script src="/static/js/preferencias.js">', html)

    def test_plugin_do_vlibras_carrega_antes_da_inicializacao(self):
        """Módulos executam depois de scripts clássicos — a ordem no HTML importa."""
        plugin = self.html.index('vlibras-plugin.js')
        inicializacao = self.html.index('js/vlibras.js')
        self.assertLess(plugin, inicializacao)

    def test_marcacao_do_vlibras_e_entregue(self):
        for atributo in ('vw-access-button', 'vw-plugin-wrapper'):
            self.assertIn(atributo, self.html)


class AcessibilidadeNaAreaInternaTest(TestCase):
    """
    A mesma camada vale para quem opera o sistema, não só para quem visita.

    A área interna estende base.html e é construída sobre Bootstrap, então o
    alto contraste precisa alcançar os componentes do framework — cards,
    etiquetas de status, botões e tabelas — além dos tokens próprios.
    """

    def setUp(self):
        CustomUser.objects.create_user(username='operador', password='senha-de-teste')

    def paginas_internas(self):
        yield 'login (anônimo)', self.client.get(reverse('users:login'))
        self.client.login(username='operador', password='senha-de-teste')
        for nome in ('dashboard:index', 'events:lista', 'impact:lista', 'users:perfil'):
            yield nome, self.client.get(reverse(nome))

    def test_todas_as_telas_internas_trazem_o_painel(self):
        for nome, resposta in self.paginas_internas():
            with self.subTest(pagina=nome):
                self.assertEqual(resposta.status_code, 200)
                self.assertIn('data-painel-acessibilidade', resposta.content.decode())

    def test_todas_as_telas_internas_trazem_o_atalho_e_o_alvo(self):
        for nome, resposta in self.paginas_internas():
            with self.subTest(pagina=nome):
                html = resposta.content.decode()
                self.assertIn('class="pular-conteudo"', html)
                self.assertIn('id="conteudo"', html)

    def test_login_carrega_o_modulo_de_preferencias(self):
        """A tela que motivou estender a acessibilidade à área interna."""
        html = self.client.get(reverse('users:login')).content.decode()
        self.assertIn('<script src="/static/js/preferencias.js">', html)

    def test_area_interna_declara_o_alto_contraste(self):
        html = self.client.get(reverse('users:login')).content.decode()
        self.assertIn('data-contraste="alto"', html)

    def test_o_alvo_do_atalho_aparece_uma_vez_so(self):
        """base.html tem dois <main> num if/else — só um pode renderizar."""
        self.client.login(username='operador', password='senha-de-teste')
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertEqual(html.count('id="conteudo"'), 1)

    def test_painel_aparece_uma_vez_so_por_pagina(self):
        """O include está nos dois bases; nenhuma página pode herdar os dois."""
        for nome, resposta in self.paginas_internas():
            with self.subTest(pagina=nome):
                self.assertEqual(resposta.content.decode().count('id="painel-acessibilidade"'), 1)


class AlternativasEmTabelaTest(TestCase):
    """
    O gráfico e o mapa do painel são invisíveis para leitor de tela.
    alternativas-em-tabela.js gera uma <table> para cada um a partir dos
    mesmos json_script; aqui se garante que os pontos de ancoragem e os
    dados que o módulo lê estão na página.
    """

    def setUp(self):
        CustomUser.objects.create_user(username='operador', password='senha-de-teste')
        self.client.login(username='operador', password='senha-de-teste')
        self.html = self.client.get(reverse('dashboard:index')).content.decode()

    def test_modulo_e_carregado_no_painel(self):
        self.assertIn('js/alternativas-em-tabela.js', self.html)

    def test_ha_ancora_para_a_tabela_do_grafico(self):
        self.assertIn('data-tabela-para="graficoMensal"', self.html)

    def test_ha_ancora_para_a_tabela_do_mapa(self):
        self.assertIn('data-tabela-para="map"', self.html)

    def test_dados_que_o_modulo_le_estao_na_pagina(self):
        for id_ in ('labels-data', 'dados-data', 'eventos-data'):
            self.assertIn(f'id="{id_}"', self.html)


class FolhaDeAcessibilidadeCompartilhadaTest(TestCase):
    """As duas áreas consomem a mesma folha, para não duplicar as regras."""

    def test_site_publico_carrega_a_folha(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertIn('css/acessibilidade.css', html)

    def test_area_interna_carrega_a_folha(self):
        html = self.client.get(reverse('users:login')).content.decode()
        self.assertIn('css/acessibilidade.css', html)


class SitePublicoJavaScriptTest(TestCase):

    def test_paginas_publicas_referenciam_o_modulo_de_navegacao(self):
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertIn('js/navegacao.js', html)

    def test_nenhuma_pagina_publica_usa_handler_inline(self):
        """Todo comportamento vive em static/js — nada de on* na marcação."""
        for pagina in ('public:home', 'public:sobre', 'public:acoes', 'public:contato'):
            html = self.client.get(reverse(pagina)).content.decode()
            achados = re.findall(r'\son[a-z]+\s*=\s*"', html)
            self.assertEqual(achados, [], f'{pagina} tem handler inline: {achados}')
