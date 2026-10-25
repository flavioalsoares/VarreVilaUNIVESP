"""
Formulários do site público.

O único aqui é o de inscrição em mutirão, e ele existe para ser preenchido
por quem não tem conta — o que significa que recebe POST de visitante
anônimo. Toda a validação de regra de negócio vive aqui, não no template.
"""

from django import forms
from django.utils import timezone

from events.models import InscricaoPublica


class InscricaoPublicaForm(forms.ModelForm):
    """
    Inscrição de visitante em um mutirão planejado.

    Pede o mínimo para organizar o dia: um nome para chamar e um contato
    para avisar se chover. Telefone é opcional porque exigir dois contatos
    afasta gente sem necessidade.
    """

    # Armadilha para robô de formulário: quem preenche tudo que encontra no
    # HTML cai aqui, e uma pessoa nunca vê o campo. É escondido por CSS, e
    # não por `type="hidden"`, porque campo oculto no HTML é justamente o
    # que esses robôs aprenderam a pular.
    #
    # tabindex=-1 e aria-hidden tiram o campo da ordem de tabulação e da
    # árvore de acessibilidade: sem isso a armadilha pegaria também quem
    # navega por teclado ou leitor de tela, que é o oposto do que o site
    # inteiro se propõe a fazer.
    sobrenome_do_meio = forms.CharField(
        required=False,
        label='Não preencha este campo',
        widget=forms.TextInput(attrs={
            'class': 'campo-armadilha',
            'autocomplete': 'off',
            'tabindex': '-1',
            'aria-hidden': 'true',
        }),
    )

    class Meta:
        model = InscricaoPublica
        fields = ['nome', 'email', 'telefone']
        labels = {
            'nome': 'Seu nome',
            'email': 'E-mail',
            'telefone': 'Telefone (opcional)',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'autocomplete': 'name', 'maxlength': '120',
                'placeholder': 'Como podemos te chamar',
            }),
            'email': forms.EmailInput(attrs={
                'autocomplete': 'email',
                'placeholder': 'para avisarmos se houver mudança',
            }),
            'telefone': forms.TextInput(attrs={
                'autocomplete': 'tel', 'maxlength': '20',
                'placeholder': '(11) 90000-0000',
            }),
        }

    def __init__(self, *args, evento=None, **kwargs):
        self.evento = evento
        super().__init__(*args, **kwargs)
        # required no HTML ajuda o navegador a avisar antes do envio, mas a
        # validação que vale é a do servidor — o formulário tem que estar
        # correto mesmo com o JavaScript desligado.
        self.fields['nome'].widget.attrs['required'] = 'required'
        self.fields['email'].widget.attrs['required'] = 'required'

    def clean_sobrenome_do_meio(self):
        preenchido = self.cleaned_data.get('sobrenome_do_meio', '')
        if preenchido:
            raise forms.ValidationError('Não foi possível registrar a inscrição.')
        return preenchido

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if self.evento and self.evento.inscricoes_publicas.filter(email=email).exists():
            raise forms.ValidationError(
                'Este e-mail já está inscrito neste mutirão. '
                'Não é preciso se inscrever de novo.'
            )
        return email

    def clean(self):
        dados = super().clean()
        evento = self.evento
        if evento is None:
            return dados

        if evento.status != 'planejado':
            raise forms.ValidationError(
                'Este mutirão não está aberto para inscrições.'
            )
        # localdate() e não now().date(): o segundo devolve a data em UTC, e
        # depois das 21h em São Paulo já é o dia seguinte lá — o mutirão de
        # hoje fecharia as inscrições no fim da tarde.
        if evento.data < timezone.localdate():
            raise forms.ValidationError('Este mutirão já aconteceu.')
        if not evento.tem_vagas():
            raise forms.ValidationError(
                'As vagas deste mutirão acabaram. Veja os próximos na agenda.'
            )
        return dados
