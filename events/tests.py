from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser

from .models import Event, InscricaoPublica, Participation


def cria_evento(**campos):
    """Atalho para eventos de teste: mutirão planejado, daqui a uma semana, 10 vagas."""
    dados = {
        'titulo': 'Mutirão de teste',
        'descricao': 'Limpeza da rua principal.',
        'data': date.today() + timedelta(days=7),
        'local': 'Rua das Flores, 150',
        'bairro': 'Ermelino Matarazzo',
        'status': 'planejado',
        'vagas': 10,
    }
    dados.update(campos)
    return Event.objects.create(**dados)


class EventModelTest(TestCase):
    """Regras de vagas — o que impede um mutirão de receber mais gente do que comporta."""

    def setUp(self):
        self.evento = cria_evento(vagas=2)

    def test_evento_novo_tem_todas_as_vagas_livres(self):
        self.assertEqual(self.evento.vagas_disponiveis(), 2)
        self.assertTrue(self.evento.tem_vagas())

    def test_cada_inscricao_consome_uma_vaga(self):
        usuario = CustomUser.objects.create_user(username='v1', password='x')
        Participation.objects.create(user=usuario, event=self.evento)
        self.assertEqual(self.evento.vagas_disponiveis(), 1)

    def test_evento_lotado_nao_tem_mais_vagas(self):
        for i in range(2):
            usuario = CustomUser.objects.create_user(username=f'v{i}', password='x')
            Participation.objects.create(user=usuario, event=self.evento)
        self.assertEqual(self.evento.vagas_disponiveis(), 0)
        self.assertFalse(self.evento.tem_vagas())

    def test_str_traz_titulo_e_data(self):
        self.assertEqual(str(self.evento), f'Mutirão de teste - {self.evento.data}')

    def test_ordenacao_padrao_e_da_data_mais_recente_para_a_mais_antiga(self):
        antigo = cria_evento(titulo='Antigo', data=date(2024, 1, 1))
        recente = cria_evento(titulo='Recente', data=date(2026, 12, 31))
        self.assertEqual(list(Event.objects.all())[0], recente)
        self.assertEqual(list(Event.objects.all())[-1], antigo)


class ParticipationModelTest(TestCase):

    def test_mesmo_usuario_nao_se_inscreve_duas_vezes_no_mesmo_evento(self):
        evento = cria_evento()
        usuario = CustomUser.objects.create_user(username='dup', password='x')
        Participation.objects.create(user=usuario, event=evento)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Participation.objects.create(user=usuario, event=evento)

    def test_presenca_comeca_nao_confirmada(self):
        evento = cria_evento()
        usuario = CustomUser.objects.create_user(username='pres', password='x')
        inscricao = Participation.objects.create(user=usuario, event=evento)
        self.assertFalse(inscricao.presenca_confirmada)


class EventoAcessoAnonimoTest(TestCase):
    """Hoje toda a área de eventos exige login. O PI-2 vai abrir parte disso ao público."""

    def test_lista_de_eventos_exige_login(self):
        resposta = self.client.get(reverse('events:lista'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)

    def test_detalhe_de_evento_exige_login(self):
        evento = cria_evento()
        resposta = self.client.get(reverse('events:detalhe', args=[evento.pk]))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)


class CriacaoDeEventoTest(TestCase):
    """Só administradores criam e editam mutirões."""

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='gestor', password='senha-de-teste', perfil='admin'
        )
        self.voluntario = CustomUser.objects.create_user(
            username='ajudante', password='senha-de-teste', perfil='voluntario'
        )
        self.dados = {
            'titulo': 'Mutirão Santa Inês',
            'descricao': 'Limpeza comunitária.',
            'data': (date.today() + timedelta(days=10)).isoformat(),
            'horario': '08:00',
            'local': 'Praça central',
            'bairro': 'Ermelino Matarazzo',
            'latitude': '-23.5004',
            'longitude': '-46.4590',
            'status': 'planejado',
            'vagas': 30,
        }

    def test_voluntario_nao_cria_evento(self):
        self.client.login(username='ajudante', password='senha-de-teste')
        resposta = self.client.post(reverse('events:criar'), self.dados)
        self.assertRedirects(resposta, reverse('events:lista'))
        self.assertEqual(Event.objects.count(), 0)

    def test_administrador_cria_evento_e_fica_registrado_como_autor(self):
        self.client.login(username='gestor', password='senha-de-teste')
        resposta = self.client.post(reverse('events:criar'), self.dados)
        self.assertEqual(Event.objects.count(), 1)
        evento = Event.objects.get()
        self.assertEqual(evento.criado_por, self.admin)
        self.assertRedirects(resposta, reverse('events:detalhe', args=[evento.pk]))

    def test_voluntario_nao_edita_evento(self):
        evento = cria_evento(titulo='Original')
        self.client.login(username='ajudante', password='senha-de-teste')
        self.client.post(reverse('events:editar', args=[evento.pk]), self.dados)
        evento.refresh_from_db()
        self.assertEqual(evento.titulo, 'Original')


class InscricaoEmEventoTest(TestCase):

    def setUp(self):
        self.voluntario = CustomUser.objects.create_user(
            username='ajudante', password='senha-de-teste', perfil='voluntario'
        )
        self.client.login(username='ajudante', password='senha-de-teste')

    def test_inscricao_em_evento_planejado_com_vaga(self):
        evento = cria_evento()
        self.client.post(reverse('events:inscrever', args=[evento.pk]))
        self.assertTrue(
            Participation.objects.filter(user=self.voluntario, event=evento).exists()
        )

    def test_inscricao_so_aceita_post(self):
        evento = cria_evento()
        resposta = self.client.get(reverse('events:inscrever', args=[evento.pk]))
        self.assertEqual(resposta.status_code, 405)

    def test_nao_ha_inscricao_em_evento_ja_realizado(self):
        evento = cria_evento(status='realizado')
        self.client.post(reverse('events:inscrever', args=[evento.pk]))
        self.assertEqual(Participation.objects.count(), 0)

    def test_nao_ha_inscricao_em_evento_cancelado(self):
        evento = cria_evento(status='cancelado')
        self.client.post(reverse('events:inscrever', args=[evento.pk]))
        self.assertEqual(Participation.objects.count(), 0)

    def test_nao_ha_inscricao_em_evento_lotado(self):
        evento = cria_evento(vagas=1)
        outro = CustomUser.objects.create_user(username='primeiro', password='x')
        Participation.objects.create(user=outro, event=evento)

        self.client.post(reverse('events:inscrever', args=[evento.pk]))

        self.assertEqual(evento.participations.count(), 1)
        self.assertFalse(
            Participation.objects.filter(user=self.voluntario, event=evento).exists()
        )

    def test_inscricao_repetida_nao_duplica_registro(self):
        evento = cria_evento()
        self.client.post(reverse('events:inscrever', args=[evento.pk]))
        self.client.post(reverse('events:inscrever', args=[evento.pk]))
        self.assertEqual(
            Participation.objects.filter(user=self.voluntario, event=evento).count(), 1
        )

    def test_cancelamento_remove_a_inscricao(self):
        evento = cria_evento()
        Participation.objects.create(user=self.voluntario, event=evento)
        self.client.post(reverse('events:cancelar', args=[evento.pk]))
        self.assertEqual(Participation.objects.count(), 0)


class ConfirmacaoDePresencaTest(TestCase):
    """Marcar presença é atribuição de administrador e funciona como alternância."""

    def setUp(self):
        self.evento = cria_evento()
        self.voluntario = CustomUser.objects.create_user(
            username='ajudante', password='senha-de-teste', perfil='voluntario'
        )
        self.inscricao = Participation.objects.create(
            user=self.voluntario, event=self.evento
        )

    def test_voluntario_nao_confirma_a_propria_presenca(self):
        self.client.login(username='ajudante', password='senha-de-teste')
        self.client.post(reverse(
            'events:confirmar_presenca', args=[self.evento.pk, self.voluntario.pk]
        ))
        self.inscricao.refresh_from_db()
        self.assertFalse(self.inscricao.presenca_confirmada)

    def test_administrador_confirma_e_desconfirma_presenca(self):
        CustomUser.objects.create_user(
            username='gestor', password='senha-de-teste', perfil='admin'
        )
        self.client.login(username='gestor', password='senha-de-teste')
        url = reverse(
            'events:confirmar_presenca', args=[self.evento.pk, self.voluntario.pk]
        )

        self.client.post(url)
        self.inscricao.refresh_from_db()
        self.assertTrue(self.inscricao.presenca_confirmada)

        self.client.post(url)
        self.inscricao.refresh_from_db()
        self.assertFalse(self.inscricao.presenca_confirmada)


class VagasContamAsDuasPortasTest(TestCase):
    """
    A lotação é do mutirão, não da porta por onde a pessoa entrou.

    Contar só participations fazia o site anunciar vagas que já não existiam
    e aceitar gente além do que o mutirão comporta.
    """

    def setUp(self):
        self.evento = cria_evento(vagas=4)

    def test_inscricao_publica_ocupa_vaga(self):
        InscricaoPublica.objects.create(
            event=self.evento, nome='Marina', email='marina@example.com',
        )
        self.assertEqual(self.evento.vagas_disponiveis(), 3)

    def test_as_duas_origens_somam(self):
        usuario = CustomUser.objects.create_user(username='vol', password='x')
        Participation.objects.create(user=usuario, event=self.evento)
        InscricaoPublica.objects.create(
            event=self.evento, nome='Marina', email='marina@example.com',
        )

        self.assertEqual(self.evento.vagas_disponiveis(), 2)

    def test_mutirao_lota_com_inscricoes_publicas(self):
        for i in range(4):
            InscricaoPublica.objects.create(
                event=self.evento, nome=f'Pessoa {i}', email=f'p{i}@example.com',
            )

        self.assertFalse(self.evento.tem_vagas())


class InscricaoPublicaNaTelaInternaTest(TestCase):
    """Quem organiza o mutirão precisa ver as duas listas na mesma tela."""

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='chefe', password='senha-de-teste', perfil='admin',
        )
        self.evento = cria_evento()
        self.inscricao = InscricaoPublica.objects.create(
            event=self.evento, nome='Cleide dos Santos',
            email='cleide@example.com', telefone='(11) 98100-0003',
        )
        self.client.login(username='chefe', password='senha-de-teste')

    def test_a_tela_lista_quem_veio_pelo_site(self):
        html = self.client.get(
            reverse('events:detalhe', args=[self.evento.pk])
        ).content.decode()

        self.assertIn('Cleide dos Santos', html)
        self.assertIn('cleide@example.com', html)

    def test_admin_alterna_a_presenca(self):
        url = reverse(
            'events:confirmar_presenca_publica',
            args=[self.evento.pk, self.inscricao.pk],
        )

        self.client.post(url)
        self.inscricao.refresh_from_db()
        self.assertTrue(self.inscricao.presenca_confirmada)

        self.client.post(url)
        self.inscricao.refresh_from_db()
        self.assertFalse(self.inscricao.presenca_confirmada)

    def test_quem_nao_e_admin_nao_altera_presenca(self):
        self.client.logout()
        CustomUser.objects.create_user(
            username='voluntario', password='senha-de-teste', perfil='voluntario',
        )
        self.client.login(username='voluntario', password='senha-de-teste')

        self.client.post(reverse(
            'events:confirmar_presenca_publica',
            args=[self.evento.pk, self.inscricao.pk],
        ))

        self.inscricao.refresh_from_db()
        self.assertFalse(self.inscricao.presenca_confirmada)

    def test_anonimo_nao_alcanca_a_tela_interna(self):
        self.client.logout()
        resposta = self.client.get(reverse('events:detalhe', args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 302)


class ResumoDaTelaInternaTest(TestCase):
    """
    O resumo "Inscritos / Vagas" no topo da tela do mutirão.

    Contava só participations e anunciava menos gente do que o mutirão tem.
    Quem organiza usa esse número para saber quantos kits levar.
    """

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='chefe', password='senha-de-teste', perfil='admin',
        )
        self.evento = cria_evento(vagas=40)
        Participation.objects.create(
            user=CustomUser.objects.create_user(username='vol', password='x'),
            event=self.evento,
        )
        for i in range(3):
            InscricaoPublica.objects.create(
                event=self.evento, nome=f'Pessoa {i}', email=f'p{i}@example.com',
            )
        self.client.login(username='chefe', password='senha-de-teste')

    def test_o_resumo_soma_as_duas_origens(self):
        html = self.client.get(
            reverse('events:detalhe', args=[self.evento.pk])
        ).content.decode()

        self.assertIn('4 / 40', html)


class TemplatesSemComentarioVazandoTest(TestCase):
    """
    {# #} no Django é comentário de UMA linha.

    Escrito em várias linhas, ele não comenta nada: o texto sai renderizado
    na tela. Aconteceu nesta própria tela e nenhum teste de conteúdo pegou,
    porque para o teste é só mais um texto na página.
    """

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='chefe', password='senha-de-teste', perfil='admin',
        )
        self.evento = cria_evento()
        self.client.login(username='chefe', password='senha-de-teste')

    def test_nenhuma_tela_mostra_marca_de_comentario(self):
        paginas = (
            ('events:lista', []),
            ('events:detalhe', [self.evento.pk]),
            ('dashboard:index', []),
        )
        for nome, args in paginas:
            with self.subTest(pagina=nome):
                html = self.client.get(reverse(nome, args=args)).content.decode()
                self.assertNotIn('{#', html)
                self.assertNotIn('#}', html)
