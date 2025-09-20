// ... (código existente do menu e dos outros gráficos) ...

// Gráfico de Ranking de Corretores (Barras)
const rankingCtx = document.getElementById("rankingChart");
if (rankingCtx) {
  new Chart(rankingCtx, {
    type: "bar",
    data: {
      labels: ["Bruno Costa", "Ana Silva", "Carla Dias"], // Nomes dos corretores
      datasets: [
        {
          label: "Total Vendido (R$)",
          data: [800000, 450000, 0], // Valores de venda correspondentes
          backgroundColor: [
            "rgba(40, 167, 69, 0.7)", // Verde
            "rgba(0, 123, 255, 0.7)", // Azul
            "rgba(255, 193, 7, 0.7)", // Amarelo
          ],
          borderColor: [
            "rgba(40, 167, 69, 1)",
            "rgba(0, 123, 255, 1)",
            "rgba(255, 193, 7, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      indexAxis: "y", // Transforma em gráfico de barras horizontais
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            callback: function (value, index, values) {
              return "R$ " + value / 1000 + "k"; // Formata o eixo X para 'R$ 500k'
            },
          },
        },
      },
      plugins: {
        legend: {
          display: false, // Oculta a legenda, pois o label do dataset já é claro
        },
      },
    },
  });
}
