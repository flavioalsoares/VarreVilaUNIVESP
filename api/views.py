"""
Views da API pública. Tudo aqui é GET.

O conjunto de eventos é um ReadOnlyModelViewSet — o roteador só registra
list e retrieve, e qualquer POST, PUT ou DELETE recebe 405 antes de chegar
a qualquer código nosso.
"""

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event
from impact.models import ImpactReport
from users.models import CustomUser

from .serializers import EventSerializer, ResumoSerializer

PARAMETROS_DE_EVENTOS = [
    OpenApiParameter('status', str, description='planejado, realizado ou cancelado'),
    OpenApiParameter('bairro', str, description='Nome exato do bairro'),
    OpenApiParameter('ano', int, description='Ano do evento, ex. 2025'),
    OpenApiParameter('search', str, description='Busca em título, bairro e local'),
    OpenApiParameter('ordering', str, description='data, -data, titulo ou -titulo (padrão: -data)'),
]


@extend_schema(tags=['Eventos'])
class EventoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Mutirões de limpeza, com o relatório de impacto quando o evento já
    aconteceu. Não inclui inscritos nem autor — dados de pessoas ficam no
    sistema interno.
    """

    serializer_class = EventSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'bairro', 'local']
    ordering_fields = ['data', 'titulo']
    ordering = ['-data']

    def get_queryset(self):
        # `inscritos` anotado aqui poupa uma consulta por evento na listagem —
        # o serializador usa a anotação quando ela existe.
        queryset = (
            Event.objects
            .select_related('impact_report')
            .annotate(inscritos=Count('participations'))
        )

        parametros = self.request.query_params
        if parametros.get('status'):
            queryset = queryset.filter(status=parametros['status'])
        if parametros.get('bairro'):
            queryset = queryset.filter(bairro=parametros['bairro'])
        if parametros.get('ano', '').isdigit():
            queryset = queryset.filter(data__year=int(parametros['ano']))
        return queryset

    @extend_schema(parameters=PARAMETROS_DE_EVENTOS)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(tags=['Impacto'], responses=ResumoSerializer)
class ResumoView(APIView):
    """
    Totais consolidados do impacto ambiental e a série mensal de lixo
    recolhido — os mesmos números que a página inicial e o painel exibem.
    """

    def get(self, request):
        totais = ImpactReport.objects.aggregate(
            lixo_kg=Sum('lixo_kg'),
            sacos=Sum('sacos_coletados'),
        )
        realizados = Event.objects.filter(status='realizado')

        por_mes = (
            ImpactReport.objects
            .annotate(mes=TruncMonth('event__data'))
            .values('mes')
            .annotate(lixo_kg=Sum('lixo_kg'), mutiroes=Count('id'))
            .order_by('mes')
        )

        dados = {
            'mutiroes_realizados': realizados.count(),
            'mutiroes_planejados': Event.objects.filter(status='planejado').count(),
            'bairros_atendidos': realizados.values('bairro').distinct().count(),
            'voluntarios': CustomUser.objects.filter(perfil='voluntario').count(),
            'lixo_kg': float(totais['lixo_kg'] or 0),
            'sacos': totais['sacos'] or 0,
            'por_mes': [
                {
                    'mes': linha['mes'].strftime('%Y-%m'),
                    'lixo_kg': float(linha['lixo_kg'] or 0),
                    'mutiroes': linha['mutiroes'],
                }
                for linha in por_mes if linha['mes']
            ],
        }
        return Response(ResumoSerializer(dados).data)
