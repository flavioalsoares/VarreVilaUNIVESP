/**
 * Preferências de acessibilidade: estado, persistência e o painel de opções.
 *
 * Carregado como script clássico no <head>, sem defer, de propósito: as
 * preferências gravadas precisam ser aplicadas ao elemento <html> ANTES da
 * primeira pintura. Com um módulo (que é adiado) o visitante veria a página
 * piscar no padrão antes de assumir a preferência dele.
 *
 * Cada preferência vira um atributo de <html>, e todo o efeito visual é CSS
 * (static/css/acessibilidade.css). Este arquivo não pinta nada. Sem
 * JavaScript nenhum atributo é escrito e a página fica no padrão.
 *
 * Duas exceções que precisam de mais do que CSS moram em módulos próprios,
 * que escutam o evento 'vv:preferencias-alteradas' publicado aqui:
 *   - guia-de-leitura.js  (a faixa segue o mouse)
 *   - leitura.js          (voz alta não é preferência; é ação)
 *
 * Nenhum módulo importa este arquivo. A comunicação é por evento porque o
 * armazenamento de estáticos em produção renomeia os arquivos com hash e o
 * Django não reescreve caminhos de import dentro de JavaScript.
 */

(function () {
    'use strict';

    const CHAVE = 'varrevila:preferencias';
    const NIVEIS_DE_FONTE = ['normal', 'grande', 'maior'];

    /* Cada alternância liga um atributo de <html> com um valor fixo. O nome
       legível é o que a região viva anuncia ao ligar ou desligar. */
    const ALTERNANCIAS = {
        contraste:    { atributo: 'data-contraste',     valor: 'alto',       nome: 'Alto contraste' },
        espacamento:  { atributo: 'data-espacamento',   valor: 'amplo',      nome: 'Espaçamento de texto' },
        links:        { atributo: 'data-links',         valor: 'destacados', nome: 'Links destacados' },
        fonteLegivel: { atributo: 'data-fonte-legivel', valor: 'sim',        nome: 'Fonte de leitura facilitada' },
        cinza:        { atributo: 'data-cinza',         valor: 'sim',        nome: 'Escala de cinza' },
        cursor:       { atributo: 'data-cursor',        valor: 'grande',     nome: 'Cursor ampliado' },
        movimento:    { atributo: 'data-movimento',     valor: 'reduzido',   nome: 'Animações pausadas' },
        guia:         { atributo: 'data-guia',          valor: 'sim',        nome: 'Guia de leitura' },
    };

    const NOME_DO_NIVEL = { normal: 'padrão', grande: 'grande', maior: 'muito grande' };

    const FONTE_LEGIVEL_URL =
        'https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap';

    function padrao() {
        const p = { fonte: 'normal' };
        for (const chave of Object.keys(ALTERNANCIAS)) {
            p[chave] = false;
        }
        return p;
    }

    /**
     * Lê o que está gravado, tolerando ausência, JSON corrompido e navegador
     * com armazenamento bloqueado. Valores desconhecidos caem no padrão em vez
     * de deixar a página num estado que o CSS não sabe representar.
     */
    function leGravadas() {
        const base = padrao();
        try {
            const bruto = window.localStorage.getItem(CHAVE);
            if (!bruto) {
                return base;
            }
            const lidas = JSON.parse(bruto);
            base.fonte = NIVEIS_DE_FONTE.includes(lidas.fonte) ? lidas.fonte : 'normal';
            for (const chave of Object.keys(ALTERNANCIAS)) {
                base[chave] = lidas[chave] === true;
            }
            return base;
        } catch (erro) {
            return base;
        }
    }

    function grava(preferencias) {
        try {
            window.localStorage.setItem(CHAVE, JSON.stringify(preferencias));
        } catch (erro) {
            // Janela anônima ou armazenamento desabilitado: a preferência vale
            // para esta visita e não persiste. Melhor do que quebrar a página.
        }
    }

    /* A fonte só é baixada quando alguém liga a opção — ninguém paga pelos
       ~30 KB sem usar. O <link> vai para o <head>, que já existe quando
       este script roda. */
    function garanteFonteLegivel() {
        if (document.getElementById('fonte-legivel')) {
            return;
        }
        const link = document.createElement('link');
        link.id = 'fonte-legivel';
        link.rel = 'stylesheet';
        link.href = FONTE_LEGIVEL_URL;
        document.head.appendChild(link);
    }

    function aplica(preferencias) {
        const raiz = document.documentElement;
        raiz.setAttribute('data-fonte', preferencias.fonte);
        for (const [chave, regra] of Object.entries(ALTERNANCIAS)) {
            if (preferencias[chave]) {
                raiz.setAttribute(regra.atributo, regra.valor);
            } else {
                raiz.removeAttribute(regra.atributo);
            }
        }
        if (preferencias.fonteLegivel) {
            garanteFonteLegivel();
        }
    }

    let preferencias = leGravadas();
    aplica(preferencias);

    // ─────────────────────────────────────────────────────────────
    //  Painel — só depois que o documento existe
    // ─────────────────────────────────────────────────────────────

    function moveNivelDaFonte(passo) {
        const atual = NIVEIS_DE_FONTE.indexOf(preferencias.fonte);
        const novo = Math.min(NIVEIS_DE_FONTE.length - 1, Math.max(0, atual + passo));
        return NIVEIS_DE_FONTE[novo];
    }

    document.addEventListener('DOMContentLoaded', function () {
        const raizDoPainel = document.querySelector('[data-painel-acessibilidade]');
        if (!raizDoPainel) {
            return;
        }

        const botaoAbrir = raizDoPainel.querySelector('[data-abrir-painel]');
        const painel = raizDoPainel.querySelector('[data-painel]');
        const botaoFechar = raizDoPainel.querySelector('[data-fechar-painel]');
        const aviso = raizDoPainel.querySelector('[data-aviso-preferencia]');

        function anuncia(mensagem) {
            if (aviso) {
                aviso.textContent = mensagem;
            }
        }

        // ── abrir e fechar ──

        function abre() {
            painel.hidden = false;
            botaoAbrir.setAttribute('aria-expanded', 'true');
            const primeiro = painel.querySelector('button:not([disabled])');
            if (primeiro) {
                primeiro.focus();
            }
        }

        function fecha(devolverFoco) {
            painel.hidden = true;
            botaoAbrir.setAttribute('aria-expanded', 'false');
            if (devolverFoco !== false) {
                botaoAbrir.focus();
            }
        }

        botaoAbrir.addEventListener('click', () => (painel.hidden ? abre() : fecha()));
        botaoFechar.addEventListener('click', () => fecha());

        document.addEventListener('keydown', (evento) => {
            if (evento.key === 'Escape' && !painel.hidden) {
                fecha();
            }
        });

        /* Clique fora fecha, mas sem roubar o foco de onde a pessoa clicou. */
        document.addEventListener('click', (evento) => {
            if (!painel.hidden && !raizDoPainel.contains(evento.target)) {
                fecha(false);
            }
        });

        /* Outros módulos podem pedir para abrir — os atalhos de teclado usam. */
        document.addEventListener('vv:abrir-painel-acessibilidade', abre);

        // ── estado dos controles ──

        function sincroniza() {
            for (const botao of painel.querySelectorAll('[data-alternar]')) {
                const chave = botao.dataset.alternar;
                botao.setAttribute('aria-pressed', String(preferencias[chave] === true));
            }
            for (const botao of painel.querySelectorAll('[data-acao$="-fonte"]')) {
                const noLimite =
                    (botao.dataset.acao === 'aumentar-fonte' && preferencias.fonte === 'maior') ||
                    (botao.dataset.acao === 'diminuir-fonte' && preferencias.fonte === 'normal');
                botao.disabled = noLimite;
            }
        }

        function altera(mudanca, mensagem) {
            preferencias = Object.assign({}, preferencias, mudanca);
            aplica(preferencias);
            grava(preferencias);
            sincroniza();
            anuncia(mensagem);
            document.dispatchEvent(new CustomEvent('vv:preferencias-alteradas', {
                detail: Object.assign({}, preferencias),
            }));
        }

        painel.addEventListener('click', (evento) => {
            const botao = evento.target.closest('[data-acao], [data-alternar]');
            if (!botao || botao.disabled) {
                return;
            }

            if (botao.dataset.alternar) {
                const chave = botao.dataset.alternar;
                const ligado = !preferencias[chave];
                altera({ [chave]: ligado }, ALTERNANCIAS[chave].nome + (ligado ? ' ativado.' : ' desativado.'));
                return;
            }

            switch (botao.dataset.acao) {
                case 'aumentar-fonte': {
                    const nivel = moveNivelDaFonte(1);
                    altera({ fonte: nivel }, 'Tamanho da letra: ' + NOME_DO_NIVEL[nivel] + '.');
                    break;
                }
                case 'diminuir-fonte': {
                    const nivel = moveNivelDaFonte(-1);
                    altera({ fonte: nivel }, 'Tamanho da letra: ' + NOME_DO_NIVEL[nivel] + '.');
                    break;
                }
                case 'restaurar-fonte':
                    altera({ fonte: 'normal' }, 'Tamanho da letra restaurado para o padrão.');
                    break;
                case 'restaurar-tudo':
                    altera(padrao(), 'Todas as preferências foram restauradas.');
                    break;
            }
        });

        sincroniza();
    });
})();
