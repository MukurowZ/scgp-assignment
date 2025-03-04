<template lang="pug">
.index
  SensorChart(
    :chartData="computedChartsData.temperature"
  )

  SensorChart(
    :chartData="computedChartsData.humidity"
  )

  SensorChart(
    :chartData="computedChartsData.airQuality"
  )
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { useFetch } from '@vueuse/core';
import SensorChart from '@/components/SensorChart.vue';

const BACKEND_URL = import.meta.env.VITE_APP_BACKEND_URL;
const EMPTY_CHART_DATA = {
  labels: [],
  datasets: [],
}

interface SensorData { 
  processed_data: { timestamp: string; value: number }[],
  anomalies: { timestamp: string; value: number }[] 
}

const { isFetching, data } = useFetch<{
  total_logs: number,
  temperature: SensorData,
  humidity: SensorData,
  air_quality: SensorData,
}>(`${BACKEND_URL}/sensor/processed`, {
  initialData: {
    total_logs: 0,
    temperature: { processed_data: [], anomalies: [] },
    humidity: { processed_data: [], anomalies: [] },
    air_quality: { processed_data: [], anomalies: [] },
  },
});

function mapDataset({
  label,
  sensorData,
}: { label: string; sensorData: SensorData }) {
  const labels = sensorData.processed_data.map(item => item.timestamp) ?? [];
  const values = sensorData.processed_data.map(item => item.value);
  const anomalyTimestamps = sensorData.anomalies.map(anomaly => anomaly.timestamp);
  const anomalyData = sensorData.anomalies.map(anomaly => anomaly.value);
  const appendAnomaliesData = [...values, ...anomalyData];

  return {
    labels,
    datasets: [{
      label,
      data: appendAnomaliesData,
      anomalyTimestamps,
      pointBackgroundColor: appendAnomaliesData.map((value, index) => {
        const hitAnomaly = anomalyTimestamps.findIndex((tm) => tm === labels[index]);
        if (hitAnomaly > -1) {
          if (appendAnomaliesData[index] === anomalyData[hitAnomaly])
            return 'rgba(255, 2, 1, 0.50)' /* This will highlight anomalies */
        }
        return 'rgba(0, 167, 255)'
      }),
      pointRadius: appendAnomaliesData.map((value, index) => {
        const hitAnomaly = anomalyTimestamps.findIndex((tm) => tm === labels[index]);
        if (hitAnomaly > -1) {
          if (appendAnomaliesData[index] === anomalyData[hitAnomaly])
            return 6;
        }
        return 3;
      }),
      pointHoverRadius: appendAnomaliesData.map((value, index) => {
        const hitAnomaly = anomalyTimestamps.findIndex((tm) => tm === labels[index]);
        if (hitAnomaly > -1) {
          if (appendAnomaliesData[index] === anomalyData[hitAnomaly])
            return 8
        }
        return 4
      }),
      borderColor: 'rgba(89, 89, 92, 0.2)',
      backgroundColor: 'rgba(89, 89, 92, 0.1)',
    }]
  };
}

const computedChartsData = computed(() => {
  if (isFetching.value || !data.value) return { 
    temperature: { ...EMPTY_CHART_DATA }, 
    humidity: { ...EMPTY_CHART_DATA }, 
    airQuality: { ...EMPTY_CHART_DATA } 
  };

  const { 
    temperature, 
    humidity, 
    air_quality: airQuality 
  } = typeof data.value === 'string' ? JSON.parse(data.value) : data.value;

  return {
    temperature: mapDataset({ label: 'Temperature', sensorData: temperature }),
    humidity: mapDataset({ label: 'Humidity', sensorData: humidity }),
    airQuality: mapDataset({ label: 'Air Quality', sensorData: airQuality }),
  };
});
</script>