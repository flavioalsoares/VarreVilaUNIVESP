/**
 * Mapa dos mutirões no painel interno, com um marcador por evento geolocalizado.
 *
 * Extraído de templates/dashboard/index.html. Depende do Leaflet, carregado como
 * script clássico em templates/base.html — que executa antes deste módulo.
 *
 * O popup é construído por DOM em vez de string HTML: textContent escapa o
 * conteúdo automaticamente, o que impede injeção a partir de dados do banco.
 */

const CENTRO_DE_SAO_PAULO = [-23.5505, -46.6333];
const ZOOM_INICIAL = 11;

const CORES_POR_STATUS = {
    planejado: '#0d6efd',
    realizado: '#a6ce39',
    cancelado: '#dc3545',
};
const COR_PADRAO = '#888';

function montaPopup(evento) {
    const caixa = document.createElement('div');

    const titulo = document.createElement('strong');
    titulo.textContent = evento.titulo;
    caixa.appendChild(titulo);
    caixa.appendChild(document.createElement('br'));

    caixa.appendChild(document.createTextNode('📍 ' + evento.bairro));
    caixa.appendChild(document.createElement('br'));
    caixa.appendChild(document.createTextNode('📅 ' + evento.data));
    caixa.appendChild(document.createElement('br'));

    const link = document.createElement('a');
    link.href = '/events/' + encodeURIComponent(evento.id) + '/';
    link.className = 'btn btn-sm btn-success mt-1';
    link.textContent = 'Ver detalhes';
    caixa.appendChild(link);

    return caixa;
}

const divDoMapa = document.getElementById('map');
const dados = document.getElementById('eventos-data');

if (divDoMapa && dados && typeof L !== 'undefined') {
    const mapa = L.map(divDoMapa).setView(CENTRO_DE_SAO_PAULO, ZOOM_INICIAL);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
    }).addTo(mapa);

    for (const evento of JSON.parse(dados.textContent)) {
        const cor = CORES_POR_STATUS[evento.status] || COR_PADRAO;

        L.circleMarker([evento.lat, evento.lng], {
            color: cor,
            fillColor: cor,
            fillOpacity: 0.8,
            radius: 10,
        })
            .addTo(mapa)
            .bindPopup(montaPopup(evento));
    }
}
