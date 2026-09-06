/**
 * Gráfico de barras da evolução mensal de lixo recolhido, no painel interno.
 *
 * Extraído de templates/dashboard/index.html. Depende do Chart.js, carregado
 * como script clássico em templates/base.html — que executa antes deste módulo.
 *
 * Os dados chegam por elementos json_script escritos pelo Django, o que evita
 * interpolar valores do banco dentro de JavaScript.
 */

const canvas = document.getElementById('graficoMensal');

function leDados(id) {
    const elemento = document.getElementById(id);
    return elemento ? JSON.parse(elemento.textContent) : [];
}

if (canvas && typeof Chart !== 'undefined') {
    const rotulos = leDados('labels-data');
    const valores = leDados('dados-data');

    new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: rotulos.length ? rotulos : ['Sem dados'],
            datasets: [{
                label: 'Lixo coletado (kg)',
                data: valores.length ? valores : [0],
                backgroundColor: 'rgba(166, 206, 57, 0.75)',
                borderColor: 'rgba(40, 41, 41, 1)',
                borderWidth: 1,
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });
}
