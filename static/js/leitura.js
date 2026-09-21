/**
 * Leitura em voz alta com a Web Speech API — nativa do navegador, sem custo.
 *
 * Lê o texto selecionado; sem seleção, lê o conteúdo principal da página.
 * Fala em pt-BR quando o sistema tem uma voz nesse idioma.
 *
 * O texto é dividido em frases antes de ir para a fila. Não é capricho:
 * o Chrome interrompe silenciosamente falas longas depois de uns quinze
 * segundos, e frases curtas contornam isso. Também permite parar entre uma
 * frase e outra sem esperar a fala inteira.
 *
 * Quando o navegador não oferece a API, o controle some do painel em vez
 * de ficar um botão que não faz nada.
 */

const raiz = document.querySelector('[data-leitura]');
const suportado = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

if (raiz && !suportado) {
    raiz.hidden = true;
}

if (raiz && suportado) {
    iniciar(raiz);
}

function iniciar(raiz) {
    const sintetizador = window.speechSynthesis;
    const botaoLer = raiz.querySelector('[data-leitura-acao="ler"]');
    const botaoParar = raiz.querySelector('[data-leitura-acao="parar"]');
    const estado = raiz.querySelector('[data-leitura-estado]');

    let vozEmPortugues = null;
    let lendo = false;

    /* As vozes chegam de forma assíncrona em alguns navegadores. */
    function escolheVoz() {
        const vozes = sintetizador.getVoices();
        vozEmPortugues =
            vozes.find((voz) => voz.lang === 'pt-BR') ||
            vozes.find((voz) => voz.lang.startsWith('pt')) ||
            null;
    }
    escolheVoz();
    sintetizador.addEventListener('voiceschanged', escolheVoz);

    function textoParaLer() {
        const selecao = window.getSelection ? window.getSelection().toString().trim() : '';
        if (selecao) {
            return { texto: selecao, origem: 'a seleção' };
        }
        const principal = document.getElementById('conteudo') || document.querySelector('main');
        return {
            texto: principal ? principal.innerText.trim() : '',
            origem: 'o conteúdo da página',
        };
    }

    function emFrases(texto) {
        return texto
            .replace(/\s+/g, ' ')
            .split(/(?<=[.!?…])\s+/)
            .map((frase) => frase.trim())
            .filter((frase) => frase.length > 0);
    }

    function atualizaControles() {
        botaoLer.disabled = lendo;
        botaoParar.disabled = !lendo;
        botaoParar.hidden = !lendo;
    }

    function informa(mensagem) {
        if (estado) {
            estado.textContent = mensagem;
        }
    }

    function parar() {
        sintetizador.cancel();
        lendo = false;
        atualizaControles();
        informa('Leitura interrompida.');
    }

    function ler() {
        const { texto, origem } = textoParaLer();
        const frases = emFrases(texto);
        if (frases.length === 0) {
            informa('Não há texto para ler.');
            return;
        }

        sintetizador.cancel();
        lendo = true;
        atualizaControles();
        informa('Lendo ' + origem + '…');

        frases.forEach((frase, indice) => {
            const fala = new SpeechSynthesisUtterance(frase);
            fala.lang = 'pt-BR';
            fala.rate = 1;
            if (vozEmPortugues) {
                fala.voice = vozEmPortugues;
            }
            if (indice === frases.length - 1) {
                fala.addEventListener('end', () => {
                    lendo = false;
                    atualizaControles();
                    informa('Leitura concluída.');
                });
            }
            fala.addEventListener('error', (evento) => {
                if (evento.error !== 'interrupted' && evento.error !== 'canceled') {
                    lendo = false;
                    atualizaControles();
                    informa('Não foi possível continuar a leitura.');
                }
            });
            sintetizador.speak(fala);
        });
    }

    botaoLer.addEventListener('click', ler);
    botaoParar.addEventListener('click', parar);

    /* Navegar para outra página no meio da fala deixaria a voz falando
       sozinha em alguns navegadores. */
    window.addEventListener('pagehide', () => sintetizador.cancel());

    atualizaControles();
}
