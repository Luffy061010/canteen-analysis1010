<template>
  <div class="dashboard">
    <el-alert v-if="loadError" type="error" :closable="false" show-icon style="margin-bottom: 16px;">
      <template #title>首页数据加载失败</template>
      <div class="error-actions">
        <span>{{ loadError }}</span>
        <el-button size="small" type="danger" plain :loading="loading" @click="loadDashboard">重试</el-button>
      </div>
    </el-alert>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.totalStudents.toLocaleString() }}</div>
            <div class="stat-label">总学生数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">¥{{ statistics.latest24hAmount.toLocaleString() }}</div>
            <div class="stat-label">最近24小时消费总额</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.latest24hRecords.toLocaleString() }}</div>
            <div class="stat-label">最近24小时交易笔数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>24小时消费统计</span>
          </template>
          <div id="hourlyChart" class="chart-large"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card>
          <template #header>
            <span>消费层级占比</span>
          </template>
          <div id="levelPieChart" class="chart-small"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card>
          <template #header>
            <span>绩点直方图</span>
          </template>
          <div id="gpaHistogramChart" class="chart-small"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :lg="8">
        <el-card>
          <template #header>
            <span>漂移程度仪表盘</span>
          </template>
          <div id="driftGaugeChart" class="chart-small"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  getDashboardOverview
} from '@/api/user.js'

const statistics = ref({
  totalStudents: 0,
  latest24hAmount: 0,
  latest24hRecords: 0
})

const loading = ref(false)
const loadError = ref('')

const charts = {
  hourly: null,
  pie: null,
  histogram: null,
  gauge: null
}

let resizeHandler = null

const safeNumber = (v) => {
  const n = Number(v)
  return Number.isNaN(n) ? 0 : n
}

const parseTime = (record) => {
  const raw = record?.consumptionTime || record?.consumption_time || record?.consume_time || record?.consumeTime || ''
  if (!raw) return null
  if (typeof raw === 'string') {
    const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T')
    const date = new Date(normalized)
    if (!Number.isNaN(date.getTime())) return date
  }
  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

const quantile = (arr, q) => {
  if (!arr.length) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const idx = Math.floor((sorted.length - 1) * q)
  return sorted[idx]
}

const levelName = (value, q1, q2, q3) => {
  if (value <= q1) return '低消费'
  if (value <= q2) return '较低消费'
  if (value <= q3) return '中消费'
  return '高消费'
}

const extractClusterRows = (res) => {
  const root = res?.results || res?.data?.results || res?.povertyResults || res?.data?.povertyResults || []
  return Array.isArray(root) ? root : []
}

const extractDateRange = (records) => {
  const dates = records.map(parseTime).filter(Boolean).sort((a, b) => a - b)
  if (!dates.length) {
    return {
      latestDate: null,
      start: null,
      end: null
    }
  }
  const latestDate = dates[dates.length - 1]
  const end = new Date(latestDate)
  const start = new Date(latestDate)
  start.setDate(start.getDate() - 29)
  return { latestDate, start, end }
}

const formatDay = (d) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const buildRecentRange = (days = 30) => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - Math.max(1, Number(days || 30) - 1))
  return {
    timeBegin: formatDay(start),
    timeEnd: formatDay(end)
  }
}

const buildHourly = (records, targetDate) => {
  const hourly = new Array(24).fill(0)
  let recordCount = 0
  records.forEach((r) => {
    const t = parseTime(r)
    if (!t) return
    if (formatDay(t) !== targetDate) return
    const hour = t.getHours()
    hourly[hour] += safeNumber(r?.amount ?? r?.money ?? 0)
    recordCount += 1
  })
  return { hourly, recordCount }
}

const buildLatest24hStats = (records, latestDate) => {
  if (!latestDate) return { amount: 0, count: 0 }
  const endTs = latestDate.getTime()
  const startTs = endTs - 24 * 60 * 60 * 1000
  let amount = 0
  let count = 0

  records.forEach((r) => {
    const t = parseTime(r)
    if (!t) return
    const ts = t.getTime()
    if (ts < startTs || ts > endTs) return
    amount += safeNumber(r?.amount ?? r?.money ?? r?.consumeAmount ?? r?.consumptionAmount ?? 0)
    count += 1
  })

  return { amount, count }
}

const buildDailySeries = (records) => {
  const dailyMap = new Map()
  records.forEach((r) => {
    const t = parseTime(r)
    if (!t) return
    const day = formatDay(t)
    const amount = safeNumber(r?.amount ?? r?.money ?? 0)
    dailyMap.set(day, (dailyMap.get(day) || 0) + amount)
  })
  return Array.from(dailyMap.values())
}

const calcCvScore = (dailySeries) => {
  if (!Array.isArray(dailySeries) || dailySeries.length < 3) return 0
  const mean = dailySeries.reduce((s, v) => s + v, 0) / dailySeries.length
  if (mean <= 0) return 0
  const variance = dailySeries.reduce((s, v) => s + (v - mean) * (v - mean), 0) / dailySeries.length
  const std = Math.sqrt(variance)
  const cv = std / mean
  return Math.min(100, cv * 100)
}

const withTimeout = async (promise, ms, fallbackValue = null) => {
  let timer = null
  try {
    const timeoutPromise = new Promise((resolve) => {
      timer = setTimeout(() => resolve(fallbackValue), ms)
    })
    return await Promise.race([promise, timeoutPromise])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

const initOrGetChart = (id, key) => {
  const el = document.getElementById(id)
  if (!el) return null
  const existing = echarts.getInstanceByDom(el)
  charts[key] = existing || echarts.init(el)
  return charts[key]
}

const renderHourlyChart = (hourlyData) => {
  const chart = initOrGetChart('hourlyChart', 'hourly')
  if (!chart) return
  const x = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)
  const maxVal = Math.max(...hourlyData, 0)
  const maxIdx = hourlyData.findIndex(v => v === maxVal)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const point = params?.[0]
        if (!point) return ''
        return `${point.axisValue}<br/>消费额: ¥${Number(point.data || 0).toFixed(2)}`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '4%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: x,
      boundaryGap: false,
      axisLabel: { interval: 1, rotate: 35, color: '#606266' },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    yAxis: {
      type: 'value',
      name: '金额(元)',
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { color: '#eef2f8', type: 'dashed' } }
    },
    series: [
      {
        name: '消费额',
        type: 'line',
        smooth: true,
        data: hourlyData.map(v => Number(v.toFixed(2))),
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 3, color: '#3A7AFE' },
        itemStyle: { color: '#3A7AFE' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(58,122,254,0.30)' },
            { offset: 1, color: 'rgba(58,122,254,0.03)' }
          ])
        },
        markPoint: maxVal > 0
          ? {
            data: [{ coord: [maxIdx, Number(maxVal.toFixed(2))], value: `峰值 ¥${Number(maxVal).toFixed(2)}` }],
            symbolSize: 42,
            label: { color: '#fff', fontSize: 10 }
          }
          : undefined
      }
    ]
  })
}

const renderPieChart = (levelRows) => {
  const chart = initOrGetChart('levelPieChart', 'pie')
  if (!chart) return
  const counts = {
    '低消费': 0,
    '较低消费': 0,
    '中消费': 0,
    '高消费': 0
  }
  levelRows.forEach((i) => {
    const key = i?.level || i?.name
    const value = safeNumber(i?.value ?? 1)
    if (key && counts[key] !== undefined) {
      counts[key] += value
    }
  })

  const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0)
  if (!total) {
    chart.setOption({
      title: {
        text: '暂无分层数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#909399', fontSize: 14 }
      },
      series: []
    })
    return
  }

  chart.setOption({
    title: { show: false },
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      type: 'scroll',
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12 }
    },
    series: [
      {
        type: 'pie',
        center: ['50%', '46%'],
        radius: ['34%', '62%'],
        data: Object.keys(counts).map(k => ({ name: k, value: counts[k] })),
        minShowLabelAngle: 10,
        avoidLabelOverlap: true,
        labelLine: { length: 10, length2: 10 },
        label: {
          formatter: (params) => `${params.name}\n${params.value}人 (${Number(params.percent || 0).toFixed(1)}%)`,
          fontSize: 11
        },
        labelLayout: { hideOverlap: true },
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 }
      }
    ]
  })
}

const renderHistogram = (gpas) => {
  const chart = initOrGetChart('gpaHistogramChart', 'histogram')
  if (!chart) return

  if (!Array.isArray(gpas) || !gpas.length) {
    chart.setOption({
      title: {
        text: '暂无绩点分布数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#909399', fontSize: 14 }
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: []
    })
    return
  }

  const bins = [0, 0, 0, 0, 0, 0]
  gpas.forEach((g) => {
    if (g < 2.0) bins[0] += 1
    else if (g < 2.5) bins[1] += 1
    else if (g < 3.0) bins[2] += 1
    else if (g < 3.5) bins[3] += 1
    else if (g <= 4.0) bins[4] += 1
    else bins[5] += 1
  })

  chart.setOption({
    title: { show: false },
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '4%', bottom: '5%', containLabel: true },
    xAxis: { show: true, type: 'category', data: ['<2.0', '2.0-2.5', '2.5-3.0', '3.0-3.5', '3.5-4.0', '>4.0'] },
    yAxis: { show: true, type: 'value', name: '人数' },
    series: [
      {
        type: 'bar',
        data: bins,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#54D0A0' },
            { offset: 1, color: '#2CB67D' }
          ])
        },
        barMaxWidth: 28
      }
    ]
  })
}

const renderGauge = (driftScore, hasData = true, note = '') => {
  const chart = initOrGetChart('driftGaugeChart', 'gauge')
  if (!chart) return

  const safeScore = Number.isFinite(Number(driftScore)) ? Number(driftScore) : 0
  const subtext = note || (hasData ? '漂移指数越高，行为变化越明显' : '样本不足，先展示默认值')
  chart.setOption({
    title: {
      text: hasData ? '漂移指数' : '暂无充分样本',
      subtext,
      left: 'center',
      top: 12,
      textStyle: { color: '#606266', fontSize: 13, fontWeight: 500 },
      subtextStyle: { color: '#909399', fontSize: 11 }
    },
    series: [
      {
        type: 'gauge',
        min: 0,
        max: 100,
        progress: { show: true, width: 14 },
        axisLine: {
          lineStyle: {
            width: 14,
            color: [[1, '#e6ebf3']]
          }
        },
        splitLine: { distance: -16, length: 10, lineStyle: { width: 1, color: '#999' } },
        axisTick: { distance: -16, length: 4, lineStyle: { color: '#999' } },
        detail: { valueAnimation: true, formatter: '{value}%', color: '#303133', fontSize: 24, offsetCenter: [0, '58%'] },
        data: [{ value: Number(safeScore.toFixed(1)), name: '漂移指数' }]
      }
    ]
  })
}

const loadDashboard = async () => {
  loading.value = true
  loadError.value = ''

  try {
    await nextTick()
    // 先渲染默认图，避免慢请求期间出现空白区域。
    renderHourlyChart(new Array(24).fill(0))
    renderPieChart([])
    renderHistogram([])
    renderGauge(0, false, '正在加载数据...')

    const overview = await withTimeout(getDashboardOverview({}).catch(() => null), 12000, null)

    if (!overview || typeof overview !== 'object') {
      throw new Error('overview unavailable')
    }

    const stats = overview.statistics || {}
    const hourly = Array.isArray(overview?.hourly?.amount) ? overview.hourly.amount : new Array(24).fill(0)
    const levelRows = Array.isArray(overview.levelDistribution) ? overview.levelDistribution : []
    const gpaLabels = Array.isArray(overview?.gpaHistogram?.labels) ? overview.gpaHistogram.labels : ['<2.0', '2.0-2.5', '2.5-3.0', '3.0-3.5', '3.5-4.0', '>4.0']
    const gpaValues = Array.isArray(overview?.gpaHistogram?.values) ? overview.gpaHistogram.values : [0, 0, 0, 0, 0, 0]
    const drift = overview.drift || {}

    statistics.value = {
      totalStudents: safeNumber(stats.totalStudents),
      latest24hAmount: safeNumber(stats.latest24hAmount),
      latest24hRecords: safeNumber(stats.latest24hRecords)
    }

    renderHourlyChart(hourly)
    renderPieChart(levelRows)

    // 复用现有柱状图风格，按后端分箱数据绘制。
    const chart = initOrGetChart('gpaHistogramChart', 'histogram')
    if (chart) {
      chart.setOption({
        title: { show: false },
        tooltip: { trigger: 'axis' },
        grid: { left: '5%', right: '4%', bottom: '5%', containLabel: true },
        xAxis: { show: true, type: 'category', data: gpaLabels },
        yAxis: { show: true, type: 'value', name: '人数' },
        series: [
          {
            type: 'bar',
            data: gpaValues,
            itemStyle: {
              borderRadius: [6, 6, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#54D0A0' },
                { offset: 1, color: '#2CB67D' }
              ])
            },
            barMaxWidth: 28
          }
        ]
      })
    }

    renderGauge(safeNumber(drift.score), !!drift.hasData, drift.note || '')

    if (!safeNumber(stats.totalStudents) && !safeNumber(stats.latest24hRecords)) {
      loadError.value = '未获取到有效首页数据，请检查后端服务与数据库连接。'
    }
  } catch (error) {
    console.error('首页数据加载失败:', error)
    loadError.value = '请检查后端服务后重试。'
    renderGauge(0, false, '加载失败，请重试')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDashboard()

  resizeHandler = () => {
    Object.values(charts).forEach((c) => {
      if (c && typeof c.resize === 'function') c.resize()
    })
  }
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  Object.values(charts).forEach((c) => {
    if (c && typeof c.dispose === 'function') c.dispose()
  })
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard :deep(.el-card) {
  border-radius: 12px;
  border: 1px solid #edf1f7;
  box-shadow: 0 6px 18px rgba(18, 38, 63, 0.05);
}

.dashboard :deep(.el-card__header) {
  font-weight: 600;
  color: #2f3a4f;
}

.stat-card {
  min-height: 120px;
  background: linear-gradient(145deg, #ffffff 0%, #f7faff 100%);
}

.stat-content {
  text-align: center;
  padding: 12px 0;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.chart-large {
  width: 100%;
  height: 390px;
}

.chart-small {
  width: 100%;
  height: 340px;
}

.error-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 1200px) {
  .chart-large {
    height: 340px;
  }

  .chart-small {
    height: 300px;
  }
}
</style>
