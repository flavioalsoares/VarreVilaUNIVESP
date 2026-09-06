from django.test import TestCase
from django.urls import reverse

from .models import CustomUser


class CustomUserModelTest(TestCase):
    """Regras do perfil de usuário, que governam o acesso ao sistema interno."""

    def test_voluntario_nao_e_administrador(self):
        usuario = CustomUser.objects.create_user(username='ana', password='x', perfil='voluntario')
        self.assertFalse(usuario.is_admin_vv())

    def test_perfil_admin_e_administrador(self):
        usuario = CustomUser.objects.create_user(username='chefe', password='x', perfil='admin')
        self.assertTrue(usuario.is_admin_vv())

    def test_staff_do_django_e_administrador_mesmo_sendo_voluntario(self):
        usuario = CustomUser.objects.create_user(
            username='suporte', password='x', perfil='voluntario', is_staff=True
        )
        self.assertTrue(usuario.is_admin_vv())

    def test_perfil_padrao_e_voluntario(self):
        usuario = CustomUser.objects.create_user(username='novato', password='x')
        self.assertEqual(usuario.perfil, 'voluntario')

    def test_str_mostra_nome_completo_e_perfil(self):
        usuario = CustomUser.objects.create_user(
            username='msantos', password='x', first_name='Maria', last_name='Santos',
            perfil='voluntario',
        )
        self.assertEqual(str(usuario), 'Maria Santos (Voluntário)')

    def test_str_cai_no_username_quando_nao_ha_nome(self):
        usuario = CustomUser.objects.create_user(username='semnome', password='x', perfil='admin')
        self.assertEqual(str(usuario), 'semnome (Administrador)')


class CadastroViewTest(TestCase):

    def test_cadastro_cria_usuario_e_ja_autentica(self):
        resposta = self.client.post(reverse('users:cadastro'), {
            'username': 'novo',
            'first_name': 'Nova',
            'last_name': 'Pessoa',
            'email': 'nova@exemplo.org',
            'telefone': '',
            'bairro': '',
            'password1': 'mutirao-2026-forte',
            'password2': 'mutirao-2026-forte',
        })
        self.assertRedirects(resposta, reverse('dashboard:index'))
        self.assertTrue(CustomUser.objects.filter(username='novo').exists())

    def test_usuario_autenticado_nao_ve_o_formulario_de_cadastro(self):
        CustomUser.objects.create_user(username='ja', password='senha-de-teste')
        self.client.login(username='ja', password='senha-de-teste')
        resposta = self.client.get(reverse('users:cadastro'))
        self.assertRedirects(resposta, reverse('dashboard:index'))


class LoginLogoutTest(TestCase):

    def setUp(self):
        self.usuario = CustomUser.objects.create_user(username='joao', password='senha-de-teste')

    def test_login_com_credenciais_validas_leva_ao_painel(self):
        resposta = self.client.post(reverse('users:login'), {
            'username': 'joao', 'password': 'senha-de-teste',
        })
        self.assertRedirects(resposta, reverse('dashboard:index'))

    def test_login_com_senha_errada_nao_autentica(self):
        resposta = self.client.post(reverse('users:login'), {
            'username': 'joao', 'password': 'errada',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_perfil_exige_autenticacao(self):
        resposta = self.client.get(reverse('users:perfil'))
        self.assertRedirects(
            resposta, f"{reverse('users:login')}?next={reverse('users:perfil')}"
        )
