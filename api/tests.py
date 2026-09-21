from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from events.models import Participation
from events.tests import cria_evento
from impact.models import ImpactReport
from users.models import CustomUser


def cria_relatorio(evento, kg='100.00', pessoas=10, sacos=5):
    return ImpactReport.objects.create(
        event=evento, lixo_kg=Decimal(kg), numero_participantes=pessoas, sacos_coletados=sacos,
    )


class ListagemDeEventosTest(APITestCase):
    """GET /api/v1/eventos/ — a fonte do mapa e dos filtros do site público."""

    def setUp(self):
        self.a = cria_evento(titulo='Mutirão A', bairro='Ermelino Matarazzo',
                             data=date(2024, 3, 10), status='realizado')
        self.b = cria_evento(titulo='Mutirão B', bairro='Guaianases',
                             data=date(2025, 6, 15), status='realizado')
        self.c = cria_evento(titulo='Limpeza C', bairro='Ermelino Matarazzo',
                             data=date(2026, 12, 1), status='planejado')
        cria_relatorio(self.a, kg='320.50', pessoas=28, sacos=45)
        self.url = reverse('api:evento-list')

    def test_responde_json_paginado(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'].split(';')[0], 'application/json')
        self.assertEqual(resposta.data['count'], 3)
        self.assertIn('results', resposta.data)

    def test_ordena_do_mais_recente_para_o_mais_antigo_por_padrao(self):
        titulos = [e['titulo'] for e in self.client.get(self.url).data['results']]
        self.assertEqual(titulos, ['Limpeza C', 'Mutirão B', 'Mutirão A'])

    def test_filtra_por_status(self):
        dados = self.client.get(self.url, {'status': 'planejado'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Limpeza C'])

    def test_filtra_por_bairro(self):
        dados = self.client.get(self.url, {'bairro': 'Guaianases'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Mutirão B'])

    def test_filtra_por_ano(self):
        dados = self.client.get(self.url, {'ano': '2024'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Mutirão A'])

    def test_ano_invalido_e_ignorado_em_vez_de_quebrar(self):
        resposta = self.client.get(self.url, {'ano': 'abc'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['count'], 3)

    def test_filtros_se_combinam(self):
        dados = self.client.get(self.url, {'bairro': 'Ermelino Matarazzo', 'status': 'realizado'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Mutirão A'])

    def test_busca_em_titulo_bairro_e_local(self):
        dados = self.client.get(self.url, {'search': 'limpeza'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Limpeza C'])
        dados = self.client.get(self.url, {'search': 'guaia'}).data
        self.assertEqual([e['titulo'] for e in dados['results']], ['Mutirão B'])

    def test_ordenacao_explicita(self):
        titulos = [e['titulo'] for e in self.client.get(self.url, {'ordering': 'data'}).data['results']]
        self.assertEqual(titulos, ['Mutirão A', 'Mutirão B', 'Limpeza C'])

    def test_evento_realizado_traz_o_impacto_aninhado(self):
        evento = next(e for e in self.client.get(self.url).data['results'] if e['titulo'] == 'Mutirão A')
        self.assertEqual(evento['impacto']['lixo_kg'], 320.5)
        self.assertEqual(evento['impacto']['numero_participantes'], 28)
        self.assertEqual(evento['impacto']['sacos_coletados'], 45)

    def test_evento_sem_relatorio_traz_impacto_nulo(self):
        evento = next(e for e in self.client.get(self.url).data['results'] if e['titulo'] == 'Limpeza C')
        self.assertIsNone(evento['impacto'])

    def test_coordenadas_e_quilos_chegam_como_numero(self):
        """O mapa e a ordenação em JavaScript precisam de número, não de string."""
        self.a.latitude = Decimal('-23.500400')
        self.a.longitude = Decimal('-46.459000')
        self.a.save()
        # .json() é o corpo renderizado — o que o navegador recebe. .data ainda
        # carrega os Decimal do Python, antes de o JSONRenderer convertê-los.
        corpo = self.client.get(self.url).json()
        evento = next(e for e in corpo['results'] if e['titulo'] == 'Mutirão A')
        self.assertIsInstance(evento['latitude'], float)
        self.assertIsInstance(evento['impacto']['lixo_kg'], float)
        self.assertEqual(evento['latitude'], -23.5004)

    def test_vagas_disponiveis_descontam_as_inscricoes(self):
        for i in range(3):
            usuario = CustomUser.objects.create_user(username=f'v{i}', password='x')
            Participation.objects.create(user=usuario, event=self.c)
        evento = next(e for e in self.client.get(self.url).data['results'] if e['titulo'] == 'Limpeza C')
        self.assertEqual(evento['vagas_disponiveis'], self.c.vagas - 3)

    def test_listagem_nao_gera_uma_consulta_por_evento(self):
        """A anotação de inscritos e o select_related evitam o N+1."""
        for i in range(10):
            cria_evento(titulo=f'Extra {i}')
        with self.assertNumQueries(2):   # contagem da paginação + a listagem
            self.client.get(self.url)


class PrivacidadeDaApiTest(APITestCase):
    """Nenhum dado de pessoa sai pela API pública."""

    def setUp(self):
        self.gestor = CustomUser.objects.create_user(
            username='gestor', password='x', perfil='admin', first_name='Ana', email='ana@ong.org',
        )
        self.voluntario = CustomUser.objects.create_user(
            username='mariasantos', password='x', first_name='Maria', email='maria@email.com',
        )
        self.evento = cria_evento(titulo='Mutirão', criado_por=self.gestor)
        Participation.objects.create(user=self.voluntario, event=self.evento)

    def test_evento_nao_expoe_inscritos_nem_autor(self):
        evento = self.client.get(reverse('api:evento-detail', args=[self.evento.pk])).data
        for campo in ('participations', 'criado_por', 'inscritos', 'usuarios', 'voluntarios'):
            self.assertNotIn(campo, evento)

    def test_nenhum_nome_ou_email_aparece_na_resposta(self):
        corpo = self.client.get(reverse('api:evento-list')).content.decode()
        for sensivel in ('mariasantos', 'Maria', 'maria@email.com', 'gestor', 'ana@ong.org'):
            self.assertNotIn(sensivel, corpo)


class SomenteLeituraTest(APITestCase):

    def setUp(self):
        self.evento = cria_evento()

    def test_metodos_de_escrita_sao_recusados(self):
        lista = reverse('api:evento-list')
        detalhe = reverse('api:evento-detail', args=[self.evento.pk])
        self.assertEqual(self.client.post(lista, {'titulo': 'x'}).status_code, 405)
        self.assertEqual(self.client.put(detalhe, {'titulo': 'x'}).status_code, 405)
        self.assertEqual(self.client.patch(detalhe, {'titulo': 'x'}).status_code, 405)
        self.assertEqual(self.client.delete(detalhe).status_code, 405)

    def test_nao_exige_autenticacao(self):
        self.assertEqual(self.client.get(reverse('api:evento-list')).status_code, 200)

    def test_evento_inexistente_devolve_404(self):
        self.assertEqual(self.client.get(reverse('api:evento-detail', args=[99999])).status_code, 404)


class ResumoDeImpactoTest(APITestCase):
    """GET /api/v1/impacto/resumo/ — os números da home e do painel."""

    def setUp(self):
        a = cria_evento(titulo='A', bairro='Ermelino Matarazzo', data=date(2024, 3, 10), status='realizado')
        b = cria_evento(titulo='B', bairro='Guaianases', data=date(2024, 3, 25), status='realizado')
        c = cria_evento(titulo='C', bairro='Ermelino Matarazzo', data=date(2024, 6, 15), status='realizado')
        cria_evento(titulo='D', bairro='Itaim Paulista', status='planejado')
        cria_relatorio(a, kg='320.50', sacos=45)
        cria_relatorio(b, kg='480.00', sacos=60)
        cria_relatorio(c, kg='250.00', sacos=38)
        CustomUser.objects.create_user(username='v1', password='x', perfil='voluntario')
        CustomUser.objects.create_user(username='v2', password='x', perfil='voluntario')
        CustomUser.objects.create_user(username='chefe', password='x', perfil='admin')
        self.dados = self.client.get(reverse('api:resumo')).data

    def test_totais(self):
        self.assertEqual(self.dados['mutiroes_realizados'], 3)
        self.assertEqual(self.dados['mutiroes_planejados'], 1)
        self.assertEqual(self.dados['bairros_atendidos'], 2)
        self.assertEqual(self.dados['lixo_kg'], 1050.5)
        self.assertEqual(self.dados['sacos'], 143)

    def test_conta_so_voluntarios_e_nao_administradores(self):
        self.assertEqual(self.dados['voluntarios'], 2)

    def test_bairro_do_evento_planejado_nao_conta_como_atendido(self):
        self.assertEqual(self.dados['bairros_atendidos'], 2)

    def test_serie_mensal_agrupa_e_ordena(self):
        self.assertEqual(self.dados['por_mes'], [
            {'mes': '2024-03', 'lixo_kg': 800.5, 'mutiroes': 2},
            {'mes': '2024-06', 'lixo_kg': 250.0, 'mutiroes': 1},
        ])

    def test_sem_dados_devolve_zeros_e_lista_vazia(self):
        ImpactReport.objects.all().delete()
        dados = self.client.get(reverse('api:resumo')).data
        self.assertEqual(dados['lixo_kg'], 0)
        self.assertEqual(dados['sacos'], 0)
        self.assertEqual(dados['por_mes'], [])


class DocumentacaoDaApiTest(APITestCase):
    """O esquema OpenAPI e a interface Swagger são a evidência visível do requisito."""

    def test_esquema_openapi_e_gerado(self):
        resposta = self.client.get(reverse('api:schema'))
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.content.decode()
        self.assertIn('openapi:', corpo)
        self.assertIn('/api/v1/eventos/', corpo)
        self.assertIn('/api/v1/impacto/resumo/', corpo)

    def test_esquema_documenta_os_parametros_de_filtro(self):
        corpo = self.client.get(reverse('api:schema')).content.decode()
        for parametro in ('name: status', 'name: bairro', 'name: ano', 'name: search', 'name: ordering'):
            self.assertIn(parametro, corpo)

    def test_esquema_tipa_o_impacto_aninhado(self):
        """SerializerMethodField sem extend_schema_field viraria 'any' no Swagger."""
        corpo = self.client.get(reverse('api:schema')).content.decode()
        self.assertIn('ImpactReport', corpo)

    def test_swagger_abre(self):
        resposta = self.client.get(reverse('api:docs'))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b'swagger', resposta.content.lower())
