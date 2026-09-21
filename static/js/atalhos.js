/**
 * Atalhos de teclado no padrão do eMAG, o Modelo de Acessibilidade em
 * Governo Eletrônico do governo federal:
 *
 *   Alt+1  conteúdo principal
 *   Alt+2  menu de navegação
 *   Alt+3  rodapé
 *   Alt+4  painel de acessibilidade
 *
 * O Firefox reserva Alt+número para trocar de aba em alguns sistemas, e o
 * eMAG recomenda Shift+Alt+número como alternativa — os dois valem aqui.
 *
 * O alvo recebe tabindex="-1" quando ainda não é focável: sem isso o foco
 * não se move e o leitor de tela não sabe que a página "pulou".
 */

const ALVOS = {
    '1': () => document.getElementById('conteudo') || document.querySelector('main'),
    '2': () => document.querySelector('nav'),
    '3': () => document.querySelector('footer'),
};

document.addEventListener('keydown', (evento) => {
    if (!evento.altKey || evento.ctrlKey || evento.metaKey) {
        return;
    }

    if (evento.key === '4') {
        evento.preventDefault();
        document.dispatchEvent(new CustomEvent('vv:abrir-painel-acessibilidade'));
        return;
    }

    const localiza = ALVOS[evento.key];
    if (!localiza) {
        return;
    }

    const alvo = localiza();
    if (!alvo) {
        return;
    }

    evento.preventDefault();
    if (!alvo.hasAttribute('tabindex')) {
        alvo.setAttribute('tabindex', '-1');
    }
    alvo.focus({ preventScroll: true });
    alvo.scrollIntoView({ block: 'start' });
});
