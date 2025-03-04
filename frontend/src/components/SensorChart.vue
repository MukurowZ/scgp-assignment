<template lang="pug">
.sensor-chart
  Scatter(
    :data="failsafeDataset"
    :options="chartOptions"
  )
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { Scatter } from 'vue-chartjs';
import { Chart as ChartJS, registerables } from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import 'chartjs-adapter-date-fns';

ChartJS.register(...registerables, zoomPlugin);

interface ChartData {
  labels: string[],
  datasets: {
    label: string,
    data: number[],
    anomalyTimestamps?: string[]
  }[]
}

const props = defineProps<{
  chartData: ChartData;
}>();

const failsafeDataset = computed(() => {
  if (!props.chartData.datasets.length) return props.chartData;

  const dataset = props.chartData.datasets[0];

  return {
    ...props.chartData,
    datasets: [{
      ...dataset,
    }]
  };
});

const chartOptions = {
  responsive: true,
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  },
  plugins: {
    zoom: {
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: 'xy',
      },
      pan: {
        enabled: true,
        mode: 'xy',
      }
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const dataIndex = context.dataIndex;
          const dataset = props.chartData.datasets[0];
          const isAnomaly = dataset.anomalyTimestamps?.includes(props.chartData.labels[dataIndex]);

          return isAnomaly 
            ? `🚨 ANOMALY - Value: ${context.parsed.y}` 
            : `Value: ${context.parsed.y}`;
        }
      }
    }
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'minute',
        displayFormats: {
          minute: 'HH:mm'
        }
      },
      title: {
        display: true,
        text: 'Timestamp'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Value'
      }
    }
  },
};
</script>

<style lang="css">
.sensor-chart {
  position: relative;
  height: 400px;
  width: 100%;
}
</style>