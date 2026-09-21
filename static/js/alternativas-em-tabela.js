/**
 * Alternativas em tabela para o gráfico e o mapa do painel interno.
 *
 * Um <canvas> do Chart.js e um mapa do Leaflet são invisíveis para leitor de
 * tela: o que a pessoa ouve é "gráfico" ou nada. Este módulo lê os mesmos
 * dados que alimentam as duas visualizações — os elementos json_script que
 * o Django escreve na página — e gera uma <table> equivalente para cada uma,
 * com <caption> e cabeçalhos de coluna.
 *
 * As tabelas nascem escondidas atrás de um botão "Ver como tabela", para não
 * duplicar o conteúdo visual de quem enxerga. A visualização recebe
 * aria-label apontando para a alternativa, e é assim que o leitor de tela
 * descobre que ela existe.
 */

const NOMES_DE_STATUS = {
    planejado: 'Planejado',
    realizado: 'Realizado',
    cancelado: 'Cancelado',
};

function leDados(id) {
    const elemento = document.getElementById(id);
    return elemento ? JSON.parse(elemento.textContent) : null;
}

function celula(tipo, texto) {
    const c = document.createElement(tipo);
    c.textContent = texto;
    if (tipo === 'th') {
        c.scope = 'col';
    }
    return c;
}

function montaTabela(legenda, cabecalhos, linhas) {
    const tabela = document.createElement('table');
    tabela.className = 'table table-sm table-striped mt-3';

    const caption = document.createElement('caption');
    caption.textContent = legenda;
    tabela.appendChild(caption);

    const thead = document.createElement('thead');
    const linhaDoCabecalho = document.createElement('tr');
    for (const texto of cabecalhos) {
        linhaDoCabecalho.appendChild(celula('th', texto));
    }
    thead.appendChild(linhaDoCabecalho);
    tabela.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (const valores of linhas) {
        const tr = document.createElement('tr');
        for (const valor of valores) {
            tr.appendChild(celula('td', valor));
        }
        tbody.appendChild(tr);
    }
    tabela.appendChild(tbody);

    return tabela;
}

function formataQuilos(valor) {
    return Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' kg';
}

function formataData(iso) {
    const [ano, mes, dia] = iso.split('-');
    return `${dia}/${mes}/${ano}`;
}

/**
 * Liga um botão que alterna a tabela, e descreve a visualização para quem
 * não a vê. O botão declara aria-expanded e aria-controls, então o leitor
 * de tela anuncia "recolhido/expandido" e sabe o que o botão controla.
 */
function instala(container, visual, descricao, tabela) {
    if (!container || !tabela) {
        return;
    }

    const id = 'tabela-' + container.dataset.tabelaPara;
    tabela.id = id;
    tabela.hidden = true;

    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'btn btn-sm btn-outline-secondary mt-2';
    botao.setAttribute('aria-expanded', 'false');
    botao.setAttribute('aria-controls', id);
    botao.textContent = 'Ver como tabela';

    botao.addEventListener('click', () => {
        const abrir = tabela.hidden;
        tabela.hidden = !abrir;
        botao.setAttribute('aria-expanded', String(abrir));
        botao.textContent = abrir ? 'Ocultar tabela' : 'Ver como tabela';
        if (abrir) {
            tabela.setAttribute('tabindex', '-1');
            tabela.focus();
        }
    });

    if (visual) {
        visual.setAttribute('role', 'img');
        visual.setAttribute('aria-label', descricao + ' Os mesmos dados estão disponíveis em tabela, pelo botão a seguir.');
    }

    container.append(botao, tabela);
}

// ── gráfico mensal ──

const rotulos = leDados('labels-data');
const valores = leDados('dados-data');

if (rotulos && valores) {
    const linhas = rotulos.map((mes, i) => [mes, formataQuilos(valores[i] ?? 0)]);
    instala(
        document.querySelector('[data-tabela-para="graficoMensal"]'),
        document.getElementById('graficoMensal'),
        'Gráfico de barras: lixo coletado por mês, em quilos.',
        linhas.length
            ? montaTabela('Lixo coletado por mês', ['Mês', 'Lixo coletado'], linhas)
            : montaTabela('Lixo coletado por mês', ['Mês', 'Lixo coletado'], [['Sem dados', '—']])
    );
}

// ── mapa de eventos ──

const eventos = leDados('eventos-data');

if (eventos) {
    const linhas = eventos.map((e) => [
        e.titulo,
        e.bairro,
        formataData(e.data),
        NOMES_DE_STATUS[e.status] || e.status,
    ]);
    instala(
        document.querySelector('[data-tabela-para="map"]'),
        document.getElementById('map'),
        `Mapa com ${eventos.length} mutirões geolocalizados.`,
        montaTabela('Mutirões no mapa', ['Mutirão', 'Bairro', 'Data', 'Situação'],
            linhas.length ? linhas : [['Nenhum mutirão geolocalizado', '—', '—', '—']])
    );
}
