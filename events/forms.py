from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['titulo', 'descricao', 'data', 'horario', 'local', 'bairro', 'latitude', 'longitude', 'status', 'vagas']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'horario': forms.TimeInput(attrs={'type': 'time'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'data': 'Data',
            'horario': 'Horário',
            'local': 'Endereço',
            'bairro': 'Bairro',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'status': 'Status',
            'vagas': 'Vagas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'titulo',
            'descricao',
            Row(Column('data'), Column('horario')),
            Row(Column('local'), Column('bairro')),
            Row(Column('latitude'), Column('longitude')),
            Row(Column('status'), Column('vagas')),
            Submit('submit', 'Salvar Mutirão', css_class='btn btn-success w-100 mt-2')
        )
