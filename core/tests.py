import os
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from events.models import Event, Participation
from impact.models import ImpactReport
from users.models import CustomUser


@override_settings(DEBUG=True)
class PopulateDemoTest(TestCase):
    """
    Comando que semeia os dados de demonstração.

    A partir da deduplicação, é o único caminho de povoamento do projeto — o
    entrypoint.sh passou a invocá-lo em vez de manter cópia própria em heredoc.

    O Django força DEBUG=False durante os testes, então a classe declara
    override_settings(DEBUG=True) para exercitar o caminho normal; os testes da
    trava desligam esse override explicitamente.
    """

    def test_cria_o_conjunto_completo_de_demonstracao(self):
        call_command('populate_demo', verbosity=0)

        self.assertTrue(CustomUser.objects.filter(username='admin').exists())
        self.assertEqual(CustomUser.objects.filter(perfil='voluntario').count(), 5)
        self.assertEqual(Event.objects.filter(status='realizado').count(), 5)
        self.assertEqual(Event.objects.filter(status='planejado').count(), 3)
        self.assertEqual(ImpactReport.objects.count(), 5)

    def test_admin_criado_e_superusuario(self):
        call_command('populate_demo', verbosity=0)

        admin = CustomUser.objects.get(username='admin')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_admin_vv())

    def test_mutiroes_realizados_tem_relatorio_de_impacto(self):
        call_command('populate_demo', verbosity=0)

        for evento in Event.objects.filter(status='realizado'):
            self.assertTrue(
                hasattr(evento, 'impact_report'),
                f'{evento.titulo} ficou sem relatório de impacto',
            )

    def test_eventos_planejados_ficam_no_futuro(self):
        from django.utils import timezone

        call_command('populate_demo', verbosity=0)

        hoje = timezone.now().date()
        for evento in Event.objects.filter(status='planejado'):
            self.assertGreater(evento.data, hoje)

    def test_inscricoes_sao_criadas_para_os_eventos(self):
        call_command('populate_demo', verbosity=0)
        self.assertGreater(Participation.objects.count(), 0)

    def test_rodar_duas_vezes_nao_duplica_nada(self):
        """A carga usa get_or_create — precisa ser segura em cada boot do container."""
        call_command('populate_demo', verbosity=0)
        contagens = (
            CustomUser.objects.count(),
            Event.objects.count(),
            ImpactReport.objects.count(),
            Participation.objects.count(),
        )

        call_command('populate_demo', verbosity=0)

        self.assertEqual(
            contagens,
            (
                CustomUser.objects.count(),
                Event.objects.count(),
                ImpactReport.objects.count(),
                Participation.objects.count(),
            ),
        )


class PopulateDemoTravaTest(TestCase):
    """A trava que impede semear dados de demonstração em produção por acidente."""

    @override_settings(DEBUG=False)
    def test_bloqueia_fora_de_debug(self):
        with self.assertRaises(CommandError):
            call_command('populate_demo', verbosity=0)
        self.assertEqual(CustomUser.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_libera_fora_de_debug_com_a_variavel_explicita(self):
        """É assim que o entrypoint.sh invoca o comando dentro do container."""
        with patch.dict(os.environ, {'LOAD_DEMO_DATA': '1'}):
            call_command('populate_demo', verbosity=0)
        self.assertTrue(CustomUser.objects.filter(username='admin').exists())
