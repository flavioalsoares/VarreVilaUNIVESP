from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    PERFIL_CHOICES = [
        ('voluntario', 'Voluntário'),
        ('admin', 'Administrador'),
    ]

    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='voluntario')
    telefone = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_perfil_display()})"

    def is_admin_vv(self):
        return self.perfil == 'admin' or self.is_staff
