<template>
  <div ref="chartContainer" :class="['chart-container', className]" :style="containerStyle"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // 图表配置
  options: {
    type: Object,
    required: true
  },
  // 容器样式
  containerStyle: {
    type: Object,
    default: () => ({
      width: '100%',
      height: '400px'
    })
  },
  // 自定义类名
  className: {
    type: String,
    default: ''
  },
  // 是否显示加载动画
  loading: {
    type: Boolean,
    default: false
  },
  // 加载动画文本
  loadingText: {
    type: String,
    default: '加载中...'
  },
  // 主题
  theme: {
    type: [String, Object],
    default: 'default'
  },
  // 是否启用响应式
  responsive: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['chart-ready', 'chart-click', 'chart-resize'])

const chartContainer = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return

  // 销毁现有实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新实例
  chartInstance = echarts.init(chartContainer.value, props.theme)

  // 设置配置
  chartInstance.setOption(props.options, true)

  // 显示加载状态
  if (props.loading) {
    chartInstance.showLoading({
      text: props.loadingText,
      color: '#409EFF',
      textColor: '#303133',
      maskColor: 'rgba(255, 255, 255, 0.8)'
    })
  } else {
    chartInstance.hideLoading()
  }

  // 绑定事件
  bindChartEvents()

  emit('chart-ready', chartInstance)
}

// 绑定图表事件
const bindChartEvents = () => {
  if (!chartInstance) return

  // 点击事件
  chartInstance.off('click')
  chartInstance.on('click', (params) => {
    emit('chart-click', params)
  })
}

// 更新图表
const updateChart = () => {
  if (!chartInstance) return

  chartInstance.setOption(props.options, true)

  if (props.loading) {
    chartInstance.showLoading()
  } else {
    chartInstance.hideLoading()
  }
}

// 响应式调整
const handleResize = () => {
  if (chartInstance && props.responsive) {
    chartInstance.resize()
    emit('chart-resize')
  }
}

// 销毁图表
const destroyChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()

    // 监听窗口变化
    if (props.responsive) {
      window.addEventListener('resize', handleResize)
    }
  })
})

onUnmounted(() => {
  destroyChart()
  if (props.responsive) {
    window.removeEventListener('resize', handleResize)
  }
})

// 监听属性变化
watch(() => props.options, (newOptions) => {
  updateChart()
}, { deep: true })

watch(() => props.loading, (newLoading) => {
  if (chartInstance) {
    if (newLoading) {
      chartInstance.showLoading()
    } else {
      chartInstance.hideLoading()
    }
  }
})

watch(() => props.theme, (newTheme) => {
  initChart()
})

// 暴露方法给父组件
defineExpose({
  getInstance: () => chartInstance,
  resize: handleResize,
  dispose: destroyChart
})
</script>

<style scoped>
.chart-container {
  position: relative;
}
</style>