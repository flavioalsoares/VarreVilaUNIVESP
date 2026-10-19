/**
 * Desvia o botão de acessibilidade quando algo o cobre — na prática, o painel
 * do VLibras, que ao abrir ocupa a faixa direita da tela.
 *
 * Histórico, porque a solução óbvia não funciona aqui: o VLibras desenha
 * dentro de shadow DOM. Os nós que ele deixa no documento — div[vw],
 * [vw-access-button], [vw-plugin-wrapper] — têm 1350x0 no fim da página e não
 * correspondem a nada do que se vê. Medir o painel é impossível a partir
 * daqui; duas tentativas nesse caminho falharam.
 *
 * O que funciona é perguntar "tem alguém na frente?" com elementFromPoint,
 * que atravessa o shadow DOM devolvendo o elemento hospedeiro. A resposta é
 * confiável; o retângulo dela, não. Então este módulo usa só o sim ou não, e
 * manda o botão para um canto conhecidamente livre — o inferior esquerdo, do
 * lado oposto ao do widget. Nada de aritmética sobre medidas de terceiros.
 */

const MAX_TENTATIVAS = 3;
/* O painel abre com animação: uma medida só, logo após o clique, pegaria o
   painel a meio caminho e nada acordaria o módulo depois. */
const ESPERAS = [120, 400, 900];
const ATRIBUTO = 'data-botao-desviado';

const botao = document.querySelector('[data-painel-acessibilidade] [data-abrir-painel]');

if (botao) {
    vigiar(botao);
}

function vigiar(botao) {
    const raiz = document.documentElement;

    /** Alguém desenhado por cima do botão? Só o sim ou não interessa. */
    function estaCoberto() {
        const r = botao.getBoundingClientRect();
        if (r.width === 0) {
            return false;
        }
        const pontos = [
            [r.left + 3, r.top + 3],
            [r.right - 3, r.top + 3],
            [r.left + r.width / 2, r.top + r.height / 2],
            [r.left + 3, r.bottom - 3],
            [r.right - 3, r.bottom - 3],
        ];
        return pontos.some(([x, y]) => {
            if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) {
                return false;
            }
            const alvo = document.elementFromPoint(x, y);
            return alvo && alvo !== botao && !botao.contains(alvo) && !alvo.contains(botao);
        });
    }

    function avaliar() {
        /* Começa sempre pela posição do CSS: é o que faz o botão voltar
           sozinho quando o painel do VLibras fecha. */
        raiz.removeAttribute(ATRIBUTO);

        for (let i = 0; i < MAX_TENTATIVAS; i += 1) {
            if (!estaCoberto()) {
                return;
            }
            if (raiz.hasAttribute(ATRIBUTO)) {
                return;      // já está no canto alternativo e ainda assim coberto
            }
            raiz.setAttribute(ATRIBUTO, '');
        }
    }

    let agendados = [];
    function agendar() {
        for (const id of agendados) {
            window.clearTimeout(id);
        }
        agendados = ESPERAS.map((ms) => window.setTimeout(avaliar, ms));
    }

    /* O widget abre e fecha dentro do próprio shadow DOM; não há mutação
       observável no documento, então o gatilho é o clique. */
    document.addEventListener('click', agendar, true);
    window.addEventListener('resize', agendar, { passive: true });
    new MutationObserver(agendar).observe(document.body, {
        attributes: true,
        attributeFilter: ['class', 'style', 'hidden'],
        childList: true,
        subtree: true,
    });

    avaliar();
}
