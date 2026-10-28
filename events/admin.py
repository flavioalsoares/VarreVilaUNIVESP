from django.contrib import admin
from .models import Event, InscricaoPublica, Participation, SugestaoDeLocal


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 0
    readonly_fields = ('inscrito_em',)


class InscricaoPublicaInline(admin.TabularInline):
    model = InscricaoPublica
    extra = 0
    readonly_fields = ('criado_em',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data', 'bairro', 'status', 'vagas', 'vagas_disponiveis')
    list_filter = ('status', 'bairro')
    search_fields = ('titulo', 'local', 'bairro')
    inlines = [ParticipationInline, InscricaoPublicaInline]
    readonly_fields = ('criado_em',)


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'presenca_confirmada', 'inscrito_em')
    list_filter = ('presenca_confirmada',)


@admin.register(InscricaoPublica)
class InscricaoPublicaAdmin(admin.ModelAdmin):
    """
    Inscrições feitas pelo site, sem conta.

    A tela do mutirão mostra a lista, mas só mostra: quem organiza precisa
    de um lugar para apagar uma inscrição de teste, um engano ou um pedido
    de remoção de quem se inscreveu. Sem este registro, a única saída seria
    mexer no banco.
    """

    list_display = ('nome', 'email', 'event', 'presenca_confirmada', 'criado_em')
    list_filter = ('presenca_confirmada', 'event')
    search_fields = ('nome', 'email', 'telefone')
    readonly_fields = ('criado_em',)


@admin.register(SugestaoDeLocal)
class SugestaoDeLocalAdmin(admin.ModelAdmin):
    """
    Sugestões de locais vindas de quem tem conta.

    A tela do sistema já lista e avalia; o admin existe para o que ela não
    faz: apagar um registro de teste, atender a um pedido de remoção e
    procurar por endereço em uma base que cresce.
    """

    list_display = ('local', 'bairro', 'status', 'sugerido_por', 'criado_em')
    list_filter = ('status', 'bairro')
    search_fields = ('local', 'bairro', 'ponto_de_referencia', 'motivo')
    readonly_fields = ('criado_em', 'atualizado_em')
