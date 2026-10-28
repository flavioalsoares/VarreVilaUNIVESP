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
 * Ter o objeto `speechSynthesis` não é o mesmo que poder falar, e foi isso que
 * deixou o botão morto no Brave: ele remove as vozes remotas do Google e não
 * conversa com o speech-dispatcher do sistema, então `getVoices()` devolve
 * lista vazia e `speak()` termina em `synthesis-failed`. O Chrome no Linux tem
 * as vozes do Google (todas remotas) e o Firefox usa o speech-dispatcher.
 *
 * Por isso o grupo nasce escondido na marcação e só aparece depois de
 * confirmada ao menos uma voz: um botão visível que não produz som é pior do
 * que controle nenhum. As vozes chegam de forma assíncrona, daí a espera.
 */

/* Quem nunca vai ter voz também nunca dispara 'voiceschanged', então a espera
   precisa de um limite. */
const ESPERA_PELAS_VOZES = 3000;

/* Tempo que a fala tem para começar antes de considerarmos que não vai sair.
   Sem isso o painel poderia ficar dizendo "Lendo…" para sempre. */
const ESPERA_PELA_FALA = 2500;

const SEM_VOZ = 'Este navegador não conseguiu gerar a voz. '
    + 'Experimente o Chrome ou o Firefox para ouvir a página.';

const raiz = document.querySelector('[data-leitura]');
const suportado = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

if (raiz && suportado) {
    esperaVozes().then((vozes) => {
        if (vozes.length > 0) {
            raiz.hidden = false;
            iniciar(raiz);
        }
    });
}

function esperaVozes() {
    const sintetizador = window.speechSynthesis;
    /* A primeira chamada também serve de gatilho: em alguns navegadores é ela
       que faz a lista começar a carregar. */
    if (sintetizador.getVoices().length > 0) {
        return Promise.resolve(sintetizador.getVoices());
    }
    return new Promise((resolve) => {
        let respondeu = false;
        const responde = () => {
            if (respondeu) {
                return;
            }
            respondeu = true;
            sintetizador.removeEventListener('voiceschanged', responde);
            resolve(sintetizador.getVoices());
        };
        sintetizador.addEventListener('voiceschanged', responde);
        setTimeout(responde, ESPERA_PELAS_VOZES);
    });
}

function iniciar(raiz) {
    const sintetizador = window.speechSynthesis;
    const botaoLer = raiz.querySelector('[data-leitura-acao="ler"]');
    const botaoParar = raiz.querySelector('[data-leitura-acao="parar"]');
    const estado = raiz.querySelector('[data-leitura-estado]');

    let vozEmPortugues = null;
    let lendo = false;
    let vigilancia = null;

    /* A lista pode mudar depois do primeiro carregamento. */
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

    function encerra(mensagem) {
        clearTimeout(vigilancia);
        lendo = false;
        atualizaControles();
        informa(mensagem);
    }

    function parar() {
        sintetizador.cancel();
        encerra('Leitura interrompida.');
    }

    function falhou(erro) {
        sintetizador.cancel();
        encerra(erro === 'synthesis-failed' || erro === 'synthesis-unavailable'
            ? SEM_VOZ
            : 'Não foi possível continuar a leitura.');
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
            if (indice === 0) {
                fala.addEventListener('start', () => clearTimeout(vigilancia));
            }
            if (indice === frases.length - 1) {
                fala.addEventListener('end', () => encerra('Leitura concluída.'));
            }
            fala.addEventListener('error', (evento) => {
                if (evento.error !== 'interrupted' && evento.error !== 'canceled' && lendo) {
                    falhou(evento.error);
                }
            });
            sintetizador.speak(fala);
        });

        /* Nem toda falha chega como evento de erro: se a fala não começar e
           nada for dito, a falha é o silêncio. */
        vigilancia = setTimeout(() => {
            if (lendo && !sintetizador.speaking) {
                falhou('synthesis-failed');
            }
        }, ESPERA_PELA_FALA);
    }

    botaoLer.addEventListener('click', ler);
    botaoParar.addEventListener('click', parar);

    /* Navegar para outra página no meio da fala deixaria a voz falando
       sozinha em alguns navegadores. */
    window.addEventListener('pagehide', () => sintetizador.cancel());

    atualizaControles();
}
