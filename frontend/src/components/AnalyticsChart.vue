<template>
  <div class="card border-0 shadow-sm rounded-3 p-4 h-100">
    <h5 class="fw-bold mb-3 text-dark">{{ title }}</h5>
    <div class="chart-container position-relative" style="min-height: 250px;">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import {
  Chart,
  DoughnutController,
  BarController,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js'

Chart.register(
  DoughnutController,
  BarController,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
)

const props = defineProps({
  title: { type: String, default: 'Trekking Analytics' },
  type: { type: String, default: 'doughnut' },
  data: { type: Object, required: true }
})

const canvasRef = ref(null)
let chartInstance = null

const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
  }

  if (!canvasRef.value) return

  chartInstance = new Chart(canvasRef.value, {
    type: props.type,
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { family: 'Plus Jakarta Sans', size: 12 } }
        }
      }
    }
  })
}

onMounted(renderChart)
watch(() => props.data, renderChart, { deep: true })
</script>

