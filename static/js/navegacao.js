/**
 * Navegação do site público: sombra da barra ao rolar e menu sanfonado no celular.
 *
 * Extraído de templates/public/base_publica.html. Carregado como módulo, então
 * roda depois que o documento foi analisado e não precisa esperar evento algum.
 */

const barra = document.getElementById('navbar');
const listaDeLinks = document.getElementById('navLinks');
const botaoDoMenu = document.getElementById('hamburger');

const LIMITE_DE_ROLAGEM = 40;

if (barra) {
    window.addEventListener('scroll', () => {
        barra.classList.toggle('scrolled', window.scrollY > LIMITE_DE_ROLAGEM);
    }, { passive: true });
}

if (botaoDoMenu && listaDeLinks) {
    const icone = botaoDoMenu.querySelector('i');

    botaoDoMenu.addEventListener('click', () => {
        const aberto = listaDeLinks.classList.toggle('aberto');
        if (icone) {
            icone.className = aberto ? 'bi bi-x' : 'bi bi-list';
        }
    });
}
