from django.contrib import admin
from .models import Event, Participation


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 0
    readonly_fields = ('inscrito_em',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data', 'bairro', 'status', 'vagas', 'vagas_disponiveis')
    list_filter = ('status', 'bairro')
    search_fields = ('titulo', 'local', 'bairro')
    inlines = [ParticipationInline]
    readonly_fields = ('criado_em',)


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'presenca_confirmada', 'inscrito_em')
    list_filter = ('presenca_confirmada',)
