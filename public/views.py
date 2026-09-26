from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from events.models import Event
from impact.models import ImpactReport


def home(request):
    """Página inicial pública da organização."""
    # Estatísticas reais para exibição pública
    stats = ImpactReport.objects.aggregate(
        total_lixo=Sum('lixo_kg'),
        total_sacos=Sum('sacos_coletados'),
    )
    total_mutiroes = Event.objects.filter(status='realizado').count()
    total_bairros = Event.objects.filter(status='realizado').values('bairro').distinct().count()

    # Últimas ações realizadas (máx. 3)
    ultimas_acoes = Event.objects.filter(
        status='realizado'
    ).select_related('impact_report').order_by('-data')[:3]

    # Próximos mutirões
    proximos = Event.objects.filter(
        status='planejado',
        data__gte=timezone.localdate(),
    ).order_by('data')[:3]

    context = {
        'total_mutiroes': total_mutiroes,
        'total_bairros': total_bairros,
        'total_lixo': stats['total_lixo'] or 0,
        'total_sacos': stats['total_sacos'] or 0,
        'ultimas_acoes': ultimas_acoes,
        'proximos': proximos,
    }
    return render(request, 'public/home.html', context)


def sobre(request):
    """Página Sobre o projeto."""
    return render(request, 'public/sobre.html')


def acoes(request):
    """Página pública de todas as ações realizadas."""
    acoes_realizadas = Event.objects.filter(
        status='realizado'
    ).select_related('impact_report').order_by('-data')

    # Só o que ainda vai acontecer: sem o filtro de data, um mutirão
    # planejado que já passou continuava listado como "próximo".
    #
    # localdate() e não now().date(): o segundo devolve a data em UTC, e
    # depois das 21h em São Paulo já é o dia seguinte lá — o mutirão de
    # hoje sumia da lista no fim da tarde.
    proximos = Event.objects.filter(
        status='planejado',
        data__gte=timezone.localdate(),
    ).order_by('data')[:6]

    context = {
        'acoes_realizadas': acoes_realizadas,
        'proximos': proximos,
    }
    return render(request, 'public/acoes.html', context)


def contato(request):
    """Página de contato e como participar."""
    return render(request, 'public/contato.html')
