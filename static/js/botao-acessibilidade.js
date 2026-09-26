/**
 * Mantém o botão de acessibilidade visível quando algo o cobre — na prática,
 * a janela do VLibras, que ao abrir ocupa a faixa direita da tela.
 *
 * A primeira versão media o retângulo do [vw-plugin-wrapper] e não funcionou:
 * o painel real do VLibras não vive dentro dele com geometria mensurável.
 * Esta versão não tenta adivinhar a estrutura do widget — pergunta ao próprio
 * navegador quem está no lugar do botão, com elementFromPoint, e desce até
 * achar espaço livre. Funciona para o VLibras e para qualquer outra coisa que
 * venha a cobrir aquele canto.
 *
 * Ao fechar, o botão volta sozinho: antes de cada avaliação a posição em
 * linha é removida, então ele é sempre medido a partir do lugar do CSS.
 */

const FOLGA = 12;
const MARGEM = 12;
const MAX_TENTATIVAS = 6;
/* O painel do VLibras abre com animação. Uma única medida logo após o
   clique pegaria o painel a meio caminho, e nenhuma mutação posterior
   acordaria o módulo de novo — daí reavaliar algumas vezes. */
const ESPERAS = [120, 400, 900];

const botao = document.querySelector('[data-painel-acessibilidade] [data-abrir-painel]');

if (botao) {
    vigiar(botao);
}

function vigiar(botao) {
    /** Quem está desenhado por cima do botão, se alguém estiver. */
    function quemCobre() {
        const r = botao.getBoundingClientRect();
        if (r.width === 0) {
            return null;
        }
        const pontos = [
            [r.left + 3, r.top + 3],
            [r.right - 3, r.top + 3],
            [r.left + r.width / 2, r.top + r.height / 2],
            [r.left + 3, r.bottom - 3],
            [r.right - 3, r.bottom - 3],
        ];
        for (const [x, y] of pontos) {
            if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) {
                continue;
            }
            const alvo = document.elementFromPoint(x, y);
            if (alvo && alvo !== botao && !botao.contains(alvo) && !alvo.contains(botao)) {
                return alvo;
            }
        }
        return null;
    }

    function avaliar() {
        /* Sempre parte da posição do CSS: é o que faz o botão voltar ao lugar
           quando a janela do VLibras fecha. */
        botao.style.removeProperty('top');

        const limite = window.innerHeight - (botao.offsetHeight || 40) - MARGEM;

        for (let i = 0; i < MAX_TENTATIVAS; i += 1) {
            const cobridor = quemCobre();
            if (!cobridor) {
                return;                       // livre
            }
            const abaixo = cobridor.getBoundingClientRect().bottom + FOLGA;
            const alvo = Math.max(MARGEM, Math.min(abaixo, limite));
            const atual = botao.getBoundingClientRect().top;
            if (alvo <= atual + 1) {
                return;                       // não há para onde descer
            }
            botao.style.top = `${alvo}px`;
        }
    }

    let agendados = [];
    function agendar() {
        for (const id of agendados) {
            window.clearTimeout(id);
        }
        agendados = ESPERAS.map((ms) => window.setTimeout(avaliar, ms));
    }

    /* O widget abre e fecha mexendo no DOM; não se sabe onde, então observa-se
       o documento inteiro, com espera para não reavaliar a cada mutação. */
    new MutationObserver(agendar).observe(document.body, {
        attributes: true,
        attributeFilter: ['class', 'style', 'hidden'],
        childList: true,
        subtree: true,
    });

    document.addEventListener('click', agendar, true);
    window.addEventListener('resize', agendar, { passive: true });
    window.addEventListener('transitionend', agendar, true);

    avaliar();
}
