from django.contrib import admin
from .models import ImpactReport

@admin.register(ImpactReport)
class ImpactReportAdmin(admin.ModelAdmin):
    list_display = ('event', 'lixo_kg', 'numero_participantes', 'sacos_coletados', 'registrado_em')
    readonly_fields = ('registrado_em',)
