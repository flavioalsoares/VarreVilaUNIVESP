from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from events.models import Event
from .models import ImpactReport
from .forms import ImpactReportForm


@login_required
def registrar_impacto(request, event_pk):
    evento = get_object_or_404(Event, pk=event_pk)
    if not request.user.is_admin_vv():
        messages.error(request, 'Apenas administradores podem registrar impacto.')
        return redirect('events:detalhe', pk=event_pk)
    if hasattr(evento, 'impact_report'):
        return redirect('impact:editar', event_pk=event_pk)
    if request.method == 'POST':
        form = ImpactReportForm(request.POST, request.FILES)
        if form.is_valid():
            relatorio = form.save(commit=False)
            relatorio.event = evento
            relatorio.save()
            evento.status = 'realizado'
            evento.save()
            messages.success(request, 'Impacto registrado com sucesso!')
            return redirect('events:detalhe', pk=event_pk)
    else:
        form = ImpactReportForm()
    return render(request, 'impact/form.html', {'form': form, 'evento': evento, 'titulo': 'Registrar Impacto'})


@login_required
def editar_impacto(request, event_pk):
    evento = get_object_or_404(Event, pk=event_pk)
    relatorio = get_object_or_404(ImpactReport, event=evento)
    if not request.user.is_admin_vv():
        messages.error(request, 'Acesso negado.')
        return redirect('events:detalhe', pk=event_pk)
    if request.method == 'POST':
        form = ImpactReportForm(request.POST, request.FILES, instance=relatorio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Relatório atualizado!')
            return redirect('events:detalhe', pk=event_pk)
    else:
        form = ImpactReportForm(instance=relatorio)
    return render(request, 'impact/form.html', {'form': form, 'evento': evento, 'titulo': 'Editar Relatório de Impacto'})


@login_required
def lista_relatorios(request):
    relatorios = ImpactReport.objects.select_related('event').order_by('-event__data')
    return render(request, 'impact/lista.html', {'relatorios': relatorios})
