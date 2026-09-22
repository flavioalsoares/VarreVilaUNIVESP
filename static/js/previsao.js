/**
 * Previsão do tempo para os próximos mutirões, via Open-Meteo.
 *
 * API pública, sem chave, com CORS aberto — a chamada sai do navegador. O
 * Django entrega a página completa; a previsão chega um instante depois e, se
 * o serviço falhar, simplesmente não aparece. Nenhuma visita depende de um
 * serviço externo responder.
 *
 * Uma requisição para todos os mutirões: o Open-Meteo aceita listas de
 * latitude e longitude e devolve um resultado por local. O intervalo de datas
 * vai de hoje ao mutirão mais distante dentro do horizonte de previsão, e cada
 * card pega o próprio dia da série.
 *
 * O horizonte é de 16 dias. Mutirão mais distante fica sem previsão, sem
 * ruído — a marcação nasce escondida e só é revelada quando há o que mostrar.
 */

const HORIZONTE_EM_DIAS = 16;
const URL_DA_API = 'https://api.open-meteo.com/v1/forecast';

/* Códigos WMO que o Open-Meteo usa. Texto sempre junto do ícone: o ícone
   sozinho não serve a quem não o vê nem a quem não o entende. */
const TEMPO = [
    [[0],                    '☀️', 'Céu limpo'],
    [[1],                    '🌤️', 'Predomínio de sol'],
    [[2],                    '⛅', 'Parcialmente nublado'],
    [[3],                    '☁️', 'Nublado'],
    [[45, 48],               '🌫️', 'Nevoeiro'],
    [[51, 53, 55, 56, 57],   '🌦️', 'Chuvisco'],
    [[61, 63, 65, 66, 67],   '🌧️', 'Chuva'],
    [[71, 73, 75, 77],       '🌨️', 'Neve'],
    [[80, 81, 82],           '🌦️', 'Pancadas de chuva'],
    [[95, 96, 99],           '⛈️', 'Tempestade'],
];

function descreveCodigo(codigo) {
    const linha = TEMPO.find(([codigos]) => codigos.includes(codigo));
    return linha ? { icone: linha[1], texto: linha[2] } : { icone: '🌡️', texto: 'Sem detalhe' };
}

function hojeIso() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function diasEntre(isoA, isoB) {
    return Math.round((new Date(isoB + 'T12:00') - new Date(isoA + 'T12:00')) / 86400000);
}

const cards = Array.from(document.querySelectorAll('[data-previsao]'));

if (cards.length > 0) {
    prever(cards);
}

async function prever(cards) {
    const hoje = hojeIso();

    const alcancaveis = cards
        .map((card) => ({
            card,
            lat: card.dataset.lat,
            lng: card.dataset.lng,
            data: card.dataset.data,
            saida: card.querySelector('[data-previsao-saida]'),
        }))
        .filter(({ data, saida }) => {
            const dias = diasEntre(hoje, data);
            return saida && dias >= 0 && dias < HORIZONTE_EM_DIAS;
        });

    if (alcancaveis.length === 0) {
        return;
    }

    const ultimaData = alcancaveis.map((a) => a.data).sort().at(-1);

    const parametros = new URLSearchParams({
        latitude: alcancaveis.map((a) => a.lat).join(','),
        longitude: alcancaveis.map((a) => a.lng).join(','),
        daily: 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        timezone: 'America/Sao_Paulo',
        start_date: hoje,
        end_date: ultimaData,
    });

    let resposta;
    try {
        const r = await fetch(`${URL_DA_API}?${parametros}`, { headers: { Accept: 'application/json' } });
        if (!r.ok) {
            return;
        }
        resposta = await r.json();
    } catch (erro) {
        return;   // sem previsão, sem alarde
    }

    /* Um local só volta como objeto; vários, como array. */
    const locais = Array.isArray(resposta) ? resposta : [resposta];

    let mostrou = false;
    alcancaveis.forEach(({ card, data, saida }, i) => {
        const diario = locais[i]?.daily;
        if (!diario) {
            return;
        }
        const indice = diario.time.indexOf(data);
        if (indice === -1) {
            return;
        }

        const { icone, texto } = descreveCodigo(diario.weather_code[indice]);
        const max = Math.round(diario.temperature_2m_max[indice]);
        const min = Math.round(diario.temperature_2m_min[indice]);
        const chuva = diario.precipitation_probability_max[indice];

        saida.textContent = '';
        const spanIcone = document.createElement('span');
        spanIcone.className = 'previsao-icone';
        spanIcone.setAttribute('aria-hidden', 'true');
        spanIcone.textContent = icone;
        saida.append(
            spanIcone,
            document.createTextNode(`${texto} · ${max}° / ${min}°` + (chuva != null ? ` · ${chuva}% de chuva` : ''))
        );
        saida.setAttribute('aria-label', `Previsão para o dia: ${texto}, máxima ${max} graus, mínima ${min} graus` + (chuva != null ? `, ${chuva} por cento de chance de chuva` : ''));
        saida.hidden = false;
        mostrou = true;

        card.dispatchEvent(new CustomEvent('vv:previsao-carregada', {
            bubbles: true,
            detail: { data, codigo: diario.weather_code[indice], max, min, chuva },
        }));
    });

    if (mostrou) {
        for (const fonte of document.querySelectorAll('[data-previsao-fonte]')) {
            fonte.hidden = false;
        }
    }
}
