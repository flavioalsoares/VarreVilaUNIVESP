from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, verbose_name='Título')),
                ('descricao', models.TextField(verbose_name='Descrição')),
                ('data', models.DateField(verbose_name='Data')),
                ('horario', models.TimeField(blank=True, null=True, verbose_name='Horário')),
                ('local', models.CharField(max_length=200, verbose_name='Local')),
                ('bairro', models.CharField(max_length=100, verbose_name='Bairro')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('status', models.CharField(
                    choices=[('planejado', 'Planejado'), ('realizado', 'Realizado'), ('cancelado', 'Cancelado')],
                    default='planejado',
                    max_length=20,
                )),
                ('vagas', models.IntegerField(default=50, verbose_name='Vagas disponíveis')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('criado_por', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='eventos_criados',
                    to='users.customuser',
                )),
            ],
            options={
                'verbose_name': 'Evento',
                'verbose_name_plural': 'Eventos',
                'ordering': ['-data'],
            },
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inscrito_em', models.DateTimeField(auto_now_add=True)),
                ('presenca_confirmada', models.BooleanField(default=False)),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='participations',
                    to='events.event',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='participations',
                    to='users.customuser',
                )),
            ],
            options={
                'verbose_name': 'Participação',
                'verbose_name_plural': 'Participações',
                'unique_together': {('user', 'event')},
            },
        ),
    ]
