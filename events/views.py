from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Event, InscricaoPublica, Participation, SugestaoDeLocal
from .forms import EventForm, SugestaoDeLocalForm


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
    return render(request, 'events/detalhe.html', {
        'evento': evento,
        'inscrito': inscrito,
        # Quem chegou pelo site público não tem conta, então não aparece em
        # participations. Sem esta lista, a equipe organizaria o mutirão sem
        # saber de parte das pessoas que vão aparecer.
        'inscricoes_publicas': evento.inscricoes_publicas.all(),
        # O resumo do topo contava só participations e anunciava menos gente
        # do que o mutirão tem — a lotação é do evento, não da porta.
        'total_inscritos': evento.participations.count() + evento.inscricoes_publicas.count(),
    })


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


@login_required
@require_POST
def confirmar_presenca_publica(request, pk, inscricao_id):
    """
    Mesma alternância de presença, para quem se inscreveu pelo site.

    Vive separada de confirmar_presenca porque as duas inscrições apontam
    para coisas diferentes: uma tem CustomUser, a outra só tem o que a
    pessoa digitou. No dia do mutirão, para quem segura a prancheta, são a
    mesma fila — e é por isso que as duas aparecem lado a lado na tela.
    """
    if not request.user.is_admin_vv():
        messages.error(request, 'Acesso negado.')
        return redirect('events:detalhe', pk=pk)
    inscricao = get_object_or_404(InscricaoPublica, pk=inscricao_id, event_id=pk)
    inscricao.presenca_confirmada = not inscricao.presenca_confirmada
    inscricao.save()
    return redirect('events:detalhe', pk=pk)


@login_required
def sugerir_local(request):
    """
    Qualquer pessoa com conta aponta um local que precisa de mutirão.

    Depois de enviada, a sugestão não volta para quem a escreveu: é a equipe
    administrativa que a lê, avalia e responde. Por isso a confirmação é uma
    mensagem, e não uma lista — ver a lista é privilégio de quem coordena.
    """
    if request.method == 'POST':
        form = SugestaoDeLocalForm(request.POST, autor=request.user)
        if form.is_valid():
            sugestao = form.save(commit=False)
            sugestao.sugerido_por = request.user
            sugestao.save()
            messages.success(
                request,
                'Sugestão enviada! A equipe do Varre Vila vai avaliar o local '
                f'“{sugestao.local}” e considerá-lo nos próximos mutirões.'
            )
            return redirect('events:sugerir_local')
    else:
        form = SugestaoDeLocalForm(autor=request.user)
    return render(request, 'events/sugerir_local.html', {'form': form})


@login_required
def sugestoes_de_local(request):
    """Lista das sugestões — só para a equipe administrativa."""
    if not request.user.is_admin_vv():
        messages.error(request, 'Apenas a equipe administrativa vê as sugestões de locais.')
        return redirect('events:lista')

    status = request.GET.get('status', '')
    sugestoes = SugestaoDeLocal.objects.select_related('sugerido_por')
    if status:
        sugestoes = sugestoes.filter(status=status)
    return render(request, 'events/sugestoes.html', {
        'sugestoes': sugestoes,
        'status_filtro': status,
        'status_disponiveis': SugestaoDeLocal.STATUS_CHOICES,
        'total_em_aberto': SugestaoDeLocal.objects.filter(
            status__in=('nova', 'em_analise')).count(),
    })


@login_required
@require_POST
def avaliar_sugestao(request, pk):
    """Muda o andamento de uma sugestão e registra a resposta da equipe."""
    if not request.user.is_admin_vv():
        messages.error(request, 'Apenas a equipe administrativa avalia sugestões.')
        return redirect('events:lista')

    sugestao = get_object_or_404(SugestaoDeLocal, pk=pk)
    status = request.POST.get('status', '')
    if status not in dict(SugestaoDeLocal.STATUS_CHOICES):
        messages.error(request, 'Andamento inválido.')
        return redirect('events:sugestoes')

    sugestao.status = status
    sugestao.resposta_da_equipe = request.POST.get('resposta_da_equipe', '').strip()
    sugestao.save()
    messages.success(request, f'Sugestão de “{sugestao.local}” marcada como '
                              f'{sugestao.get_status_display().lower()}.')
    return redirect('events:sugestoes')
