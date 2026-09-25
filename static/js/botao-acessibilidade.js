/**
 * Mantém o botão de acessibilidade visível quando a janela do VLibras abre.
 *
 * Fechado, o VLibras é só um ícone de 40px e o nosso botão fica logo abaixo,
 * pela posição do CSS. Aberto, o widget vira um painel alto que cobre a faixa
 * direita — e engolia o nosso botão.
 *
 * Aqui o botão passa a acompanhar: sempre que a área do widget muda de
 * tamanho, ele se reposiciona para logo abaixo da borda inferior dela. Se não
 * couber embaixo, encosta no rodapé da janela, que é o lugar livre mais
 * próximo.
 *
 * A detecção é por geometria, não por nome de classe: mede-se o retângulo do
 * [vw-plugin-wrapper]. Se o VLibras mudar a nomenclatura interna numa
 * atualização, isto continua funcionando. E se o widget não carregar, nada
 * acontece — o botão fica onde o CSS o pôs.
 */

const FOLGA = 12;
const MARGEM_DA_JANELA = 12;

const botao = document.querySelector('[data-painel-acessibilidade] [data-abrir-painel]');
const vlibras = document.querySelector('div[vw]');
const janelaDoWidget = vlibras && vlibras.querySelector('[vw-plugin-wrapper]');

if (botao && vlibras && janelaDoWidget) {
    acompanhar(botao, vlibras, janelaDoWidget);
}

function acompanhar(botao, vlibras, janelaDoWidget) {
    /** Aberto quando o painel tem área na tela. */
    function estaAberto() {
        const r = janelaDoWidget.getBoundingClientRect();
        return r.height > 8 && r.width > 8;
    }

    function reposicionar() {
        if (!estaAberto()) {
            botao.style.removeProperty('top');   // volta à posição do CSS
            return;
        }

        const painel = janelaDoWidget.getBoundingClientRect();
        const altura = botao.offsetHeight || 40;
        const limite = window.innerHeight - altura - MARGEM_DA_JANELA;

        // Logo abaixo do painel; se não couber, no rodapé da janela.
        const alvo = Math.min(painel.bottom + FOLGA, limite);
        botao.style.top = `${Math.max(MARGEM_DA_JANELA, alvo)}px`;
    }

    /* O widget abre e fecha trocando classes e estilos nos próprios nós. */
    new MutationObserver(reposicionar).observe(vlibras, {
        attributes: true,
        attributeFilter: ['class', 'style'],
        subtree: true,
        childList: true,
    });

    /* Redimensionar a janela com o painel aberto muda onde é "logo abaixo". */
    window.addEventListener('resize', reposicionar, { passive: true });

    reposicionar();
}
