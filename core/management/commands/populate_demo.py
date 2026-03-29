"""
Management command: populate_demo
Popula o banco com dados de demonstração do Varre Vila.
Seguro para rodar múltiplas vezes (usa get_or_create).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event, Participation
from impact.models import ImpactReport
from decimal import Decimal
import datetime


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # ─── Superusuário ───────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@organizacao.org',
                password='admin123',
                first_name='Administrador',
                last_name='Administrador',
                perfil='admin',
                telefone='(11) 99999-0000',
                bairro='Ermelino Matarazzo',
            )
            self.stdout.write(self.style.SUCCESS('Admin criado'))
        else:
            self.stdout.write('Admin já existe, pulando...')

        # ─── Voluntários ────────────────────────────────────────────────
        voluntarios_data = [
            ('Maria',  'Santos',   'Ermelino Matarazzo'),
            ('João',   'Oliveira', 'Guaianases'),
            ('Ana',    'Lima',     'Itaim Paulista'),
            ('Carlos', 'Pereira',  'Ermelino Matarazzo'),
            ('Lucia',  'Ferreira', 'Guaianases'),
        ]

        for i, (nome, sobrenome, bairro) in enumerate(voluntarios_data, 1):
            username = f'voluntario{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'{username}@email.com',
                    password='voluntario123',
                    first_name=nome,
                    last_name=sobrenome,
                    perfil='voluntario',
                    bairro=bairro,
                )
                self.stdout.write(self.style.SUCCESS(f'Usuário {username} criado'))

        admin = User.objects.get(username='admin')
        voluntarios = list(User.objects.filter(perfil='voluntario'))

        # ─── Eventos realizados ─────────────────────────────────────────
        eventos_realizados = [
            {
                'titulo': 'Mutirão Santa Inês - Edição 1',
                'descricao': 'Primeiro grande mutirão na Comunidade Santa Inês. Mobilizamos moradores para limpeza das ruas principais e conscientização sobre descarte correto.',
                'data': datetime.date(2024, 3, 10),
                'horario': datetime.time(8, 0),
                'local': 'Rua das Flores, 150 - Comunidade Santa Inês',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5004'),
                'longitude': Decimal('-46.4590'),
                'status': 'realizado',
                'vagas': 30,
                'lixo_kg': Decimal('320.50'),
                'participantes_real': 28,
                'sacos': 45,
                'obs': 'Excelente participação da comunidade. Foco nas ruas principais do bairro.',
            },
            {
                'titulo': 'Limpeza Córrego do Bixiga',
                'descricao': 'Ação especial nas margens do córrego. Retirada de resíduos sólidos e conscientização sobre descarte em áreas de preservação.',
                'data': datetime.date(2024, 4, 20),
                'horario': datetime.time(7, 30),
                'local': 'Avenida Rincão, próx. ponte',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5020'),
                'longitude': Decimal('-46.4610'),
                'status': 'realizado',
                'vagas': 40,
                'lixo_kg': Decimal('480.00'),
                'participantes_real': 35,
                'sacos': 60,
                'obs': 'Limpeza de margem de córrego, material pesado. Recolhidos pneus, móveis e entulho.',
            },
            {
                'titulo': 'Mutirão Guaianases',
                'descricao': 'Expansão do projeto para Guaianases com apoio da associação de moradores local.',
                'data': datetime.date(2024, 6, 15),
                'horario': datetime.time(8, 0),
                'local': 'Praça da Matriz de Guaianases',
                'bairro': 'Guaianases',
                'latitude': Decimal('-23.5500'),
                'longitude': Decimal('-46.3800'),
                'status': 'realizado',
                'vagas': 50,
                'lixo_kg': Decimal('250.00'),
                'participantes_real': 42,
                'sacos': 38,
                'obs': 'Ótima adesão dos moradores. Projeto muito bem recebido pela comunidade.',
            },
            {
                'titulo': 'Mutirão Itaim Paulista',
                'descricao': 'Parceria com escola municipal com participação de estudantes e pais na limpeza.',
                'data': datetime.date(2024, 9, 22),
                'horario': datetime.time(8, 30),
                'local': 'Emei Prof. Benedita, Rua Boa Vista, 300',
                'bairro': 'Itaim Paulista',
                'latitude': Decimal('-23.5300'),
                'longitude': Decimal('-46.3500'),
                'status': 'realizado',
                'vagas': 60,
                'lixo_kg': Decimal('190.00'),
                'participantes_real': 55,
                'sacos': 30,
                'obs': 'Participação de crianças tornando o evento especialmente significativo.',
            },
            {
                'titulo': 'Ação Novembro Verde',
                'descricao': 'Edição especial com plantio de mudas e limpeza simultâneos em parceria com ONG ambiental.',
                'data': datetime.date(2024, 11, 30),
                'horario': datetime.time(8, 0),
                'local': 'Parque linear Rincão',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5015'),
                'longitude': Decimal('-46.4570'),
                'status': 'realizado',
                'vagas': 50,
                'lixo_kg': Decimal('145.00'),
                'participantes_real': 38,
                'sacos': 22,
                'obs': 'Plantadas 30 mudas de árvores nativas além da limpeza.',
            },
        ]

        for ed in eventos_realizados:
            evento, created = Event.objects.get_or_create(
                titulo=ed['titulo'],
                defaults={
                    'descricao': ed['descricao'],
                    'data': ed['data'],
                    'horario': ed['horario'],
                    'local': ed['local'],
                    'bairro': ed['bairro'],
                    'latitude': ed['latitude'],
                    'longitude': ed['longitude'],
                    'status': ed['status'],
                    'vagas': ed['vagas'],
                    'criado_por': admin,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Evento criado: {evento.titulo}'))
                for vol in voluntarios[:3]:
                    Participation.objects.get_or_create(
                        user=vol, event=evento,
                        defaults={'presenca_confirmada': True}
                    )
                ImpactReport.objects.get_or_create(
                    event=evento,
                    defaults={
                        'lixo_kg': ed['lixo_kg'],
                        'numero_participantes': ed['participantes_real'],
                        'sacos_coletados': ed['sacos'],
                        'observacoes': ed['obs'],
                    }
                )

        # ─── Eventos futuros ────────────────────────────────────────────
        hoje = timezone.now().date()

        proximos = [
            {
                'titulo': 'Mutirão Março 2025 – Santa Inês',
                'descricao': 'Grande mutirão de limpeza na Santa Inês. Venha fazer parte dessa transformação! Levamos luvas, vassouras e sacos.',
                'data': hoje + datetime.timedelta(days=21),
                'horario': datetime.time(8, 0),
                'local': 'Rua das Palmeiras, 200 - Santa Inês',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5010'),
                'longitude': Decimal('-46.4600'),
                'vagas': 45,
            },
            {
                'titulo': 'Mutirão + Escola',
                'descricao': 'Edição especial com foco em educação ambiental. Atividades para crianças e adultos.',
                'data': hoje + datetime.timedelta(days=45),
                'horario': datetime.time(9, 0),
                'local': 'EMEF Tiradentes, Rua da Liberdade, 50',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5040'),
                'longitude': Decimal('-46.4580'),
                'vagas': 35,
            },
            {
                'titulo': 'Dia de Limpeza Guaianases II',
                'descricao': 'Segunda edição do projeto em Guaianases, com mais voluntários e mais ruas cobertas.',
                'data': hoje + datetime.timedelta(days=60),
                'horario': datetime.time(8, 0),
                'local': 'Praça Dom Pedro II, Guaianases',
                'bairro': 'Guaianases',
                'latitude': Decimal('-23.5510'),
                'longitude': Decimal('-46.3790'),
                'vagas': 50,
            },
        ]

        for ep in proximos:
            evento, created = Event.objects.get_or_create(
                titulo=ep['titulo'],
                defaults={
                    'descricao': ep['descricao'],
                    'data': ep['data'],
                    'horario': ep['horario'],
                    'local': ep['local'],
                    'bairro': ep['bairro'],
                    'latitude': ep['latitude'],
                    'longitude': ep['longitude'],
                    'status': 'planejado',
                    'vagas': ep['vagas'],
                    'criado_por': admin,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Evento planejado criado: {evento.titulo}'))
                for vol in voluntarios[:2]:
                    Participation.objects.get_or_create(user=vol, event=evento)

        self.stdout.write(self.style.SUCCESS('=== Dados de demonstração carregados com sucesso! ==='))
