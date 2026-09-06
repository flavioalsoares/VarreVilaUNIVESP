/**
 * Filtros da página pública de Ações.
 *
 * O Django entrega o histórico completo em HTML — a página funciona, é
 * navegável e é indexável sem JavaScript. Este módulo assume dali em diante:
 * busca ao digitar, filtro por bairro e ano, ordenação, e sincronia do estado
 * com a URL, de modo que uma seleção vira link compartilhável e o botão Voltar
 * do navegador desfaz o filtro.
 *
 * A barra de controles nasce com o atributo hidden no template e só é revelada
 * aqui. Sem JavaScript ninguém vê um controle que não funcionaria.
 *
 * Publica 'vv:filtro-aplicado' no document a cada mudança. O mapa público e o
 * módulo de anúncios vão escutar esse evento sem conhecer este arquivo — não há
 * import entre módulos porque o armazenamento de estáticos em produção renomeia
 * os arquivos com hash e o Django não reescreve caminhos de import em JS.
 */

const ATRASO_DA_BUSCA = 200;

const ORDENACOES = {
    'data-desc': (a, b) => b.data.localeCompare(a.data),
    'data-asc': (a, b) => a.data.localeCompare(b.data),
    'lixo-desc': (a, b) => b.lixo - a.lixo,
};

const PADRAO = { busca: '', bairro: '', ano: '', ordem: 'data-desc' };

const barra = document.querySelector('[data-filtros]');
const lista = document.querySelector('[data-lista-acoes]');

if (barra && lista) {
    iniciar(barra, lista);
}

function iniciar(barra, lista) {
    const contagem = barra.querySelector('[data-contagem]');
    const botaoLimpar = barra.querySelector('[data-limpar-filtros]');
    const semResultado = document.querySelector('[data-sem-resultado]');

    const campos = {
        busca: barra.querySelector('[data-filtro="busca"]'),
        bairro: barra.querySelector('[data-filtro="bairro"]'),
        ano: barra.querySelector('[data-filtro="ano"]'),
        ordem: barra.querySelector('[data-filtro="ordem"]'),
    };

    /* As ações já estão no HTML; aqui elas viram dados para filtrar em memória,
       sem nenhuma ida ao servidor. */
    const acoes = Array.from(lista.querySelectorAll('[data-acao-linha]')).map((elemento) => ({
        elemento,
        titulo: elemento.dataset.titulo || '',
        bairro: elemento.dataset.bairro || '',
        local: elemento.dataset.local || '',
        ano: elemento.dataset.ano || '',
        data: elemento.dataset.data || '',
        lixo: Number.parseFloat(elemento.dataset.lixo) || 0,
    }));

    if (acoes.length === 0) {
        return;
    }

    preencheOpcoes(campos.bairro, valoresUnicos(acoes, 'bairro'));
    preencheOpcoes(campos.ano, valoresUnicos(acoes, 'ano').reverse());

    /* O <form> agrupa os controles para leitores de tela, mas nada é enviado
       ao servidor: o Enter na busca não deve recarregar a página. */
    barra.addEventListener('submit', (evento) => evento.preventDefault());

    barra.hidden = false;

    let estado = leEstadoDaUrl();
    escreveNosCampos(campos, estado);
    aplica(estado, { atualizarUrl: false });

    // ── eventos ──────────────────────────────────────────────────

    let temporizador = null;
    campos.busca.addEventListener('input', () => {
        window.clearTimeout(temporizador);
        temporizador = window.setTimeout(() => {
            estado = Object.assign({}, estado, { busca: campos.busca.value.trim() });
            aplica(estado);
        }, ATRASO_DA_BUSCA);
    });

    for (const nome of ['bairro', 'ano', 'ordem']) {
        campos[nome].addEventListener('change', () => {
            estado = Object.assign({}, estado, { [nome]: campos[nome].value });
            aplica(estado);
        });
    }

    botaoLimpar.addEventListener('click', () => {
        estado = Object.assign({}, PADRAO);
        escreveNosCampos(campos, estado);
        aplica(estado);
        campos.busca.focus();
    });

    /* Voltar e avançar do navegador refazem a seleção, porque o estado mora
       na URL e não só na memória da página. */
    window.addEventListener('popstate', () => {
        estado = leEstadoDaUrl();
        escreveNosCampos(campos, estado);
        aplica(estado, { atualizarUrl: false });
    });

    // ── núcleo ───────────────────────────────────────────────────

    function aplica(estado, opcoes = {}) {
        const termo = estado.busca.toLowerCase();

        const visiveis = acoes.filter((acao) => {
            const casaBusca =
                termo === '' ||
                acao.titulo.includes(termo) ||
                acao.local.includes(termo) ||
                acao.bairro.toLowerCase().includes(termo);
            const casaBairro = estado.bairro === '' || acao.bairro === estado.bairro;
            const casaAno = estado.ano === '' || acao.ano === estado.ano;
            return casaBusca && casaBairro && casaAno;
        });

        for (const acao of acoes) {
            acao.elemento.hidden = !visiveis.includes(acao);
        }

        /* Reordenar move os nós existentes: append num elemento que já está no
           documento reposiciona em vez de duplicar. */
        const comparador = ORDENACOES[estado.ordem] || ORDENACOES['data-desc'];
        for (const acao of [...visiveis].sort(comparador)) {
            lista.append(acao.elemento);
        }

        const filtrando = temAlgumFiltro(estado);
        botaoLimpar.hidden = !filtrando;
        semResultado.hidden = visiveis.length > 0;
        contagem.textContent = descreve(visiveis.length, acoes.length, filtrando);

        if (opcoes.atualizarUrl !== false) {
            gravaEstadoNaUrl(estado);
        }

        document.dispatchEvent(new CustomEvent('vv:filtro-aplicado', {
            detail: {
                visiveis: visiveis.length,
                total: acoes.length,
                filtros: Object.assign({}, estado),
                datas: visiveis.map((acao) => acao.data),
            },
        }));
    }

    // ── URL ──────────────────────────────────────────────────────

    function leEstadoDaUrl() {
        const parametros = new URLSearchParams(window.location.search);
        const ordem = parametros.get('ordem') || PADRAO.ordem;
        return {
            busca: parametros.get('busca') || '',
            bairro: parametros.get('bairro') || '',
            ano: parametros.get('ano') || '',
            ordem: ORDENACOES[ordem] ? ordem : PADRAO.ordem,
        };
    }

    function gravaEstadoNaUrl(estado) {
        const parametros = new URLSearchParams();
        for (const [chave, valor] of Object.entries(estado)) {
            if (valor && valor !== PADRAO[chave]) {
                parametros.set(chave, valor);
            }
        }
        const consulta = parametros.toString();
        window.history.pushState(
            estado,
            '',
            consulta ? `${window.location.pathname}?${consulta}` : window.location.pathname
        );
    }
}

// ── auxiliares ───────────────────────────────────────────────────

function valoresUnicos(acoes, campo) {
    return [...new Set(acoes.map((acao) => acao[campo]).filter(Boolean))].sort();
}

function preencheOpcoes(select, valores) {
    for (const valor of valores) {
        const opcao = document.createElement('option');
        opcao.value = valor;
        opcao.textContent = valor;
        select.append(opcao);
    }
}

function escreveNosCampos(campos, estado) {
    campos.busca.value = estado.busca;
    campos.bairro.value = estado.bairro;
    campos.ano.value = estado.ano;
    campos.ordem.value = estado.ordem;
}

function temAlgumFiltro(estado) {
    return Object.keys(PADRAO).some((chave) => estado[chave] !== PADRAO[chave]);
}

function descreve(visiveis, total, filtrando) {
    if (!filtrando) {
        return total === 1 ? '1 ação realizada.' : `${total} ações realizadas.`;
    }
    if (visiveis === 0) {
        return 'Nenhuma ação corresponde aos filtros.';
    }
    if (visiveis === 1) {
        return `1 ação encontrada, de ${total}.`;
    }
    return `${visiveis} ações encontradas, de ${total}.`;
}
