import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0002_inscricaopublica_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SugestaoDeLocal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('local', models.CharField(max_length=200, verbose_name='Endereço')),
                ('bairro', models.CharField(max_length=100, verbose_name='Bairro')),
                ('ponto_de_referencia', models.CharField(blank=True, max_length=200,
                                                         verbose_name='Ponto de referência')),
                ('motivo', models.TextField(verbose_name='O que acontece no local')),
                ('status', models.CharField(
                    choices=[('nova', 'Nova'), ('em_analise', 'Em análise'),
                             ('aceita', 'Aceita'), ('recusada', 'Recusada')],
                    default='nova', max_length=20)),
                ('resposta_da_equipe', models.TextField(blank=True,
                                                        verbose_name='Resposta da equipe')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('sugerido_por', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sugestoes_de_local', to=settings.AUTH_USER_MODEL,
                    verbose_name='Sugerido por')),
            ],
            options={
                'verbose_name': 'Sugestão de local',
                'verbose_name_plural': 'Sugestões de locais',
                'ordering': ['-criado_em'],
            },
        ),
    ]
