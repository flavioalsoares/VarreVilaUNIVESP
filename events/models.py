from django.db import models
from users.models import CustomUser


class Event(models.Model):
    STATUS_CHOICES = [
        ('planejado', 'Planejado'),
        ('realizado', 'Realizado'),
        ('cancelado', 'Cancelado'),
    ]

    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(verbose_name='Descrição')
    data = models.DateField(verbose_name='Data')
    horario = models.TimeField(verbose_name='Horário', null=True, blank=True)
    local = models.CharField(max_length=200, verbose_name='Local')
    bairro = models.CharField(max_length=100, verbose_name='Bairro')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planejado')
    vagas = models.IntegerField(default=50, verbose_name='Vagas disponíveis')
    criado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='eventos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.titulo} - {self.data}"

    def vagas_disponiveis(self):
        return self.vagas - self.participations.count()

    def tem_vagas(self):
        return self.vagas_disponiveis() > 0


class Participation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='participations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participations')
    inscrito_em = models.DateTimeField(auto_now_add=True)
    presenca_confirmada = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = 'Participação'
        verbose_name_plural = 'Participações'

    def __str__(self):
        return f"{self.user.username} → {self.event.titulo}"
