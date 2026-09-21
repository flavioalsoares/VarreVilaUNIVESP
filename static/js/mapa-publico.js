/**
 * Mapa público das ações realizadas, alimentado pela API própria.
 *
 * É a "View em JavaScript numa tela" combinada como demonstração de
 * arquitetura: o Django entrega a casca e a lista em HTML; este módulo busca
 * /api/v1/eventos/ e desenha os marcadores por conta própria. Sem JavaScript
 * o mapa não aparece — o contêiner nasce com hidden — e a lista continua lá.
 *
 * Sincroniza com filtros.js sem conhecê-lo: escuta 'vv:filtro-aplicado' e
 * esconde os marcadores cujo id não está entre os visíveis. Não há import
 * entre módulos porque o armazenamento de estáticos em produção renomeia os
 * arquivos com hash e o Django não reescreve caminhos de import em JS.
 *
 * Acessibilidade: os marcadores são L.marker com ícone HTML, e não
 * L.circleMarker. A diferença importa — o Leaflet dá a marcadores de ícone
 * foco por teclado (Tab percorre, Enter abre o popup) e um atributo alt, o
 * que os desenhos em SVG do circleMarker não têm.
 */

const URL_DA_API = '/api/v1/eventos/?status=realizado&page_size=200';
const CENTRO_DE_SAO_PAULO = [-23.5505, -46.6333];
const ZOOM_INICIAL = 11;

const raiz = document.querySelector('[data-mapa-publico]');
const area = document.getElementById('mapa-publico');

if (raiz && area && typeof L !== 'undefined') {
    iniciar(raiz, area);
}

async function iniciar(raiz, area) {
    const legenda = raiz.querySelector('[data-mapa-legenda]');
    raiz.hidden = false;
    mostraAviso(area, 'Carregando o mapa…');

    let eventos;
    try {
        eventos = await buscaTodos(URL_DA_API);
    } catch (erro) {
        mostraAviso(area, 'Não foi possível carregar o mapa agora. A lista abaixo traz as mesmas ações.');
        return;
    }

    const geolocalizados = eventos.filter((e) => e.latitude !== null && e.longitude !== null);
    if (geolocalizados.length === 0) {
        mostraAviso(area, 'Nenhuma ação com localização registrada ainda.');
        return;
    }

    area.textContent = '';
    const mapa = L.map(area, { scrollWheelZoom: false }).setView(CENTRO_DE_SAO_PAULO, ZOOM_INICIAL);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
    }).addTo(mapa);

    const marcadores = new Map();
    for (const evento of geolocalizados) {
        const marcador = L.marker([evento.latitude, evento.longitude], {
            icon: L.divIcon({ className: 'marcador-mutirao', iconSize: [18, 18] }),
            alt: `${evento.titulo}, ${evento.bairro}, ${formataData(evento.data)}`,
            title: evento.titulo,
        })
            .addTo(mapa)
            .bindPopup(montaPopup(evento));
        marcadores.set(evento.id, marcador);
    }

    mapa.fitBounds(geolocalizados.map((e) => [e.latitude, e.longitude]), { padding: [24, 24], maxZoom: 13 });
    atualizaLegenda(legenda, geolocalizados.length, geolocalizados.length, false);

    /* Os filtros da lista publicam os ids visíveis; o mapa só obedece. */
    document.addEventListener('vv:filtro-aplicado', ({ detail }) => {
        const visiveis = new Set(detail.ids);
        let mostrados = 0;
        for (const [id, marcador] of marcadores) {
            const mostrar = !detail.filtrando || visiveis.has(id);
            marcador.getElement()?.classList.toggle('oculto', !mostrar);
            if (mostrar) {
                mostrados += 1;
            } else {
                marcador.closePopup();
            }
        }
        atualizaLegenda(legenda, mostrados, marcadores.size, detail.filtrando);
    });
}

/**
 * Percorre a paginação da API até o fim. A primeira página já vem com
 * page_size=200, então normalmente é uma requisição só — mas se a ONG
 * passar de duzentos mutirões, o mapa continua completo sem mudar nada aqui.
 */
async function buscaTodos(url) {
    const acumulado = [];
    let proxima = url;
    while (proxima) {
        const resposta = await fetch(proxima, { headers: { Accept: 'application/json' } });
        if (!resposta.ok) {
            throw new Error(`HTTP ${resposta.status}`);
        }
        const pagina = await resposta.json();
        acumulado.push(...pagina.results);
        proxima = pagina.next;
    }
    return acumulado;
}

function montaPopup(evento) {
    const caixa = document.createElement('div');

    const titulo = document.createElement('strong');
    titulo.textContent = evento.titulo;
    caixa.append(titulo, document.createElement('br'));

    caixa.append(document.createTextNode(`${evento.bairro} · ${formataData(evento.data)}`));

    if (evento.impacto) {
        caixa.append(document.createElement('br'));
        const impacto = document.createElement('span');
        impacto.textContent =
            `${formataQuilos(evento.impacto.lixo_kg)} recolhidos · ` +
            `${evento.impacto.numero_participantes} voluntários`;
        caixa.append(impacto);
    }
    return caixa;
}

function mostraAviso(area, texto) {
    area.textContent = '';
    const aviso = document.createElement('p');
    aviso.className = 'mapa-publico-aviso';
    aviso.textContent = texto;
    area.append(aviso);
}

function atualizaLegenda(legenda, mostrados, total, filtrando) {
    if (!legenda) {
        return;
    }
    if (!filtrando) {
        legenda.textContent = total === 1 ? '1 mutirão no mapa.' : `${total} mutirões no mapa.`;
    } else {
        legenda.textContent = `${mostrados} de ${total} mutirões no mapa.`;
    }
}

function formataData(iso) {
    const [ano, mes, dia] = iso.split('-');
    return `${dia}/${mes}/${ano}`;
}

function formataQuilos(valor) {
    return Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + ' kg';
}
