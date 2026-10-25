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
        # Duas portas levam ao mesmo mutirão: a interna, de quem tem conta, e
        # a pública, de quem se inscreveu pelo site sem criar uma. A lotação
        # é do evento, não da porta — contar só uma delas deixava o mutirão
        # aceitar gente além do que comporta.
        return self.vagas - self.participations.count() - self.inscricoes_publicas.count()

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


class InscricaoPublica(models.Model):
    """
    Inscrição feita pelo site público, sem conta.

    Era aqui que o projeto perdia gente: quem via um mutirão no site e queria
    ir precisava primeiro criar login e senha, e o cadastro é justamente onde
    a maioria desiste. Pedir nome e um contato é o suficiente para organizar
    um mutirão de rua.

    Fica separada de Participation em vez de reaproveitá-la porque são coisas
    diferentes: Participation pertence a um CustomUser e sabe quem é a pessoa
    no sistema; esta aqui guarda apenas o que a pessoa digitou. Fundir as
    duas exigiria criar usuários fantasmas a cada inscrição.
    """

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE,
        related_name='inscricoes_publicas', verbose_name='Mutirão',
    )
    nome = models.CharField(max_length=120, verbose_name='Nome')
    email = models.EmailField(verbose_name='E-mail')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    criado_em = models.DateTimeField(auto_now_add=True)
    presenca_confirmada = models.BooleanField(default=False)

    class Meta:
        ordering = ['criado_em']
        verbose_name = 'Inscrição pública'
        verbose_name_plural = 'Inscrições públicas'
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'email'],
                name='inscricao_publica_unica_por_evento',
            ),
        ]

    def save(self, *args, **kwargs):
        # O e-mail é a chave que impede a mesma pessoa de se inscrever duas
        # vezes. Sem normalizar, "Ana@Exemplo.com" e "ana@exemplo.com"
        # passariam pela restrição como duas pessoas diferentes.
        self.email = self.email.strip().lower()
        self.nome = self.nome.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} → {self.event.titulo}'
