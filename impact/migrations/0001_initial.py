from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImpactReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lixo_kg', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Lixo coletado (kg)')),
                ('numero_participantes', models.IntegerField(verbose_name='Número de participantes')),
                ('sacos_coletados', models.IntegerField(default=0, verbose_name='Sacos coletados')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='fotos_mutirao/', verbose_name='Foto')),
                ('registrado_em', models.DateTimeField(auto_now_add=True)),
                ('event', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='impact_report',
                    to='events.event',
                )),
            ],
            options={
                'verbose_name': 'Relatório de Impacto',
                'verbose_name_plural': 'Relatórios de Impacto',
            },
        ),
    ]
