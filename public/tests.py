import re
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from datetime import date, timedelta

from events.models import Event, InscricaoPublica
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

    def test_cada_acao_carrega_o_id_para_o_mapa_sincronizar(self):
        for linha in re.findall(r'<div class="acao-linha"[^>]*>', self.html, re.S):
            self.assertRegex(linha, r'data-id="\d+"')

    def test_sem_acoes_realizadas_nao_ha_barra_de_filtros(self):
        ImpactReport.objects.all().delete()
        Event.objects.all().delete()
        html = self.client.get(reverse('public:acoes')).content.decode()
        self.assertNotIn('data-filtros', html)
        self.assertIn('Nenhuma ação registrada ainda', html)


class ProximosMutiroesTest(TestCase):
    """
    "Próximos Mutirões" não pode listar mutirão que já passou. A home
    filtrava por data; a página de Ações, não — e exibia eventos vencidos.
    """

    def setUp(self):
        self.futuro = cria_evento(
            titulo='Ainda vai acontecer', status='planejado',
            data=date.today() + timedelta(days=5),
        )
        self.passado = cria_evento(
            titulo='Já passou', status='planejado',
            data=date.today() - timedelta(days=5),
        )

    def test_nenhuma_pagina_lista_mutirao_planejado_que_ja_passou(self):
        for pagina in ('public:home', 'public:acoes'):
            with self.subTest(pagina=pagina):
                contexto = self.client.get(reverse(pagina)).context
                titulos = [e.titulo for e in contexto['proximos']]
                self.assertIn('Ainda vai acontecer', titulos)
                self.assertNotIn('Já passou', titulos)

    def test_mutirao_de_hoje_ainda_conta_como_proximo(self):
        cria_evento(titulo='É hoje', status='planejado', data=date.today())
        for pagina in ('public:home', 'public:acoes'):
            with self.subTest(pagina=pagina):
                titulos = [e.titulo for e in self.client.get(reverse(pagina)).context['proximos']]
                self.assertIn('É hoje', titulos)


class MapaPublicoTest(TestCase):
    """
    O mapa público é a tela renderizada no cliente a partir da API. O Django
    entrega só o contêiner — escondido — e a descrição para leitor de tela.
    """

    def setUp(self):
        evento = cria_evento(titulo='Com mapa', status='realizado')
        ImpactReport.objects.create(event=evento, lixo_kg=Decimal('10.00'), numero_participantes=2)
        self.html = self.client.get(reverse('public:acoes')).content.decode()

    def test_modulo_e_carregado_depois_do_leaflet(self):
        """O módulo usa o global L — o Leaflet precisa vir antes no HTML."""
        self.assertIn('js/mapa-publico.js', self.html)
        self.assertLess(self.html.index('leaflet.js'), self.html.index('js/mapa-publico.js'))

    def test_folha_do_leaflet_e_carregada(self):
        self.assertIn('leaflet.css', self.html)

    def test_plugin_de_agrupamento_carrega_entre_o_leaflet_e_o_modulo(self):
        """O plugin estende L, então precisa do Leaflet antes e do módulo depois."""
        leaflet = self.html.index('leaflet@1.9.4/dist/leaflet.js')
        plugin = self.html.index('leaflet.markercluster.js')
        modulo = self.html.index('js/mapa-publico.js')
        self.assertLess(leaflet, plugin)
        self.assertLess(plugin, modulo)
        self.assertIn('MarkerCluster.css', self.html)

    def test_conteiner_chega_escondido(self):
        """Sem JavaScript não há mapa — e não deve haver um retângulo vazio."""
        conteiner = re.search(r'<div[^>]*data-mapa-publico[^>]*>', self.html)
        self.assertIsNotNone(conteiner)
        self.assertIn('hidden', conteiner.group())

    def test_area_do_mapa_e_uma_regiao_descrita(self):
        area = re.search(r'<div id="mapa-publico"[^>]*>', self.html)
        self.assertIsNotNone(area)
        self.assertIn('role="region"', area.group())
        self.assertIn('aria-labelledby="mapa-publico-titulo"', area.group())
        self.assertIn('aria-describedby="mapa-publico-descricao"', area.group())
        self.assertIn('id="mapa-publico-descricao"', self.html)

    def test_legenda_e_regiao_viva(self):
        legenda = re.search(r'<p[^>]*data-mapa-legenda[^>]*>', self.html)
        self.assertIsNotNone(legenda)
        self.assertIn('aria-live="polite"', legenda.group())

    def test_sem_acoes_realizadas_nao_ha_mapa(self):
        ImpactReport.objects.all().delete()
        Event.objects.all().delete()
        html = self.client.get(reverse('public:acoes')).content.decode()
        self.assertNotIn('data-mapa-publico', html)


class PrevisaoDoTempoTest(TestCase):
    """
    previsao.js consome o Open-Meteo a partir do navegador. Aqui se garante a
    marcação de que ele depende: coordenadas e data em cada card de próximo
    mutirão, em formato que o JavaScript consiga ler, e a saída escondida
    até haver o que mostrar.
    """

    def setUp(self):
        self.com_coordenadas = cria_evento(
            titulo='Com lugar', status='planejado',
            data=date.today() + timedelta(days=5),
            latitude=Decimal('-23.500400'), longitude=Decimal('-46.459000'),
        )
        self.sem_coordenadas = cria_evento(
            titulo='Sem lugar', status='planejado', data=date.today() + timedelta(days=7),
        )

    def test_card_com_coordenadas_carrega_os_dados_da_previsao(self):
        for pagina in ('public:home', 'public:acoes'):
            with self.subTest(pagina=pagina):
                html = self.client.get(reverse(pagina)).content.decode()
                card = re.search(r'<div class="proximo-(?:item|card)"[^>]*data-previsao[^>]*>', html)
                self.assertIsNotNone(card, 'card sem data-previsao')
                self.assertIn('data-lat="-23.500400"', card.group())
                self.assertIn('data-lng="-46.459000"', card.group())
                self.assertIn(f'data-data="{self.com_coordenadas.data.isoformat()}"', card.group())

    def test_coordenadas_saem_com_ponto_e_nao_virgula(self):
        """Mesmo bug do PR #7: floatformat localizado quebraria o parseFloat."""
        html = self.client.get(reverse('public:home')).content.decode()
        self.assertNotIn('data-lat="-23,', html)

    def test_card_sem_coordenadas_nao_pede_previsao(self):
        html = self.client.get(reverse('public:home')).content.decode()
        cards = re.findall(r'<div class="proximo-item"[^>]*>', html)
        self.assertEqual(len(cards), 2)
        self.assertEqual(sum('data-previsao' in c for c in cards), 1)

    def test_saida_e_fonte_nascem_escondidas(self):
        html = self.client.get(reverse('public:acoes')).content.decode()
        saida = re.search(r'<p class="previsao"[^>]*>', html)
        fonte = re.search(r'<p class="previsao-fonte"[^>]*>', html)
        self.assertIn('hidden', saida.group())
        self.assertIn('hidden', fonte.group())

    def test_atribuicao_ao_open_meteo_esta_na_pagina(self):
        html = self.client.get(reverse('public:acoes')).content.decode()
        self.assertIn('open-meteo.com', html)

    def test_modulo_e_carregado_nas_duas_paginas(self):
        for pagina in ('public:home', 'public:acoes'):
            with self.subTest(pagina=pagina):
                self.assertIn('js/previsao.js', self.client.get(reverse(pagina)).content.decode())


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


class LeituraEmVozAltaTest(TestCase):
    """
    O grupo "Ouvir a página" é sempre entregue visível.

    Ter `window.speechSynthesis` não garante que o navegador fale: o Brave
    remove as vozes remotas do Google e só usa o speech-dispatcher do sistema
    quando aberto com `--enable-speech-dispatcher`, então a lista de vozes vem
    vazia e `speak()` termina em `synthesis-failed`.

    A primeira tentativa de correção escondeu o grupo nesse caso, e isso tirou
    do painel uma função que existe — quem usa Chrome ou Firefox perdia o
    controle de vista por causa de uma limitação de outro navegador, e quem usa
    Brave deixou de saber que a função está lá. Agora o controle fica, e quem
    não tem voz recebe a explicação na linha de dica, que é região viva.
    """

    def setUp(self):
        CustomUser.objects.create_user(username='operador', password='senha-de-teste')

    def paginas(self):
        yield 'home pública', self.client.get(reverse('public:home')).content.decode()
        self.client.login(username='operador', password='senha-de-teste')
        yield 'painel interno', self.client.get(reverse('dashboard:index')).content.decode()

    def test_o_grupo_e_entregue_visivel_nas_duas_areas(self):
        for pagina, html in self.paginas():
            with self.subTest(pagina=pagina):
                grupo = re.search(r'<fieldset[^>]*data-leitura[^>]*>', html)
                self.assertIsNotNone(grupo, 'o grupo de leitura não foi entregue')
                self.assertNotIn('hidden', grupo.group())

    def test_o_botao_de_ler_e_entregue_habilitado(self):
        """Botão desabilitado sai da ordem de tabulação e some do leitor de tela."""
        html = self.client.get(reverse('public:home')).content.decode()
        botao = re.search(r'<button[^>]*data-leitura-acao="ler"[^>]*>', html)
        self.assertIsNotNone(botao)
        self.assertNotIn('disabled', botao.group())

    def test_o_botao_de_parar_tambem_nasce_escondido(self):
        html = self.client.get(reverse('public:home')).content.decode()
        botao = re.search(r'<button[^>]*data-leitura-acao="parar"[^>]*>', html)
        self.assertIsNotNone(botao)
        self.assertIn('hidden', botao.group())

    def test_o_estado_da_leitura_e_anunciado(self):
        """É por aqui que a falha de síntese chega a quem não vê a tela."""
        html = self.client.get(reverse('public:home')).content.decode()
        estado = re.search(r'<p[^>]*data-leitura-estado[^>]*>', html)
        self.assertIsNotNone(estado)
        self.assertIn('aria-live="polite"', estado.group())


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

    def test_logotipo_da_area_interna_leva_a_home_mesmo_autenticado(self):
        """
        O logotipo apontava para o próprio painel quando a pessoa estava logada —
        clicar nele em /sistema/ recarregava /sistema/. Convenção de qualquer
        site: o logotipo volta ao início.
        """
        self.client.login(username='operador', password='senha-de-teste')
        html = self.client.get(reverse('dashboard:index')).content.decode()
        marca = re.search(r'<a class="navbar-brand"[^>]*>', html)
        self.assertIsNotNone(marca)
        self.assertIn(f'href="{reverse("public:home")}"', marca.group())

    def test_barra_superior_tem_caminho_de_volta_ao_painel(self):
        """
        O menu lateral some no celular. A barra superior é o único caminho de
        volta ao painel a partir de mutirões, relatórios e perfil — antes ela
        oferecia "Site Público", que o logotipo já cobre.
        """
        self.client.login(username='operador', password='senha-de-teste')
        html = self.client.get(reverse('events:lista')).content.decode()
        barra = re.search(r'<nav class="navbar.*?</nav>', html, re.S).group()
        self.assertIn(f'href="{reverse("dashboard:index")}"', barra)
        self.assertIn('Painel', barra)
        self.assertNotIn('Site Público', barra)

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


class NenhumCssVazandoComoTextoTest(TestCase):
    """
    Regra de CSS fora de <style> aparece como texto na página. Aconteceu de
    verdade: as regras dos filtros e do mapa foram inseridas depois do
    </style> e ficaram visíveis no topo da página de Ações. Este teste remove
    os blocos <style> e <script> e procura o que sobrou com cara de CSS.
    """

    def test_paginas_publicas_nao_exibem_css_como_texto(self):
        for pagina in ('public:home', 'public:sobre', 'public:acoes', 'public:contato',
                       'users:login', 'users:cadastro'):
            with self.subTest(pagina=pagina):
                html = self.client.get(reverse(pagina)).content.decode()
                visivel = re.sub(r'<style\b.*?</style>', '', html, flags=re.S)
                visivel = re.sub(r'<script\b.*?</script>', '', visivel, flags=re.S)
                vazamento = re.search(r'[.#][\w-]+\s*\{[^}]*;[^}]*\}', visivel)
                self.assertIsNone(
                    vazamento,
                    f'CSS fora de <style>: {vazamento.group()[:80] if vazamento else ""}',
                )


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


class TarjaAcademicaTest(TestCase):
    """
    A tarja que identifica a disciplina vive copiada nos dois base.html.

    Ela ficou um semestre inteiro anunciando o Projeto Integrador I depois
    que o projeto já era o II, e passou despercebida porque nada a olhava.
    Como é texto duplicado em dois arquivos, o modo de errar é corrigir um e
    esquecer o outro — então o teste compara os dois em vez de só procurar a
    frase certa em cada um.
    """

    DISCIPLINA = 'Projeto Integrador em Computação II - DRP14 - Turma 001'

    def setUp(self):
        CustomUser.objects.create_user(username='operador', password='senha-de-teste')

    def tarja(self, html):
        achado = re.search(
            r'<div class="disclaimer-univesp">(.*?)</div>', html, re.S,
        )
        self.assertIsNotNone(achado, 'página sem a tarja acadêmica')
        return re.sub(r'\s+', ' ', achado.group(1)).strip()

    def test_a_tarja_nomeia_a_disciplina_atual_nas_duas_areas(self):
        publica = self.tarja(self.client.get(reverse('public:home')).content.decode())
        self.client.login(username='operador', password='senha-de-teste')
        interna = self.tarja(self.client.get(reverse('dashboard:index')).content.decode())

        for area, texto in (('pública', publica), ('interna', interna)):
            with self.subTest(area=area):
                self.assertIn(self.DISCIPLINA, texto)

        self.assertEqual(
            publica, interna,
            'as duas tarjas divergiram — corrigir uma sem a outra é o erro clássico aqui',
        )

    def test_a_tarja_avisa_que_os_dados_sao_simulados(self):
        """O banco é semeado por populate_demo; o aviso é o que torna isso honesto."""
        texto = self.tarja(self.client.get(reverse('public:home')).content.decode())
        self.assertIn('FICTÍCIOS', texto)


class InscricaoSemLoginTest(TestCase):
    """
    A inscrição pública: participar sem criar conta.

    Era a barreira central do projeto — quem via um mutirão no site e queria
    ir era mandado para a tela de login, e o cadastro é onde a maioria
    desiste. Estes testes cobrem o caminho sem JavaScript, que é o que
    precisa funcionar sempre.
    """

    def setUp(self):
        self.evento = cria_evento(vagas=3)
        self.url = reverse('public:mutirao', args=[self.evento.pk])

    def dados(self, **troca):
        base = {
            'nome': 'Marina Albuquerque',
            'email': 'marina@example.com',
            'telefone': '(11) 98100-0001',
            'sobrenome_do_meio': '',
        }
        base.update(troca)
        return base

    def test_a_pagina_abre_sem_login_e_traz_o_formulario(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        html = resposta.content.decode()
        self.assertIn('name="nome"', html)
        self.assertIn('name="email"', html)

    def test_a_pagina_mostra_o_endereco_e_nao_coordenadas(self):
        """Pessoas em cidades se encontram por endereço."""
        evento = cria_evento(
            local='Praça do Campo Limpo, 200',
            latitude=Decimal('-23.6512'), longitude=Decimal('-46.7580'),
        )
        html = self.client.get(reverse('public:mutirao', args=[evento.pk])).content.decode()

        self.assertIn('Praça do Campo Limpo, 200', html)
        self.assertNotIn('-23.6512', html)
        self.assertNotIn('-46.7580', html)

    def test_inscricao_grava_e_redireciona(self):
        resposta = self.client.post(self.url, self.dados())

        self.assertRedirects(resposta, self.url)
        inscricao = InscricaoPublica.objects.get()
        self.assertEqual(inscricao.nome, 'Marina Albuquerque')
        self.assertEqual(inscricao.event, self.evento)

    def test_a_confirmacao_sobrevive_ao_redirecionamento(self):
        """Padrão POST-redirect-GET: recarregar não pode reenviar a inscrição."""
        self.client.post(self.url, self.dados())

        html = self.client.get(self.url).content.decode()
        self.assertIn('Inscrição confirmada, Marina', html)

        # A mensagem é consumida: não gruda na página para sempre.
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('Inscrição confirmada', html)

    def test_email_repetido_no_mesmo_mutirao_e_recusado(self):
        self.client.post(self.url, self.dados())
        resposta = self.client.post(self.url, self.dados(nome='Outra pessoa'))

        self.assertEqual(InscricaoPublica.objects.count(), 1)
        self.assertContains(resposta, 'já está inscrito', status_code=400)

    def test_email_repetido_ignora_maiusculas(self):
        """Sem normalizar, 'Ana@X.com' e 'ana@x.com' passariam como duas pessoas."""
        self.client.post(self.url, self.dados(email='ana@example.com'))
        self.client.post(self.url, self.dados(email='Ana@Example.COM'))

        self.assertEqual(InscricaoPublica.objects.count(), 1)

    def test_o_mesmo_email_pode_se_inscrever_em_outro_mutirao(self):
        outro = cria_evento(titulo='Outro mutirão')
        self.client.post(self.url, self.dados())
        self.client.post(reverse('public:mutirao', args=[outro.pk]), self.dados())

        self.assertEqual(InscricaoPublica.objects.count(), 2)

    def test_armadilha_preenchida_nao_grava(self):
        resposta = self.client.post(self.url, self.dados(sobrenome_do_meio='robô'))

        self.assertEqual(InscricaoPublica.objects.count(), 0)
        self.assertEqual(resposta.status_code, 400)

    def test_mutirao_lotado_recusa(self):
        for i in range(3):
            InscricaoPublica.objects.create(
                event=self.evento, nome=f'Pessoa {i}', email=f'p{i}@example.com',
            )

        resposta = self.client.post(self.url, self.dados())

        self.assertEqual(InscricaoPublica.objects.filter(email='marina@example.com').count(), 0)
        self.assertContains(resposta, 'vagas', status_code=400)

    def test_mutirao_ja_realizado_nao_aceita_inscricao(self):
        passado = cria_evento(
            titulo='Mutirão antigo', status='realizado',
            data=date.today() - timedelta(days=30),
        )
        url = reverse('public:mutirao', args=[passado.pk])

        self.assertNotContains(self.client.get(url), 'name="email"')
        self.client.post(url, self.dados())
        self.assertEqual(InscricaoPublica.objects.count(), 0)

    def test_mutirao_com_data_vencida_nao_aceita_inscricao(self):
        """Planejado mas já passou: a agenda esconde, a página também fecha."""
        vencido = cria_evento(
            titulo='Mutirão esquecido na agenda',
            data=date.today() - timedelta(days=1),
        )

        self.client.post(reverse('public:mutirao', args=[vencido.pk]), self.dados())
        self.assertEqual(InscricaoPublica.objects.count(), 0)

    def test_nome_e_email_sao_obrigatorios(self):
        resposta = self.client.post(self.url, self.dados(nome='', email=''))

        self.assertEqual(InscricaoPublica.objects.count(), 0)
        self.assertEqual(resposta.status_code, 400)


class InscricaoPorFetchTest(TestCase):
    """O caminho com JavaScript: mesmo endereço, mesma regra, resposta em JSON."""

    def setUp(self):
        self.evento = cria_evento(vagas=2)
        self.url = reverse('public:mutirao', args=[self.evento.pk])
        self.dados = {
            'nome': 'Rafael Toledo', 'email': 'rafael@example.com',
            'telefone': '', 'sobrenome_do_meio': '',
        }

    def test_sucesso_devolve_json_e_grava(self):
        resposta = self.client.post(self.url, self.dados, HTTP_ACCEPT='application/json')

        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.json()
        self.assertTrue(corpo['ok'])
        self.assertIn('Rafael', corpo['mensagem'])
        self.assertEqual(InscricaoPublica.objects.count(), 1)

    def test_erro_devolve_json_com_o_campo_recusado(self):
        self.client.post(self.url, self.dados, HTTP_ACCEPT='application/json')
        resposta = self.client.post(self.url, self.dados, HTTP_ACCEPT='application/json')

        self.assertEqual(resposta.status_code, 400)
        corpo = resposta.json()
        self.assertFalse(corpo['ok'])
        self.assertIn('email', corpo['erros'])

    def test_a_pagina_carrega_o_modulo_de_inscricao(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('js/inscricao.js', html)

    def test_a_pagina_nao_tem_comportamento_embutido_na_marcacao(self):
        html = self.client.get(self.url).content.decode()
        self.assertEqual(re.findall(r'\son[a-z]+\s*=\s*"', html), [])

    def test_o_formulario_funciona_sem_javascript(self):
        """
        O enriquecimento é progressivo: a marcação precisa trazer method,
        action e o botão de envio, para o navegador dar conta sozinho.
        """
        html = self.client.get(self.url).content.decode()

        self.assertIn('method="post"', html)
        self.assertIn(f'action="{self.url}"', html)
        self.assertIn('type="submit"', html)


class ArmadilhaAcessivelTest(TestCase):
    """
    A armadilha de robô não pode virar armadilha de pessoa.

    Esconder um campo só com CSS deixaria ele no caminho de quem navega por
    teclado ou leitor de tela — que é o oposto do que o site se propõe.
    """

    def setUp(self):
        self.html = self.client.get(
            reverse('public:mutirao', args=[cria_evento().pk])
        ).content.decode()

    def test_o_campo_sai_da_ordem_de_tabulacao_e_do_leitor(self):
        campo = re.search(r'<input[^>]*name="sobrenome_do_meio"[^>]*>', self.html)
        self.assertIsNotNone(campo, 'a armadilha sumiu do formulário')
        marcacao = campo.group(0)

        self.assertIn('tabindex="-1"', marcacao)
        self.assertIn('aria-hidden="true"', marcacao)
        self.assertNotIn('type="hidden"', marcacao)
