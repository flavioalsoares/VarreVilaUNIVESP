from django.shortcuts import render
from django.db.models import Sum, Count
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
    from django.utils import timezone
    proximos = Event.objects.filter(
        status='planejado',
        data__gte=timezone.now().date()
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

    proximos = Event.objects.filter(status='planejado').order_by('data')[:6]

    context = {
        'acoes_realizadas': acoes_realizadas,
        'proximos': proximos,
    }
    return render(request, 'public/acoes.html', context)


def contato(request):
    """Página de contato e como participar."""
    return render(request, 'public/contato.html')
