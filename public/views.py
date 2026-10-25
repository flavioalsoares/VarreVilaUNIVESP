from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from impact.models import ImpactReport

from .forms import InscricaoPublicaForm


def home(request):
    """Página inicial pública da organização."""
    # Estatísticas reais para exibição pública
    stats = ImpactReport.objects.aggregate(
        total_lixo=Sum('lixo_kg'),
        total_sacos=Sum('sacos_coletados'),
    )
    total_mutiroes = Event.objects.filter(status='realizado').count()
    total_bairros = Event.objects.filter(status='realizado').values('bairro').distinct().count()

    # Últimas ações realizadas (máx. 3)
    ultimas_acoes = Event.objects.filter(
        status='realizado'
    ).select_related('impact_report').order_by('-data')[:3]

    # Próximos mutirões
    proximos = Event.objects.filter(
        status='planejado',
        data__gte=timezone.localdate(),
    ).order_by('data')[:3]

    context = {
        'total_mutiroes': total_mutiroes,
        'total_bairros': total_bairros,
        'total_lixo': stats['total_lixo'] or 0,
        'total_sacos': stats['total_sacos'] or 0,
        'ultimas_acoes': ultimas_acoes,
        'proximos': proximos,
    }
    return render(request, 'public/home.html', context)


def sobre(request):
    """Página Sobre o projeto."""
    return render(request, 'public/sobre.html')


def acoes(request):
    """Página pública de todas as ações realizadas."""
    acoes_realizadas = Event.objects.filter(
        status='realizado'
    ).select_related('impact_report').order_by('-data')

    # Só o que ainda vai acontecer: sem o filtro de data, um mutirão
    # planejado que já passou continuava listado como "próximo".
    #
    # localdate() e não now().date(): o segundo devolve a data em UTC, e
    # depois das 21h em São Paulo já é o dia seguinte lá — o mutirão de
    # hoje sumia da lista no fim da tarde.
    proximos = Event.objects.filter(
        status='planejado',
        data__gte=timezone.localdate(),
    ).order_by('data')[:6]

    context = {
        'acoes_realizadas': acoes_realizadas,
        'proximos': proximos,
    }
    return render(request, 'public/acoes.html', context)


def contato(request):
    """Página de contato e como participar."""
    return render(request, 'public/contato.html')


def _pede_json(request):
    """
    O mesmo endereço atende os dois caminhos.

    Sem JavaScript o navegador envia o formulário e recarrega a página; com
    ele, inscricao.js manda o mesmo POST pedindo JSON e troca só o trecho do
    formulário. Uma view só, uma regra só — a resposta é que muda de forma.
    """
    return 'application/json' in request.headers.get('Accept', '')


def mutirao(request, pk):
    """
    Página pública de um mutirão, com inscrição sem conta.

    Até aqui, quem via um mutirão no site e queria participar era mandado
    para a tela de login. Esta página encerra esse desvio.
    """
    evento = get_object_or_404(Event.objects.select_related('impact_report'), pk=pk)

    aberto = (
        evento.status == 'planejado'
        and evento.data >= timezone.localdate()
        and evento.tem_vagas()
    )

    if request.method != 'POST':
        contexto = {
            'evento': evento,
            'aberto': aberto,
            'form': InscricaoPublicaForm(evento=evento),
            'inscritos': evento.inscricoes_publicas.count() + evento.participations.count(),
            # Sem JavaScript a confirmação chega por redirecionamento, para
            # que recarregar a página não reenvie o formulário. A mensagem
            # atravessa esse salto na sessão e é consumida aqui.
            'confirmacao': request.session.pop('inscricao_confirmada', None),
        }
        return render(request, 'public/mutirao.html', contexto)

    form = InscricaoPublicaForm(request.POST, evento=evento)

    # A vaga é conferida dentro da transação, com a linha do evento travada:
    # duas pessoas clicando no mesmo instante na última vaga passariam as
    # duas pela checagem do formulário antes de qualquer uma gravar.
    gravou = False
    if form.is_valid():
        with transaction.atomic():
            travado = Event.objects.select_for_update().get(pk=evento.pk)
            if travado.tem_vagas():
                inscricao = form.save(commit=False)
                inscricao.event = travado
                inscricao.save()
                gravou = True

    if gravou:
        mensagem = (
            f'Inscrição confirmada, {form.cleaned_data["nome"].split()[0]}! '
            f'Esperamos você no dia {evento.data.strftime("%d/%m")}.'
        )
        if _pede_json(request):
            return JsonResponse({'ok': True, 'mensagem': mensagem})
        request.session['inscricao_confirmada'] = mensagem
        return redirect(reverse('public:mutirao', args=[evento.pk]))

    if not form.errors:
        form.add_error(None, 'As vagas deste mutirão acabaram enquanto você preenchia.')

    if _pede_json(request):
        return JsonResponse({'ok': False, 'erros': form.errors}, status=400)

    contexto = {
        'evento': evento,
        'aberto': aberto,
        'form': form,
        'inscritos': evento.inscricoes_publicas.count() + evento.participations.count(),
    }
    return render(request, 'public/mutirao.html', contexto, status=400)
