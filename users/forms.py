from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import CustomUser


class CadastroForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='Nome')
    last_name = forms.CharField(max_length=100, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    bairro = forms.CharField(max_length=100, required=False, label='Bairro')

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'telefone', 'bairro', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name'), Column('last_name')),
            'username',
            'email',
            Row(Column('telefone'), Column('bairro')),
            'password1',
            'password2',
            Submit('submit', 'Cadastrar', css_class='btn btn-success w-100 mt-2')
        )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Entrar', css_class='btn btn-success w-100 mt-2')
        )
