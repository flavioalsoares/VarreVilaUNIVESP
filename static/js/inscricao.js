/*
 * Inscrição em mutirão sem recarregar a página.
 *
 * O formulário já funciona sozinho: sem JavaScript o navegador envia o POST
 * e o servidor devolve a página inteira. Este módulo só encurta o caminho —
 * manda o mesmo POST pedindo JSON e troca o trecho do aviso.
 *
 * Por isso nada aqui é condição para a inscrição acontecer. Se o arquivo não
 * carregar, o botão continua enviando o formulário do jeito antigo.
 *
 * Não importa outros módulos de propósito: em produção o WhiteNoise serve os
 * estáticos com o nome carimbado por hash, e o Django reescreve caminhos
 * dentro de CSS mas não dentro de `import` de JavaScript — um import quebra
 * no deploy sem quebrar no desenvolvimento.
 */

const formulario = document.querySelector('[data-inscricao]');
if (formulario) {
    preparar(formulario);
}

function preparar(form) {
    const botao = form.querySelector('[data-inscricao-enviar]');
    const aviso = form.querySelector('[data-inscricao-aviso]');
    const textoOriginal = botao ? botao.innerHTML : '';

    form.addEventListener('submit', async (evento) => {
        evento.preventDefault();
        limparErros(form);

        if (botao) {
            botao.disabled = true;
            botao.textContent = 'Enviando…';
        }

        try {
            const resposta = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    Accept: 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });
            const dados = await resposta.json();

            if (dados.ok) {
                mostrarSucesso(form, aviso, dados.mensagem);
            } else {
                mostrarErros(form, aviso, dados.erros || {});
            }
        } catch {
            // Rede fora, servidor mudo: o formulário continua preenchido e
            // o envio comum segue disponível — avisar é melhor do que
            // deixar a pessoa olhando para um botão que não responde.
            mostrarErros(form, aviso, {
                __all__: ['Não foi possível enviar agora. Verifique sua conexão e tente de novo.'],
            });
        } finally {
            if (botao) {
                botao.disabled = false;
                botao.innerHTML = textoOriginal;
            }
        }
    });
}

function limparErros(form) {
    for (const marca of form.querySelectorAll('[data-erro-de]')) {
        marca.remove();
    }
    for (const campo of form.querySelectorAll('[aria-invalid]')) {
        campo.removeAttribute('aria-invalid');
        campo.removeAttribute('aria-describedby');
    }
}

function mostrarSucesso(form, aviso, mensagem) {
    const caixa = form.parentElement;
    const confirmacao = document.createElement('p');
    confirmacao.className = 'inscricao-aviso ok';
    // role="status" e não "alert": a mudança é esperada, resultado de um
    // clique da própria pessoa. "alert" interromperia a leitura em curso.
    confirmacao.setAttribute('role', 'status');
    confirmacao.setAttribute('tabindex', '-1');
    confirmacao.textContent = mensagem;

    form.replaceWith(confirmacao);
    if (aviso && aviso.parentElement === caixa) {
        aviso.remove();
    }
    // O foco precisa ir junto: sem isso quem navega por teclado continuaria
    // num botão que não existe mais, e o leitor de tela não teria para onde
    // levar a pessoa depois do anúncio.
    confirmacao.focus();
}

function mostrarErros(form, aviso, erros) {
    const gerais = [];

    for (const [campo, mensagens] of Object.entries(erros)) {
        if (campo === '__all__') {
            gerais.push(...mensagens);
            continue;
        }
        const entrada = form.querySelector(`[name="${campo}"]`);
        if (!entrada) {
            gerais.push(...mensagens);
            continue;
        }
        const marca = document.createElement('span');
        marca.className = 'erro-campo';
        marca.dataset.erroDe = campo;
        marca.id = `erro-${campo}`;
        marca.textContent = mensagens[0];
        entrada.insertAdjacentElement('afterend', marca);
        entrada.setAttribute('aria-invalid', 'true');
        entrada.setAttribute('aria-describedby', marca.id);
    }

    if (aviso) {
        if (gerais.length > 0) {
            aviso.textContent = gerais.join(' ');
            aviso.hidden = false;
            aviso.focus();
            return;
        }
        aviso.hidden = true;
        aviso.textContent = '';
    }

    // Sem erro geral, o foco vai para o primeiro campo recusado — é onde a
    // pessoa tem o que fazer.
    const primeiro = form.querySelector('[aria-invalid="true"]');
    if (primeiro) {
        primeiro.focus();
    }
}
