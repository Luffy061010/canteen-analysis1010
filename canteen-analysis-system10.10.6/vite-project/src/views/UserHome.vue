<template>
  <div class="user-home" style="padding:16px">
    <el-card>
      <template #header>
        <span>我的消费 - 最近 7 天</span>
      </template>
      <div style="display:flex;gap:12px;align-items:center">
        <el-date-picker v-model="range" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD"/>
        <el-button type="primary" @click="loadRecent">刷新</el-button>
      </div>
        <div style="width:100%;height:320px;margin-top:12px" ref="chartContainer"></div>
    </el-card>

    <el-card style="margin-top:16px">
      <template #header>
        <span>我的消费明细</span>
      </template>
      <el-table :data="records" style="width:100%">
        <el-table-column prop="consume_time" label="时间" width="180"/>
        <el-table-column prop="amount" label="金额" width="120"/>
        <el-table-column prop="window" label="窗口" width="120"/>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getConsumption, getConsumptionData } from '@/api/user.js'
import { getStoredUserInfo } from '@/utils/auth'

const userInfo = getStoredUserInfo() || {}
const uid = userInfo.username || ''

const range = ref([new Date(Date.now() - 6 * 24 * 3600).toISOString().slice(0,10), new Date().toISOString().slice(0,10)])
const trend = ref([])
const records = ref([])
const chartContainer = ref(null)
let chartInstance = null

const loadRecent = async () => {
  try {
    const params = { studentId: uid, timeBegin: range.value[0], timeEnd: range.value[1] }
    const stats = await getConsumption(params)
    // stats 中可能包含 daily series 或 total；我们尝试从返回的 chartData 或 records 中构建简单日序列
    // 如果没有可用结构，则用聚合的单条数据显示
    const days = []
    // 尝试从 stats.chartData.values.actual
    const cds = stats?.chartData?.dates || []
    const vals = stats?.chartData?.values?.actual || []
    if (Array.isArray(cds) && cds.length) {
      trend.value = cds.map((d, i) => ({ date: d, amount: vals[i] ?? 0 }))
    } else {
      trend.value = [{ date: range.value[0] + ' ~ ' + range.value[1], amount: stats?.totalAmount || 0 }]
    }

    // 更新图表
    await nextTick()
    renderChart()

    const table = await getConsumptionData(params)
    const raw = table?.records || table?.data || []
    records.value = raw.map(r => ({ consume_time: (r.consumption_time || r.consume_time || '').replace('T',' '), amount: (r.amount || r.money || 0).toFixed ? Number(r.amount || r.money || 0).toFixed(2) : r.amount, window: r.window || r.windowId || r.window_id || '-' }))
  } catch (e) {
    console.error('加载用户消费失败', e)
  }
}

onMounted(() => {
  if (!uid) return
  loadRecent()
  // 初始化空图
  chartInstance = null
})

watch(trend, () => {
  // 当数据变化时重新渲染
  nextTick().then(() => renderChart())
})

function renderChart() {
  if (!chartContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
  }
  const dates = trend.value.map(i => i.date)
  const amounts = trend.value.map(i => Number(i.amount) || 0)
  const option = {
    title: { text: '最近消费趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    series: [{ name: '消费', type: 'line', data: amounts, smooth: true, areaStyle: {} }]
  }
  chartInstance.setOption(option)
}
</script>

<style scoped>
.user-home { padding: 12px }
</style>
