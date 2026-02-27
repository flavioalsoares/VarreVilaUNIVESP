from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CadastroForm, LoginForm
from .models import CustomUser


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Conta criada com sucesso! Bem-vindo!')
            return redirect('dashboard:index')
    else:
        form = CadastroForm()
    return render(request, 'users/cadastro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
            return redirect('dashboard:index')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('users:login')


@login_required
def perfil_view(request):
    participacoes = request.user.participations.select_related('event').order_by('-event__data')
    return render(request, 'users/perfil.html', {'participacoes': participacoes})
