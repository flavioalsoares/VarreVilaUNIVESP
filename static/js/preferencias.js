/**
 * Preferências de acessibilidade do site público: tamanho da letra e alto contraste.
 *
 * Carregado como script clássico no <head>, sem defer, de propósito: as
 * preferências gravadas precisam ser aplicadas ao elemento <html> ANTES da
 * primeira pintura. Com um módulo (que é adiado) o visitante veria a página
 * piscar no tamanho padrão antes de assumir a preferência dele.
 *
 * O estado vive em dois atributos de <html>, e todo o efeito visual é CSS:
 *   data-fonte="normal|grande|maior"
 *   data-contraste="alto"        (ausente quando desligado)
 *
 * Publica o evento 'vv:preferencias-alteradas' no document. Nenhum módulo
 * importa este arquivo — a comunicação entre módulos é por evento, porque o
 * armazenamento de estáticos em produção renomeia os arquivos com hash e o
 * Django não reescreve caminhos de import dentro de JavaScript.
 */

(function () {
    'use strict';

    const CHAVE = 'varrevila:preferencias';
    const NIVEIS_DE_FONTE = ['normal', 'grande', 'maior'];
    const PADRAO = { fonte: 'normal', contraste: false };

    const NOME_DO_NIVEL = {
        normal: 'padrão',
        grande: 'grande',
        maior: 'muito grande',
    };

    /**
     * Lê o que está gravado, tolerando ausência, JSON corrompido e navegador
     * com armazenamento bloqueado. Valores desconhecidos caem no padrão em vez
     * de deixar a página num estado que o CSS não sabe representar.
     */
    function leGravadas() {
        try {
            const bruto = window.localStorage.getItem(CHAVE);
            if (!bruto) {
                return Object.assign({}, PADRAO);
            }
            const lidas = JSON.parse(bruto);
            return {
                fonte: NIVEIS_DE_FONTE.includes(lidas.fonte) ? lidas.fonte : PADRAO.fonte,
                contraste: lidas.contraste === true,
            };
        } catch (erro) {
            return Object.assign({}, PADRAO);
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

    function aplica(preferencias) {
        const raiz = document.documentElement;
        raiz.setAttribute('data-fonte', preferencias.fonte);
        if (preferencias.contraste) {
            raiz.setAttribute('data-contraste', 'alto');
        } else {
            raiz.removeAttribute('data-contraste');
        }
    }

    let preferencias = leGravadas();
    aplica(preferencias);

    // ─────────────────────────────────────────────────────────────
    //  Controles — só depois que o documento existe
    // ─────────────────────────────────────────────────────────────

    function moveNivelDaFonte(passo) {
        const atual = NIVEIS_DE_FONTE.indexOf(preferencias.fonte);
        const novo = Math.min(NIVEIS_DE_FONTE.length - 1, Math.max(0, atual + passo));
        return NIVEIS_DE_FONTE[novo];
    }

    document.addEventListener('DOMContentLoaded', function () {
        const barra = document.querySelector('[data-barra-acessibilidade]');
        if (!barra) {
            return;
        }

        const aviso = barra.querySelector('[data-aviso-preferencia]');
        const botaoDeContraste = barra.querySelector('[data-acao="alternar-contraste"]');

        function anuncia(mensagem) {
            if (aviso) {
                aviso.textContent = mensagem;
            }
        }

        function sincronizaBotoes() {
            if (botaoDeContraste) {
                botaoDeContraste.setAttribute('aria-pressed', String(preferencias.contraste));
            }
            for (const botao of barra.querySelectorAll('[data-acao$="-fonte"]')) {
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
            sincronizaBotoes();
            anuncia(mensagem);
            document.dispatchEvent(new CustomEvent('vv:preferencias-alteradas', {
                detail: Object.assign({}, preferencias),
            }));
        }

        barra.addEventListener('click', function (evento) {
            const botao = evento.target.closest('[data-acao]');
            if (!botao || botao.disabled) {
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
                case 'alternar-contraste': {
                    const ligado = !preferencias.contraste;
                    altera(
                        { contraste: ligado },
                        ligado ? 'Alto contraste ativado.' : 'Alto contraste desativado.'
                    );
                    break;
                }
            }
        });

        sincronizaBotoes();
    });
})();
