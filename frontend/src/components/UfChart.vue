<template>
  <div class="chart-container">
    <Bar v-if="loaded" :data="chartData" :options="chartOptions" />
    <p v-else>Carregando gráfico...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import { getStatsUF } from '../services/api';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const loaded = ref(false);
const chartData = ref(null);
const chartOptions = { 
  responsive: true, 
  maintainAspectRatio: false,
  layout: {
    padding: {
      left: 10,
      right: 20,
      top: 20,
      bottom: 10
    }
  },
  plugins: {
    legend: {
      position: 'top',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: function(context) {
          let label = context.dataset.label || '';
          if (label) {
            label += ': ';
          }
          if (context.parsed.y !== null) {
            label += new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(context.parsed.y);
          }
          return label;
        }
      }
    }
  },
  scales: {
    y: {
      ticks: {
        callback: function(value) {
          if (Math.abs(value) >= 1.0e+9) {
            return 'R$ ' + (value / 1.0e+9).toFixed(1) + 'B';
          }
          if (Math.abs(value) >= 1.0e+6) {
            return 'R$ ' + (value / 1.0e+6).toFixed(1) + 'M';
          }
          return value;
        }
      }
    }
  }
};

onMounted(async () => {
  try {
    const { data } = await getStatsUF();
    chartData.value = {
      labels: data.map(item => item.uf),
      datasets: [{
        label: 'Despesas por UF (R$)',
        backgroundColor: '#42b983',
        data: data.map(item => item.total)
      }]
    };
    loaded.value = true;
  } catch (e) {
    console.error("Erro ao carregar dados do gráfico", e);
  }
});
</script>
