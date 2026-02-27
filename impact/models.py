from django.db import models
from events.models import Event


class ImpactReport(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='impact_report')
    lixo_kg = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Lixo coletado (kg)')
    numero_participantes = models.IntegerField(verbose_name='Número de participantes')
    sacos_coletados = models.IntegerField(default=0, verbose_name='Sacos coletados')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    foto = models.ImageField(upload_to='fotos_mutirao/', blank=True, null=True, verbose_name='Foto')
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Relatório de Impacto'
        verbose_name_plural = 'Relatórios de Impacto'

    def __str__(self):
        return f"Impacto: {self.event.titulo}"
