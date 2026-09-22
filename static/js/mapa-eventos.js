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

    /* Tiles do Esri World Street Map. Histórico da escolha, em setembro de
       2026: os servidores voluntários do OpenStreetMap passaram a devolver
       "Access blocked" — a política de uso deles proíbe apps publicados de
       consumi-los direto. O CARTO, primeira alternativa, marca os tiles com
       "API KEY REQUIRED" para domínios não cadastrados. O Esri permite uso
       gratuito com atribuição, sem chave, e serve por CDN comercial.
       Repare na ordem {z}/{y}/{x} — o Esri inverte y e x. */
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © <a href="https://www.esri.com/">Esri</a> — Esri, TomTom, Garmin, FAO, NOAA, USGS, © OpenStreetMap contributors',
        maxZoom: 19,
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
