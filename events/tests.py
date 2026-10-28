from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser

from .models import Event, InscricaoPublica, Participation, SugestaoDeLocal


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


class InscricaoPublicaNoAdminTest(TestCase):
    """
    A equipe precisa poder apagar uma inscrição.

    A tela do mutirão só lista. Sem registro no admin, remover um engano,
    uma inscrição de teste ou atender um pedido de remoção exigiria mexer no
    banco à mão.
    """

    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            username='super', password='senha-de-teste', email='super@example.com',
        )
        self.inscricao = InscricaoPublica.objects.create(
            event=cria_evento(), nome='Engano', email='engano@example.com',
        )
        self.client.login(username='super', password='senha-de-teste')

    def test_a_lista_aparece_no_admin(self):
        resposta = self.client.get('/admin/events/inscricaopublica/')

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'engano@example.com')

    def test_da_para_apagar_pelo_admin(self):
        self.client.post(
            f'/admin/events/inscricaopublica/{self.inscricao.pk}/delete/',
            {'post': 'yes'},
        )

        self.assertFalse(
            InscricaoPublica.objects.filter(pk=self.inscricao.pk).exists()
        )


class SugestaoDeLocalTest(TestCase):
    """
    Sugerir um local é de quem tem conta; ler as sugestões é da equipe.

    As duas metades da regra importam. Qualquer voluntário aponta um ponto que
    precisa de mutirão, porque é ele que mora na rua; mas o que foi registrado
    só aparece para a equipe administrativa — nem o site público, nem os
    outros voluntários, nem quem escreveu a sugestão a vê de novo.
    """

    DADOS = {
        'local': 'Rua das Acácias, 200',
        'bairro': 'Ermelino Matarazzo',
        'ponto_de_referencia': 'Ao lado da padaria',
        'motivo': 'Entulho acumulado na esquina há três semanas.',
    }

    def setUp(self):
        self.voluntario = CustomUser.objects.create_user(
            username='vizinho', password='senha-de-teste', perfil='voluntario')
        self.outro = CustomUser.objects.create_user(
            username='outro', password='senha-de-teste', perfil='voluntario')
        self.admin = CustomUser.objects.create_user(
            username='coordenacao', password='senha-de-teste', perfil='admin')

    def entra(self, usuario):
        self.client.login(username=usuario.username, password='senha-de-teste')

    # ─── Quem pode sugerir ──────────────────────────────────────────────

    def test_visitante_sem_conta_nao_alcanca_o_formulario(self):
        resposta = self.client.get(reverse('events:sugerir_local'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)

    def test_voluntario_abre_o_formulario(self):
        self.entra(self.voluntario)
        resposta = self.client.get(reverse('events:sugerir_local'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'name="local"')
        self.assertContains(resposta, 'name="motivo"')

    def test_formulario_pede_endereco_e_nao_coordenada(self):
        """Quem vê o problema na rua sabe o endereço, não a latitude."""
        self.entra(self.voluntario)
        html = self.client.get(reverse('events:sugerir_local')).content.decode()
        self.assertNotIn('name="latitude"', html)
        self.assertNotIn('name="longitude"', html)

    def test_sugestao_grava_com_o_autor_e_status_inicial(self):
        self.entra(self.voluntario)
        resposta = self.client.post(reverse('events:sugerir_local'), self.DADOS)
        self.assertEqual(resposta.status_code, 302)
        sugestao = SugestaoDeLocal.objects.get()
        self.assertEqual(sugestao.sugerido_por, self.voluntario)
        self.assertEqual(sugestao.status, 'nova')
        self.assertEqual(sugestao.local, 'Rua das Acácias, 200')

    def test_a_confirmacao_e_uma_mensagem_e_nao_uma_lista(self):
        """Depois de enviada, a sugestão pertence à equipe — nem o autor a revê."""
        self.entra(self.voluntario)
        resposta = self.client.post(reverse('events:sugerir_local'), self.DADOS, follow=True)
        self.assertContains(resposta, 'Sugestão enviada')
        self.assertNotContains(resposta, self.DADOS['motivo'])

    def test_motivo_curto_demais_e_recusado(self):
        self.entra(self.voluntario)
        self.client.post(reverse('events:sugerir_local'), {**self.DADOS, 'motivo': 'tem lixo'})
        self.assertEqual(SugestaoDeLocal.objects.count(), 0)

    def test_mesma_pessoa_nao_sugere_o_mesmo_local_duas_vezes(self):
        self.entra(self.voluntario)
        self.client.post(reverse('events:sugerir_local'), self.DADOS)
        self.client.post(reverse('events:sugerir_local'), self.DADOS)
        self.assertEqual(SugestaoDeLocal.objects.count(), 1)

    def test_outra_pessoa_pode_apontar_o_mesmo_local(self):
        """Dois moradores reclamando do mesmo ponto é informação, não duplicata."""
        self.entra(self.voluntario)
        self.client.post(reverse('events:sugerir_local'), self.DADOS)
        self.client.logout()
        self.entra(self.outro)
        self.client.post(reverse('events:sugerir_local'), self.DADOS)
        self.assertEqual(SugestaoDeLocal.objects.count(), 2)

    # ─── Quem pode ler ──────────────────────────────────────────────────

    def cria_sugestao(self, **campos):
        dados = {**self.DADOS, 'sugerido_por': self.voluntario}
        dados.update(campos)
        return SugestaoDeLocal.objects.create(**dados)

    def test_voluntario_nao_alcanca_a_lista_de_sugestoes(self):
        self.cria_sugestao()
        self.entra(self.voluntario)
        resposta = self.client.get(reverse('events:sugestoes'))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.url, reverse('events:lista'))

    def test_voluntario_nao_le_o_conteudo_nem_seguindo_o_redirecionamento(self):
        sugestao = self.cria_sugestao()
        self.entra(self.voluntario)
        resposta = self.client.get(reverse('events:sugestoes'), follow=True)
        self.assertNotContains(resposta, sugestao.motivo)
        self.assertNotContains(resposta, sugestao.local)

    def test_visitante_sem_conta_nao_alcanca_a_lista(self):
        self.cria_sugestao()
        resposta = self.client.get(reverse('events:sugestoes'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('users:login'), resposta.url)

    def test_equipe_administrativa_le_a_sugestao_de_outra_pessoa(self):
        sugestao = self.cria_sugestao()
        self.entra(self.admin)
        resposta = self.client.get(reverse('events:sugestoes'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, sugestao.local)
        self.assertContains(resposta, sugestao.motivo)
        self.assertContains(resposta, 'vizinho')

    def test_filtro_por_andamento(self):
        self.cria_sugestao(status='nova')
        self.cria_sugestao(local='Outro ponto', status='aceita')
        self.entra(self.admin)
        resposta = self.client.get(reverse('events:sugestoes'), {'status': 'aceita'})
        self.assertContains(resposta, 'Outro ponto')
        self.assertNotContains(resposta, 'Rua das Acácias, 200')

    # ─── Quem pode avaliar ──────────────────────────────────────────────

    def test_equipe_muda_o_andamento_e_registra_a_resposta(self):
        sugestao = self.cria_sugestao()
        self.entra(self.admin)
        self.client.post(reverse('events:avaliar_sugestao', args=[sugestao.pk]),
                         {'status': 'aceita', 'resposta_da_equipe': 'Entrou no calendário.'})
        sugestao.refresh_from_db()
        self.assertEqual(sugestao.status, 'aceita')
        self.assertEqual(sugestao.resposta_da_equipe, 'Entrou no calendário.')

    def test_voluntario_nao_avalia(self):
        sugestao = self.cria_sugestao()
        self.entra(self.voluntario)
        self.client.post(reverse('events:avaliar_sugestao', args=[sugestao.pk]),
                         {'status': 'aceita'})
        sugestao.refresh_from_db()
        self.assertEqual(sugestao.status, 'nova')

    def test_andamento_invalido_nao_passa(self):
        sugestao = self.cria_sugestao()
        self.entra(self.admin)
        self.client.post(reverse('events:avaliar_sugestao', args=[sugestao.pk]),
                         {'status': 'arquivada'})
        sugestao.refresh_from_db()
        self.assertEqual(sugestao.status, 'nova')

    def test_avaliacao_nao_acontece_por_get(self):
        """Mudança de estado por link seria vulnerável a clique de terceiro."""
        sugestao = self.cria_sugestao()
        self.entra(self.admin)
        resposta = self.client.get(reverse('events:avaliar_sugestao', args=[sugestao.pk]),
                                   {'status': 'aceita'})
        self.assertEqual(resposta.status_code, 405)
        sugestao.refresh_from_db()
        self.assertEqual(sugestao.status, 'nova')

    # ─── O que cada um vê na navegação ──────────────────────────────────

    def test_todo_mundo_logado_ve_o_atalho_para_sugerir(self):
        for usuario in (self.voluntario, self.admin):
            with self.subTest(usuario=usuario.username):
                self.client.logout()
                self.entra(usuario)
                html = self.client.get(reverse('dashboard:index')).content.decode()
                self.assertIn(reverse('events:sugerir_local'), html)

    def test_so_a_equipe_ve_o_atalho_para_a_lista(self):
        self.entra(self.voluntario)
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertNotIn(reverse('events:sugestoes'), html)

        self.client.logout()
        self.entra(self.admin)
        html = self.client.get(reverse('dashboard:index')).content.decode()
        self.assertIn(reverse('events:sugestoes'), html)

    def test_o_painel_avisa_a_equipe_quantas_sugestoes_esperam(self):
        self.cria_sugestao()
        self.cria_sugestao(local='Outro ponto', status='em_analise')
        self.cria_sugestao(local='Ponto resolvido', status='aceita')
        self.entra(self.admin)
        resposta = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resposta.context['sugestoes_em_aberto'], 2)
        self.assertContains(resposta, 'esperando avaliação')

    def test_o_painel_do_voluntario_nao_conta_sugestao_alguma(self):
        self.cria_sugestao()
        self.entra(self.voluntario)
        resposta = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resposta.context['sugestoes_em_aberto'], 0)
        self.assertNotContains(resposta, 'esperando avaliação')
