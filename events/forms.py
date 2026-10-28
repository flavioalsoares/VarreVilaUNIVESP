from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Event, SugestaoDeLocal


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


class SugestaoDeLocalForm(forms.ModelForm):
    """
    Formulário de sugestão de local — endereço, nunca coordenada.

    Quem vê o problema na rua sabe o endereço, não a latitude. Converter
    endereço em ponto no mapa é trabalho da coordenação, depois de aceitar a
    sugestão; pedir coordenada aqui afastaria justamente quem tem a
    informação.
    """

    class Meta:
        model = SugestaoDeLocal
        fields = ['local', 'bairro', 'ponto_de_referencia', 'motivo']
        widgets = {
            'local': forms.TextInput(attrs={'placeholder': 'Rua, número ou trecho'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Bairro ou distrito'}),
            'ponto_de_referencia': forms.TextInput(
                attrs={'placeholder': 'Em frente à escola, ao lado do mercado…'}),
            'motivo': forms.Textarea(
                attrs={'rows': 4,
                       'placeholder': 'Descreva o que acontece no local: entulho, lixo acumulado, '
                                      'mato alto, há quanto tempo…'}),
        }
        help_texts = {
            'ponto_de_referencia': 'Opcional. Ajuda a equipe a achar o lugar.',
            'motivo': 'Quanto mais concreto, mais fácil planejar o mutirão.',
        }

    def __init__(self, *args, **kwargs):
        # O autor não vem do formulário: vem da sessão, na view. Guardado aqui
        # só para a checagem de sugestão repetida.
        self.autor = kwargs.pop('autor', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('local'), Column('bairro')),
            'ponto_de_referencia',
            'motivo',
            Submit('submit', 'Enviar sugestão', css_class='btn btn-success w-100 mt-2'),
        )

    def clean_motivo(self):
        motivo = self.cleaned_data['motivo'].strip()
        if len(motivo) < 15:
            raise forms.ValidationError(
                'Conte um pouco mais sobre o local — a equipe precisa entender o problema '
                'para planejar o mutirão.'
            )
        return motivo

    def clean(self):
        dados = super().clean()
        local, bairro = dados.get('local'), dados.get('bairro')
        # Só olha as sugestões do próprio autor: avisar que outra pessoa já
        # sugeriu aquele endereço entregaria a quem não é da equipe um dado
        # que só a equipe pode ver.
        if self.autor and local and bairro:
            repetida = SugestaoDeLocal.objects.filter(
                sugerido_por=self.autor,
                local__iexact=local.strip(),
                bairro__iexact=bairro.strip(),
                status__in=('nova', 'em_analise'),
            )
            if repetida.exists():
                raise forms.ValidationError(
                    'Você já sugeriu este local e a equipe ainda está avaliando.'
                )
        return dados
