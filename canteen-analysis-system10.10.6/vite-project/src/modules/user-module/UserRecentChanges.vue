<template>
  <div>
    <div style="display:flex;gap:12px;align-items:center">
      <el-date-picker v-model="range" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD"/>
      <el-button type="primary" @click="load">刷新</el-button>
    </div>

    <el-card style="margin-top:12px">
      <template #header>最近消费趋势</template>
      <div ref="chart" style="width:100%;height:320px"></div>
      <div style="margin-top:12px">总额：¥{{ total }}，平均日消费：¥{{ avgDaily }}，趋势斜率：{{ slope }}，最常去窗口：{{ trendMeta.busiestWindow }}（次数：{{ trendMeta.visits }}）</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { getConsumptionData } from '@/api/user'
import * as echarts from 'echarts'
import { getStoredUserInfo } from '@/utils/auth'

const userInfo = getStoredUserInfo() || {}
const uid = userInfo.username || userInfo.userId || ''

const range = ref([])
const chart = ref(null)
let chartIns = null
const total = ref(0)
const avgDaily = ref(0)
const slope = ref(0)
const trendMeta = ref({ busiestWindow: '-', visits: 0 })

const render = (dates, series) => {
  if (!chart.value) return
  if (!chartIns) chartIns = echarts.init(chart.value)
  const option = { title:{text:'最近消费变化'}, tooltip:{trigger:'axis'}, xAxis:{type:'category',data:dates}, yAxis:{type:'value'}, series:[{type:'line',data:series,smooth:true}] }
  chartIns.setOption(option)
}

const fetchAllRecords = async (baseParams) => {
  const pageSize = 1000
  const maxPages = 50
  let page = 1
  let all = []
  let total = null
  while (page <= maxPages) {
    const res = await getConsumptionData({ ...baseParams, page, pageSize })
    const raw = res?.records || res?.data?.records || res?.data || res || []
    const records = Array.isArray(raw) ? raw : []
    const totalVal = res?.total || res?.totalCount || res?.data?.total || res?.data?.totalCount
    if (totalVal !== undefined && totalVal !== null) total = Number(totalVal)
    all = all.concat(records)
    if (records.length < pageSize) break
    if (total && all.length >= total) break
    page += 1
  }
  return all
}

const load = async () => {
  if (!uid) return
  try {
    // 查询明细数据（尽量拉取足够范围内的记录）
    const params = { studentId: uid }
    if (range.value && range.value.length === 2) {
      params.timeBegin = range.value[0]
      params.timeEnd = range.value[1]
    }
    const raw = await fetchAllRecords(params)

    // 聚合为按日序列
    const dailyMap = {}
    raw.forEach(r => {
      const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || r.consumptionTimeStr || ''
      let dstr = ''
      if (typeof timeRaw === 'string') dstr = timeRaw.split('T')[0]
      else if (timeRaw) dstr = new Date(timeRaw).toISOString().slice(0,10)
      if (!dstr) return
      if (params.timeBegin && dstr < params.timeBegin) return
      if (params.timeEnd && dstr > params.timeEnd) return
      const amt = Number(r.amount || r.money || 0) || 0
      dailyMap[dstr] = dailyMap[dstr] || { total: 0, count: 0, windows: {} }
      dailyMap[dstr].total += amt
      dailyMap[dstr].count += 1
      const win = r.window || r.windowId || r.window_id || r.windowNo || '未知'
      dailyMap[dstr].windows[win] = (dailyMap[dstr].windows[win] || 0) + 1
    })

    const dates = Object.keys(dailyMap).sort()
    const series = dates.map(d => Number(dailyMap[d].total.toFixed(2)))

    // 基本统计
    total.value = series.reduce((a,b)=>a+b, 0)
    avgDaily.value = dates.length ? (total.value / dates.length) : 0

    // 线性拟合斜率（每天消费总额）
    if (series.length >= 2) {
      const n = series.length
      const xMean = (n - 1) / 2
      const yMean = series.reduce((a,b) => a + b, 0) / n
      let num = 0, den = 0
      for (let i = 0; i < n; i++) {
        num += (i - xMean) * (series[i] - yMean)
        den += (i - xMean) * (i - xMean)
      }
      slope.value = den === 0 ? 0 : (num / den)
    } else {
      slope.value = 0
    }

    // 计算最常去的窗口（整个周期）
    const windowCounts = {}
    Object.values(dailyMap).forEach(d => {
      Object.entries(d.windows).forEach(([w,c]) => { windowCounts[w] = (windowCounts[w] || 0) + c })
    })
    let bestWin = ''
    let bestCnt = 0
    Object.entries(windowCounts).forEach(([w,c]) => { if (c > bestCnt) { bestCnt = c; bestWin = w } })

    // 渲染
    await nextTick()
    render(dates, series)
    // 将额外分析显示在卡片下方（DOM 内已有文本绑定）
    total.value = Number(total.value.toFixed(2))
    avgDaily.value = Number(avgDaily.value.toFixed(2))
    trendMeta.value = { busiestWindow: bestWin || '-', visits: bestCnt }
  } catch (e) {
    console.error('load recent error', e)
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
</style>
