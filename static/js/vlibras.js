/**
 * Inicialização do VLibras, o tradutor para Libras do governo federal.
 *
 * O plugin em si vem de vlibras.gov.br, carregado como script clássico
 * antes deste módulo — módulos executam depois dos scripts clássicos, então
 * window.VLibras já existe aqui. Se o serviço estiver fora do ar, o guarda
 * abaixo evita erro no console e a página segue normal.
 *
 * A única razão de este arquivo existir é não ter JavaScript inline no
 * template: a chamada de inicialização do widget é uma linha, e o projeto
 * mantém todo comportamento em static/js.
 */

if (window.VLibras && typeof window.VLibras.Widget === 'function') {
    new window.VLibras.Widget('https://vlibras.gov.br/app');
}
