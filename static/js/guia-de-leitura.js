/**
 * Guia de leitura: uma faixa horizontal que acompanha o mouse e ajuda a não
 * perder a linha. Útil para dislexia e para baixa visão.
 *
 * Este módulo não decide quando a guia está ligada — quem decide é a
 * preferência gravada em preferencias.js. Ao carregar, lê o atributo que
 * aquele script já escreveu em <html>; dali em diante escuta o evento
 * 'vv:preferencias-alteradas'. É o padrão de comunicação entre módulos
 * deste projeto: por atributo e por evento, sem import.
 *
 * A faixa só existe no DOM enquanto está ligada. O ouvinte de mousemove é
 * registrado ao ligar e removido ao desligar — não fica um listener ocioso
 * disparando a cada pixel para quem nunca usou a opção.
 */

let faixa = null;

function move(evento) {
    faixa.style.top = evento.clientY + 'px';
}

function liga() {
    if (faixa) {
        return;
    }
    faixa = document.createElement('div');
    faixa.className = 'guia-de-leitura';
    faixa.setAttribute('aria-hidden', 'true');
    faixa.style.top = Math.round(window.innerHeight / 2) + 'px';
    document.body.appendChild(faixa);
    document.addEventListener('mousemove', move, { passive: true });
}

function desliga() {
    if (!faixa) {
        return;
    }
    document.removeEventListener('mousemove', move);
    faixa.remove();
    faixa = null;
}

document.addEventListener('vv:preferencias-alteradas', ({ detail }) => {
    if (detail.guia) {
        liga();
    } else {
        desliga();
    }
});

/* O estado inicial já está no <html>: preferencias.js roda no <head> e
   escreve os atributos antes da primeira pintura. Lemos dali em vez de
   esperar um evento que só chegaria na próxima mudança. */
if (document.documentElement.getAttribute('data-guia') === 'sim') {
    liga();
}
