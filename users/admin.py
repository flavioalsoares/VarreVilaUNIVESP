from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'perfil', 'bairro', 'date_joined')
    list_filter = ('perfil', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'bairro')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados da Organização', {'fields': ('perfil', 'telefone', 'bairro', 'bio', 'foto')}),
    )
