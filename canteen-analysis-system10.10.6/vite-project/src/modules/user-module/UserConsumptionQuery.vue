<template>
  <div class="user-consumption-page">
    <el-card>
      <template #header>
        <span>个人消费信息查询</span>
      </template>

      <el-form :model="form" inline>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="query">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-row :gutter="12" style="margin-bottom: 12px;">
        <el-col :span="6">
          <el-card shadow="never">
            <div class="metric-label">总消费额</div>
            <div class="metric-value">¥{{ summary.total }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="metric-label">日均消费额</div>
            <div class="metric-value">¥{{ summary.avgDaily }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="metric-label">趋势斜率</div>
            <div class="metric-value">{{ summary.slope }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="metric-label">最常消费窗口</div>
            <div class="metric-value">{{ summary.favoriteWindow }}</div>
          </el-card>
        </el-col>
      </el-row>

      <div ref="chartRef" class="trend-chart" />

      <el-divider />

      <el-table :data="records" style="width: 100%">
        <el-table-column prop="consume_time" label="时间" width="180" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="window" label="窗口" width="120" />
        <el-table-column prop="mealType" label="餐别" width="100" />
      </el-table>

      <el-pagination
        style="margin-top: 12px"
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getConsumptionData } from '@/api/user'
import { getStoredUserInfo } from '@/utils/auth'

const userInfo = getStoredUserInfo() || {}
const uid = userInfo.username || userInfo.userId || ''

const form = ref({ start: '', end: '' })
const records = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const chartRef = ref(null)
let chartIns = null

const summary = ref({
  total: 0,
  avgDaily: 0,
  slope: 0,
  favoriteWindow: '-'
})

const safeNum = (v) => {
  const n = Number(v)
  return Number.isNaN(n) ? 0 : n
}

const queryParams = (forAll = false) => {
  const p = {
    studentId: uid,
    page: forAll ? 1 : currentPage.value,
    pageSize: forAll ? 5000 : pageSize.value
  }
  if (form.value.start) p.timeBegin = form.value.start
  if (form.value.end) p.timeEnd = form.value.end
  return p
}

const renderChart = (dailyRows) => {
  if (!chartRef.value) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)

  const dates = dailyRows.map(i => i.date)
  const amounts = dailyRows.map(i => i.value)

  chartIns.setOption({
    title: { text: '个人消费变化' },
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 35 } },
    yAxis: { type: 'value', name: '金额(元)' },
    series: [
      {
        name: '消费金额',
        type: 'line',
        smooth: true,
        data: amounts,
        lineStyle: { width: 3, color: '#409EFF' },
        areaStyle: { opacity: 0.1 }
      }
    ]
  })
}

const calcSummary = (allRows) => {
  const dailyMap = {}
  const winMap = {}

  allRows.forEach((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    const day = String(timeRaw).split('T')[0].split(' ')[0]
    const amount = safeNum(r.amount || r.money || 0)
    const win = r.window || r.windowId || r.window_id || '未知'
    if (day) dailyMap[day] = (dailyMap[day] || 0) + amount
    winMap[win] = (winMap[win] || 0) + 1
  })

  const dailyRows = Object.keys(dailyMap)
    .sort((a, b) => a.localeCompare(b))
    .map(d => ({ date: d, value: Number(dailyMap[d].toFixed(2)) }))

  const totalCost = dailyRows.reduce((s, i) => s + i.value, 0)
  const avgDaily = dailyRows.length ? totalCost / dailyRows.length : 0

  let slope = 0
  if (dailyRows.length >= 2) {
    const n = dailyRows.length
    const xMean = (n - 1) / 2
    const yMean = totalCost / n
    let num = 0
    let den = 0
    for (let i = 0; i < n; i += 1) {
      num += (i - xMean) * (dailyRows[i].value - yMean)
      den += (i - xMean) * (i - xMean)
    }
    slope = den === 0 ? 0 : num / den
  }

  let favoriteWindow = '-'
  let maxCount = 0
  Object.keys(winMap).forEach((k) => {
    if (winMap[k] > maxCount) {
      maxCount = winMap[k]
      favoriteWindow = k
    }
  })

  summary.value = {
    total: Number(totalCost.toFixed(2)),
    avgDaily: Number(avgDaily.toFixed(2)),
    slope: Number(slope.toFixed(3)),
    favoriteWindow
  }

  nextTick(() => renderChart(dailyRows))
}

const query = async () => {
  if (!uid) return

  const [pageRes, allRes] = await Promise.all([
    getConsumptionData(queryParams(false)),
    getConsumptionData(queryParams(true))
  ])

  const pageRows = pageRes?.records || pageRes?.data?.records || pageRes?.data || []
  const allRows = allRes?.records || allRes?.data?.records || allRes?.data || []

  const list = Array.isArray(pageRows) ? pageRows : []
  const allList = Array.isArray(allRows) ? allRows : []

  total.value = Number(pageRes?.total || pageRes?.totalCount || pageRes?.data?.total || allList.length || 0)

  records.value = list.map((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    return {
      consume_time: String(timeRaw).replace('T', ' '),
      amount: Number(safeNum(r.amount || r.money || 0)).toFixed(2),
      window: r.window || r.windowId || r.window_id || '-',
      mealType: r.mealType || r.meal_type || '-'
    }
  })

  calcSummary(allList)
}

const reset = () => {
  form.value = { start: '', end: '' }
  currentPage.value = 1
  pageSize.value = 20
  query()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  query()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  query()
}

onMounted(() => {
  query()
  window.addEventListener('resize', () => {
    if (chartIns) chartIns.resize()
  })
})

onBeforeUnmount(() => {
  if (chartIns) chartIns.dispose()
})
</script>

<style scoped>
.user-consumption-page {
  padding: 16px;
}

.metric-label {
  color: #909399;
  font-size: 13px;
}

.metric-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.trend-chart {
  width: 100%;
  height: 340px;
}
</style>
