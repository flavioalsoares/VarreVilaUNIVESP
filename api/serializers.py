"""
Serializadores da API pública.

A regra que orienta todos eles: nenhum dado de pessoa sai daqui. Eventos
carregam bairro, coordenadas e impacto ambiental; quem se inscreveu, quem
criou e quem confirmou presença ficam no sistema interno.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from events.models import Event
from impact.models import ImpactReport


class ImpactReportSerializer(serializers.ModelSerializer):
    foto = serializers.ImageField(read_only=True, use_url=True)

    class Meta:
        model = ImpactReport
        fields = ['lixo_kg', 'numero_participantes', 'sacos_coletados', 'observacoes', 'foto', 'registrado_em']
        read_only_fields = fields


class EventSerializer(serializers.ModelSerializer):
    status_nome = serializers.CharField(source='get_status_display', read_only=True)
    vagas_disponiveis = serializers.SerializerMethodField()
    impacto = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'titulo', 'descricao', 'data', 'horario', 'local', 'bairro',
            'latitude', 'longitude', 'status', 'status_nome', 'vagas',
            'vagas_disponiveis', 'impacto',
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField())
    def get_vagas_disponiveis(self, evento):
        # A view anota `inscritos` no queryset para evitar uma consulta por
        # evento; fora dela, o método do modelo continua valendo.
        inscritos = getattr(evento, 'inscritos', None)
        if inscritos is None:
            return evento.vagas_disponiveis()
        return evento.vagas - inscritos

    @extend_schema_field(ImpactReportSerializer(allow_null=True))
    def get_impacto(self, evento):
        relatorio = getattr(evento, 'impact_report', None)
        if relatorio is None:
            return None
        return ImpactReportSerializer(relatorio, context=self.context).data


class ResumoMensalSerializer(serializers.Serializer):
    mes = serializers.CharField(help_text='Ano e mês no formato AAAA-MM')
    lixo_kg = serializers.FloatField()
    mutiroes = serializers.IntegerField()


class ResumoSerializer(serializers.Serializer):
    """Totais consolidados — os mesmos números da página inicial e do painel."""

    mutiroes_realizados = serializers.IntegerField()
    mutiroes_planejados = serializers.IntegerField()
    bairros_atendidos = serializers.IntegerField()
    voluntarios = serializers.IntegerField()
    lixo_kg = serializers.FloatField()
    sacos = serializers.IntegerField()
    por_mes = ResumoMensalSerializer(many=True)
