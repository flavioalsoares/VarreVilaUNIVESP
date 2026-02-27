from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from events.models import Event, Participation
from impact.models import ImpactReport
from users.models import CustomUser
import json


@login_required
def index(request):
    # Totais gerais
    total_mutiroes = Event.objects.filter(status='realizado').count()
    total_voluntarios = CustomUser.objects.filter(perfil='voluntario').count()
    total_bairros = Event.objects.filter(status='realizado').values('bairro').distinct().count()

    agregado = ImpactReport.objects.aggregate(
        total_lixo=Sum('lixo_kg'),
        total_sacos=Sum('sacos_coletados'),
    )
    total_lixo = agregado['total_lixo'] or 0
    total_sacos = agregado['total_sacos'] or 0

    # Próximos eventos
    from django.utils import timezone
    proximos = Event.objects.filter(status='planejado', data__gte=timezone.now().date()).order_by('data')[:3]

    # Dados para gráfico mensal
    mensal = (
        ImpactReport.objects
        .annotate(mes=TruncMonth('event__data'))
        .values('mes')
        .annotate(total=Sum('lixo_kg'), count=Count('id'))
        .order_by('mes')
    )

    labels = [str(m['mes'].strftime('%b/%Y')) if m['mes'] else '' for m in mensal]
    dados_lixo = [float(m['total'] or 0) for m in mensal]

    # Mapa de eventos
    eventos_mapa = Event.objects.exclude(latitude=None).exclude(longitude=None).values(
        'id', 'titulo', 'local', 'bairro', 'status', 'data',
        'latitude', 'longitude'
    )
    eventos_json = json.dumps([
        {
            'id': e['id'],
            'titulo': e['titulo'],
            'local': e['local'],
            'bairro': e['bairro'],
            'status': e['status'],
            'data': str(e['data']),
            'lat': float(e['latitude']),
            'lng': float(e['longitude']),
        }
        for e in eventos_mapa
    ])

    context = {
        'total_mutiroes': total_mutiroes,
        'total_voluntarios': total_voluntarios,
        'total_bairros': total_bairros,
        'total_lixo': total_lixo,
        'total_sacos': total_sacos,
        'proximos': proximos,
        'labels': json.dumps(labels),
        'dados_lixo': json.dumps(dados_lixo),
        'eventos_json': eventos_json,
    }
    return render(request, 'dashboard/index.html', context)
