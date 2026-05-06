from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Event, Participation
from .forms import EventForm


@login_required
def lista_eventos(request):
    status = request.GET.get('status', '')
    eventos = Event.objects.all()
    if status:
        eventos = eventos.filter(status=status)
    return render(request, 'events/lista.html', {'eventos': eventos, 'status_filtro': status})


@login_required
def detalhe_evento(request, pk):
    evento = get_object_or_404(Event, pk=pk)
    inscrito = Participation.objects.filter(user=request.user, event=evento).exists()
    return render(request, 'events/detalhe.html', {'evento': evento, 'inscrito': inscrito})


@login_required
def criar_evento(request):
    if not request.user.is_admin_vv():
        messages.error(request, 'Apenas administradores podem criar eventos.')
        return redirect('events:lista')
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criado_por = request.user
            evento.save()
            messages.success(request, 'Mutirão criado com sucesso!')
            return redirect('events:detalhe', pk=evento.pk)
    else:
        form = EventForm()
    return render(request, 'events/form.html', {'form': form, 'titulo': 'Novo Mutirão'})


@login_required
def editar_evento(request, pk):
    evento = get_object_or_404(Event, pk=pk)
    if not request.user.is_admin_vv():
        messages.error(request, 'Apenas administradores podem editar eventos.')
        return redirect('events:detalhe', pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mutirão atualizado!')
            return redirect('events:detalhe', pk=pk)
    else:
        form = EventForm(instance=evento)
    return render(request, 'events/form.html', {'form': form, 'titulo': 'Editar Mutirão', 'evento': evento})


@login_required
@require_POST
def inscrever_evento(request, pk):
    evento = get_object_or_404(Event, pk=pk)
    if evento.status != 'planejado':
        messages.error(request, 'Inscrições encerradas para este evento.')
        return redirect('events:detalhe', pk=pk)
    if not evento.tem_vagas():
        messages.error(request, 'Não há mais vagas disponíveis.')
        return redirect('events:detalhe', pk=pk)
    obj, created = Participation.objects.get_or_create(user=request.user, event=evento)
    if created:
        messages.success(request, f'Inscrição confirmada para "{evento.titulo}"!')
    else:
        messages.info(request, 'Você já está inscrito neste mutirão.')
    return redirect('events:detalhe', pk=pk)


@login_required
@require_POST
def cancelar_inscricao(request, pk):
    evento = get_object_or_404(Event, pk=pk)
    Participation.objects.filter(user=request.user, event=evento).delete()
    messages.info(request, 'Inscrição cancelada.')
    return redirect('events:detalhe', pk=pk)


@login_required
@require_POST
def confirmar_presenca(request, pk, user_id):
    if not request.user.is_admin_vv():
        messages.error(request, 'Acesso negado.')
        return redirect('events:detalhe', pk=pk)
    participacao = get_object_or_404(Participation, event_id=pk, user_id=user_id)
    participacao.presenca_confirmada = not participacao.presenca_confirmada
    participacao.save()
    return redirect('events:detalhe', pk=pk)
