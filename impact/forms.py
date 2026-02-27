from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import ImpactReport


class ImpactReportForm(forms.ModelForm):
    class Meta:
        model = ImpactReport
        fields = ['lixo_kg', 'numero_participantes', 'sacos_coletados', 'observacoes', 'foto']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('lixo_kg'), Column('numero_participantes'), Column('sacos_coletados')),
            'observacoes',
            'foto',
            Submit('submit', 'Registrar Impacto', css_class='btn btn-success w-100 mt-2')
        )
