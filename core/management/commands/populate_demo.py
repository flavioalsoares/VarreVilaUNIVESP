"""
Management command: populate_demo
Popula o banco com dados de demonstração do Varre Vila.
Seguro para rodar múltiplas vezes (usa get_or_create).
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event, Participation
from impact.models import ImpactReport
from decimal import Decimal
import datetime


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração'

    def handle(self, *args, **kwargs):
        if not settings.DEBUG and os.environ.get('LOAD_DEMO_DATA') != '1':
            raise CommandError(
                'populate_demo bloqueado fora de DEBUG. '
                'Defina LOAD_DEMO_DATA=1 explicitamente para forçar.'
            )

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

        # ─── Correções em dados já semeados ─────────────────────────────
        # get_or_create localiza pelo título: mudar o título aqui criaria um
        # evento novo e deixaria o antigo. Bancos semeados antes da correção
        # recebem a renomeação; bancos novos nunca veem o nome antigo.
        RENOMEACOES = {
            # O Bixiga fica no centro, longe de Ermelino Matarazzo, e não tem
            # córrego a céu aberto. O Jacu atravessa o bairro até o Tietê.
            'Limpeza Córrego do Bixiga': {
                'titulo': 'Limpeza do Córrego Jacu',
                'descricao': 'Ação especial nas margens do Córrego Jacu, que atravessa o bairro até o Tietê. Retirada de resíduos sólidos e conscientização sobre descarte em áreas de preservação.',
                'local': 'Margem do Córrego Jacu, próx. à Av. Assis Ribeiro',
                'latitude': Decimal('-23.4900'),
                'longitude': Decimal('-46.4690'),
            },
        }
        for titulo_antigo, novos in RENOMEACOES.items():
            corrigidos = Event.objects.filter(titulo=titulo_antigo).update(**novos)
            if corrigidos:
                self.stdout.write(self.style.WARNING(f'Corrigido: "{titulo_antigo}" → "{novos["titulo"]}"'))

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
                'titulo': 'Limpeza do Córrego Jacu',
                'descricao': 'Ação especial nas margens do Córrego Jacu, que atravessa o bairro até o Tietê. Retirada de resíduos sólidos e conscientização sobre descarte em áreas de preservação.',
                'data': datetime.date(2024, 4, 20),
                'horario': datetime.time(7, 30),
                'local': 'Margem do Córrego Jacu, próx. à Av. Assis Ribeiro',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.4900'),
                'longitude': Decimal('-46.4690'),
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
            # ── 2025 e 2026: mais bairros da zona leste ─────────────────
            # Coordenadas aproximadas do local; dados simulados, como avisa o
            # disclaimer no topo de todas as páginas.
            {
                'titulo': 'Mutirão Parque Linear Tiquatira',
                'descricao': 'Limpeza das margens do córrego Tiquatira ao longo do parque linear, com triagem de recicláveis no local.',
                'data': datetime.date(2025, 2, 15),
                'horario': datetime.time(8, 0),
                'local': 'Parque Linear Tiquatira, Av. Gov. Carvalho Pinto',
                'bairro': 'Penha',
                'latitude': Decimal('-23.5150'),
                'longitude': Decimal('-46.5260'),
                'status': 'realizado',
                'vagas': 50,
                'lixo_kg': Decimal('410.00'),
                'participantes_real': 44,
                'sacos': 52,
                'obs': 'Grande volume de embalagens plásticas nas margens. Parceria com cooperativa de reciclagem local.',
            },
            {
                'titulo': 'Mutirão Ponte Rasa',
                'descricao': 'Ação nas ruas do entorno do terminal, com foco em pontos viciados de descarte irregular.',
                'data': datetime.date(2025, 3, 29),
                'horario': datetime.time(8, 30),
                'local': 'Praça Ponte Rasa, próx. ao terminal',
                'bairro': 'Ponte Rasa',
                'latitude': Decimal('-23.5080'),
                'longitude': Decimal('-46.4750'),
                'status': 'realizado',
                'vagas': 40,
                'lixo_kg': Decimal('265.00'),
                'participantes_real': 31,
                'sacos': 38,
                'obs': 'Dois pontos viciados eliminados; moradores pediram lixeiras.',
            },
            {
                'titulo': 'Limpeza Parque Chico Mendes',
                'descricao': 'Mutirão de limpeza e plantio no parque, em parceria com a subprefeitura.',
                'data': datetime.date(2025, 5, 10),
                'horario': datetime.time(8, 0),
                'local': 'Parque Chico Mendes, Av. Nordestina',
                'bairro': 'São Miguel Paulista',
                'latitude': Decimal('-23.4940'),
                'longitude': Decimal('-46.4360'),
                'status': 'realizado',
                'vagas': 60,
                'lixo_kg': Decimal('180.00'),
                'participantes_real': 57,
                'sacos': 27,
                'obs': 'Plantadas 40 mudas. Participação de duas escolas da região.',
            },
            {
                'titulo': 'Mutirão Vila Jacuí',
                'descricao': 'Limpeza de viela e escadaria com acúmulo de entulho, com apoio de caçamba da subprefeitura.',
                'data': datetime.date(2025, 6, 21),
                'horario': datetime.time(8, 0),
                'local': 'Rua Vitória Régia, escadaria',
                'bairro': 'Vila Jacuí',
                'latitude': Decimal('-23.4970'),
                'longitude': Decimal('-46.4270'),
                'status': 'realizado',
                'vagas': 30,
                'lixo_kg': Decimal('620.00'),
                'participantes_real': 26,
                'sacos': 35,
                'obs': 'Maior parte do peso foi entulho de construção. Escadaria liberada para passagem.',
            },
            {
                'titulo': 'Ação Várzeas do Tietê',
                'descricao': 'Retirada de resíduos na borda do parque, área de várzea sujeita a alagamento.',
                'data': datetime.date(2025, 8, 9),
                'horario': datetime.time(7, 30),
                'local': 'Parque Várzeas do Tietê, acesso pela Rua Rio Negro',
                'bairro': 'Jardim Helena',
                'latitude': Decimal('-23.4840'),
                'longitude': Decimal('-46.4100'),
                'status': 'realizado',
                'vagas': 50,
                'lixo_kg': Decimal('530.00'),
                'participantes_real': 39,
                'sacos': 61,
                'obs': 'Muitos resíduos trazidos pela última enchente. Recolhidos pneus e isopor em grande quantidade.',
            },
            {
                'titulo': 'Mutirão CEU Jambeiro',
                'descricao': 'Limpeza do entorno do CEU e oficina de compostagem para a comunidade.',
                'data': datetime.date(2025, 9, 27),
                'horario': datetime.time(9, 0),
                'local': 'CEU Jambeiro, Av. José Pinheiro Borges',
                'bairro': 'Guaianases',
                'latitude': Decimal('-23.5450'),
                'longitude': Decimal('-46.3950'),
                'status': 'realizado',
                'vagas': 45,
                'lixo_kg': Decimal('150.00'),
                'participantes_real': 48,
                'sacos': 24,
                'obs': 'Oficina de compostagem lotada. Composteira comunitária instalada no CEU.',
            },
            {
                'titulo': 'Limpeza Parque do Carmo',
                'descricao': 'Mutirão nas trilhas e no lago do parque, com equipe de resgate de resíduos na água.',
                'data': datetime.date(2025, 11, 8),
                'horario': datetime.time(8, 0),
                'local': 'Parque do Carmo, portão da Av. Afonso de Sampaio e Sousa',
                'bairro': 'Itaquera',
                'latitude': Decimal('-23.5770'),
                'longitude': Decimal('-46.4500'),
                'status': 'realizado',
                'vagas': 80,
                'lixo_kg': Decimal('290.00'),
                'participantes_real': 73,
                'sacos': 44,
                'obs': 'Maior mutirão do ano em participantes. Lago com menos resíduos flutuantes que na visita prévia.',
            },
            {
                'titulo': 'Mutirão Santa Inês - Edição 2',
                'descricao': 'Segunda grande edição na comunidade de origem do projeto, um ano depois da primeira.',
                'data': datetime.date(2026, 3, 14),
                'horario': datetime.time(8, 0),
                'local': 'Rua das Flores, 150 - Comunidade Santa Inês',
                'bairro': 'Ermelino Matarazzo',
                'latitude': Decimal('-23.5006'),
                'longitude': Decimal('-46.4588'),
                'status': 'realizado',
                'vagas': 40,
                'lixo_kg': Decimal('210.00'),
                'participantes_real': 36,
                'sacos': 31,
                'obs': 'Volume bem menor que na Edição 1: a rua se mantém limpa entre os mutirões.',
            },
            {
                'titulo': 'Mutirão Cidade Tiradentes',
                'descricao': 'Primeira ação no extremo leste, a convite de associação de moradores.',
                'data': datetime.date(2026, 4, 25),
                'horario': datetime.time(8, 30),
                'local': 'Praça dos Conjuntos, Av. dos Metalúrgicos',
                'bairro': 'Cidade Tiradentes',
                'latitude': Decimal('-23.5850'),
                'longitude': Decimal('-46.4050'),
                'status': 'realizado',
                'vagas': 50,
                'lixo_kg': Decimal('340.00'),
                'participantes_real': 41,
                'sacos': 47,
                'obs': 'Associação local quer repetir mensalmente. Ponto de partida para expansão no distrito.',
            },
            {
                'titulo': 'Limpeza Parque Linear Rio Verde',
                'descricao': 'Retirada de resíduos das margens do Rio Verde ao longo do parque linear.',
                'data': datetime.date(2026, 6, 6),
                'horario': datetime.time(8, 0),
                'local': 'Parque Linear Rio Verde, Av. Jacu-Pêssego',
                'bairro': 'Cidade Líder',
                'latitude': Decimal('-23.5600'),
                'longitude': Decimal('-46.4780'),
                'status': 'realizado',
                'vagas': 45,
                'lixo_kg': Decimal('385.00'),
                'participantes_real': 38,
                'sacos': 49,
                'obs': 'Trecho do parque sem manutenção há meses. Registradas fotos para envio à subprefeitura.',
            },
            {
                'titulo': 'Mutirão Parque Ecológico do Tietê',
                'descricao': 'Ação em parceria com a administração do parque, no núcleo Engenheiro Goulart.',
                'data': datetime.date(2026, 7, 18),
                'horario': datetime.time(8, 0),
                'local': 'Parque Ecológico do Tietê, núcleo Eng. Goulart',
                'bairro': 'Cangaíba',
                'latitude': Decimal('-23.5050'),
                'longitude': Decimal('-46.5050'),
                'status': 'realizado',
                'vagas': 70,
                'lixo_kg': Decimal('225.00'),
                'participantes_real': 62,
                'sacos': 36,
                'obs': 'Foco na borda das lagoas. Voluntários de três bairros diferentes.',
            },
            {
                'titulo': 'Mutirão Vila Matilde',
                'descricao': 'Limpeza de praça e canteiros centrais, com pintura de lixeiras pela comunidade.',
                'data': datetime.date(2026, 8, 22),
                'horario': datetime.time(8, 30),
                'local': 'Praça Alberto Ramos',
                'bairro': 'Vila Matilde',
                'latitude': Decimal('-23.5350'),
                'longitude': Decimal('-46.5220'),
                'status': 'realizado',
                'vagas': 35,
                'lixo_kg': Decimal('95.00'),
                'participantes_real': 29,
                'sacos': 16,
                'obs': 'Pouco lixo, muita pintura: doze lixeiras recuperadas pelas crianças da praça.',
            },
            {
                'titulo': 'Mutirão Sapopemba',
                'descricao': 'Limpeza da praça e do entorno da feira, com orientação sobre descarte de óleo de cozinha.',
                'data': datetime.date(2026, 9, 5),
                'horario': datetime.time(8, 0),
                'local': 'Praça Felisberto Fernandes da Silva',
                'bairro': 'Sapopemba',
                'latitude': Decimal('-23.6050'),
                'longitude': Decimal('-46.5150'),
                'status': 'realizado',
                'vagas': 45,
                'lixo_kg': Decimal('175.00'),
                'participantes_real': 40,
                'sacos': 29,
                'obs': 'Recolhidos 60 litros de óleo usado para reciclagem. Feirantes aderiram à separação.',
            },
            {
                'titulo': 'Mutirão Vila Curuçá',
                'descricao': 'Ação de fim de semana no canteiro central da avenida e nas ruas laterais.',
                'data': datetime.date(2026, 9, 19),
                'horario': datetime.time(8, 30),
                'local': 'Av. Marechal Tito, canteiro central',
                'bairro': 'Vila Curuçá',
                'latitude': Decimal('-23.5030'),
                'longitude': Decimal('-46.4100'),
                'status': 'realizado',
                'vagas': 40,
                'lixo_kg': Decimal('240.00'),
                'participantes_real': 34,
                'sacos': 41,
                'obs': 'Mutirão mais recente. Fotos e relatório enviados no mesmo dia.',
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
            {
                'titulo': 'Mutirão Lajeado',
                'descricao': 'Primeira ação no Lajeado, com limpeza da praça e cadastro de novos voluntários do bairro.',
                'data': hoje + datetime.timedelta(days=10),
                'horario': datetime.time(8, 0),
                'local': 'Praça Frei Aleixo, próx. à Av. Prof. Alípio de Barros',
                'bairro': 'Lajeado',
                'latitude': Decimal('-23.5380'),
                'longitude': Decimal('-46.3920'),
                'vagas': 40,
            },
            {
                'titulo': 'Mutirão Margem do Aricanduva',
                'descricao': 'Retirada de resíduos na margem do rio, no trecho da avenida entre duas pontes.',
                'data': hoje + datetime.timedelta(days=30),
                'horario': datetime.time(7, 30),
                'local': 'Av. Aricanduva, margem do rio, próx. ao shopping',
                'bairro': 'Aricanduva',
                'latitude': Decimal('-23.5600'),
                'longitude': Decimal('-46.5100'),
                'vagas': 55,
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
