<template>
  <div class="user-portrait-page">
    <el-card>
      <template #header>
        <span>个人用户画像</span>
      </template>

      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="never">
            <div class="item-title">消费层级</div>
            <div class="item-value">{{ portraitTag.level }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="item-title">消费活跃度</div>
            <div class="item-value">{{ portraitTag.activity }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="item-title">作息消费特征</div>
            <div class="item-value">{{ portraitTag.schedule }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never">
            <div class="item-title">学习状态</div>
            <div class="item-value">{{ portraitTag.studyState }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="section-card" shadow="never">
        <template #header>
          <span>基础信息</span>
        </template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="姓名">{{ basicInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ basicInfo.studentId }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ basicInfo.gender }}</el-descriptions-item>
          <el-descriptions-item label="学院">{{ basicInfo.college }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ basicInfo.major }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ basicInfo.grade }}</el-descriptions-item>
          <el-descriptions-item label="班级" :span="3">{{ basicInfo.className }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="section-card" shadow="never">
        <template #header>
          <span>消费统计画像</span>
        </template>
        <el-row :gutter="12">
          <el-col :span="6"><div class="metric-item"><span>日均消费金额</span><strong>¥{{ fmtNum(metrics.dailyAvg) }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>日均消费次数</span><strong>{{ fmtNum(metrics.dailyCount) }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>月均消费金额</span><strong>¥{{ fmtNum(metrics.monthAvgAmount) }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>月均消费次数</span><strong>{{ fmtNum(metrics.monthAvgCount) }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>年累计消费额</span><strong>¥{{ fmtNum(metrics.yearTotalAmount) }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>最常去窗口</span><strong>{{ metrics.favoriteWindow }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>消费高峰餐别</span><strong>{{ metrics.peakPeriod }}</strong></div></el-col>
          <el-col :span="6"><div class="metric-item"><span>绩点</span><strong>{{ fmtNum(metrics.gpa) }}</strong></div></el-col>
        </el-row>
      </el-card>

      <el-row :gutter="20" style="margin-top: 16px;">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>个人餐别占比</span>
            </template>
            <div id="mealPieChart" class="portrait-chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>个人消费时段分布</span>
            </template>
            <div id="hourBarChart" class="portrait-chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 16px;">
        <template #header>
          <span>大模型个性化解释</span>
        </template>
        <div class="explain-text">{{ explainText }}</div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getClusterDetails, getConsumptionData, getDeepSeekExplanation, getPovertyIdentification, getStudentInfo } from '@/api/user'
import { getStoredUserInfo } from '@/utils/auth'

const userInfo = getStoredUserInfo() || {}
const uid = userInfo.username || userInfo.userId || ''

const basicInfo = ref({
  name: '-',
  studentId: uid || '-',
  gender: '-',
  college: '-',
  major: '-',
  grade: '-',
  className: '-'
})

const metrics = ref({
  dailyAvg: 0,
  dailyCount: 0,
  monthAvgAmount: 0,
  monthAvgCount: 0,
  yearTotalAmount: 0,
  favoriteWindow: '-',
  peakPeriod: '-',
  gpa: 0
})

const portraitTag = ref({
  level: '-',
  activity: '-',
  schedule: '-',
  studyState: '-'
})

const explainText = ref('正在生成个人画像解释...')

const charts = {
  meal: null,
  hour: null
}

const safeNum = (v) => {
  const n = Number(v)
  return Number.isNaN(n) ? 0 : n
}

const fmtNum = (v) => safeNum(v).toFixed(2)

const deriveDailyMetrics = (clusterRow) => {
  const monthAvgAmount = safeNum(clusterRow?.monthAvgAmount)
  const monthAvgCount = safeNum(clusterRow?.monthAvgCount)
  const fallbackDailyAvg = safeNum(clusterRow?.dailyAvg ?? clusterRow?.daily_avg ?? clusterRow?.monthlyAvg ?? 0)
  const fallbackDailyCount = safeNum(clusterRow?.dailyCount ?? clusterRow?.daily_count ?? 0)

  // 优先使用月均口径反推日均，避免全历史聚类字段被误解为“日均”。
  const dailyAvg = monthAvgAmount > 0 ? monthAvgAmount / 30 : fallbackDailyAvg
  const dailyCount = monthAvgCount > 0 ? monthAvgCount / 30 : fallbackDailyCount

  return {
    dailyAvg,
    dailyCount,
    monthAvgAmount,
    monthAvgCount
  }
}

const quantile = (arr, q) => {
  if (!arr.length) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const idx = Math.floor((sorted.length - 1) * q)
  return sorted[idx]
}

const mapLevel = (value, q1, q2, q3) => {
  if (value <= q1) return '低消费'
  if (value <= q2) return '较低消费'
  if (value <= q3) return '中消费'
  return '高消费'
}

const normalizePortraitRows = (res) => {
  const raw = res?.results || res?.data?.results || res?.data || res || []
  const arr = Array.isArray(raw) ? raw : []
  return arr.map((i) => ({
    studentId: String(i.studentId || i.student_id || '').trim(),
    name: i.name || '-',
    gender: i.gender || '-',
    college: i.college || '-',
    major: i.major || '-',
    className: i.className || i.class_name || '-',
    grade: i.grade || '-',
    dailyAvg: Number(i.dailyAvg ?? i.daily_avg ?? i.monthlyAvg ?? i.monthly_avg ?? 0),
    dailyCount: Number(i.dailyCount ?? i.daily_count ?? i.monthAvgCount ?? i.month_avg_count ?? 0),
    monthAvgAmount: Number(i.monthAvgAmount ?? i.month_avg_amount ?? 0),
    monthAvgCount: Number(i.monthAvgCount ?? i.month_avg_count ?? 0),
    favoriteWindow: i.favoriteWindow || i.favorite_window || '-',
    peakPeriod: i.peakPeriod || i.peak_period || '-',
    gpa: Number(i.gpa ?? i.GPA ?? i.score ?? 0),
    clusterType: i.clusterType || i.consumptionType || i.consumptionGroup || ''
  }))
}

const getRows = (res) => {
  const rows = res?.records || res?.data?.records || res?.data || []
  return Array.isArray(rows) ? rows : []
}

const getTotal = (res, fallback = 0) => {
  const total = Number(res?.total || res?.totalCount || res?.data?.total || fallback || 0)
  return Number.isNaN(total) ? fallback : total
}

const fetchAllConsumptionRecords = async (studentId) => {
  const pageSize = 2000
  const maxPages = 80
  let page = 1
  let allRows = []
  let total = 0

  while (page <= maxPages) {
    const res = await getConsumptionData({ studentId, page, pageSize })
    const rows = getRows(res)
    const list = Array.isArray(rows) ? rows : []

    if (!list.length) break

    allRows = allRows.concat(list)
    total = getTotal(res, allRows.length)

    if (allRows.length >= total) break
    if (list.length < pageSize) break

    page += 1
  }

  return allRows
}

const getStudentRow = (res) => {
  const root = res?.data || res || {}
  if (Array.isArray(root.items) && root.items.length) return root.items[0]
  if (Array.isArray(root.records) && root.records.length) return root.records[0]
  if (Array.isArray(root) && root.length) return root[0]
  return null
}

const initOrGet = (id, key) => {
  const el = document.getElementById(id)
  if (!el) return null
  const old = echarts.getInstanceByDom(el)
  charts[key] = old || echarts.init(el)
  charts[key].clear()
  return charts[key]
}

const getTargetYear = (records) => {
  const years = []
  records.forEach((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    const dt = new Date(String(timeRaw).replace(' ', 'T'))
    if (!Number.isNaN(dt.getTime())) {
      years.push({ year: dt.getFullYear(), ts: dt.getTime() })
    }
  })

  if (!years.length) return null
  return years.reduce((a, b) => (a.ts > b.ts ? a : b)).year
}

const renderCharts = (records) => {
  const mealMap = {}
  const hourMap = new Array(24).fill(0)
  const targetYear = getTargetYear(records)

  records.forEach((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    const date = new Date(String(timeRaw).replace(' ', 'T'))
    if (Number.isNaN(date.getTime())) return

    const amount = safeNum(r.amount || r.money || 0)

    // 餐别占比与“年累计消费额”保持同口径：仅统计目标年份数据。
    if (targetYear !== null && date.getFullYear() === targetYear) {
      const meal = r.mealType || r.meal_type || '未知'
      mealMap[meal] = (mealMap[meal] || 0) + amount
    }

    hourMap[date.getHours()] += amount
  })

  const mealChart = initOrGet('mealPieChart', 'meal')
  if (mealChart) {
    mealChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
      series: [{ type: 'pie', radius: ['38%', '70%'], data: Object.keys(mealMap).map(k => ({ name: k, value: Number(mealMap[k].toFixed(2)) })) }]
    })
  }

  const hourChart = initOrGet('hourBarChart', 'hour')
  if (hourChart) {
    hourChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, i) => `${i}时`) },
      yAxis: { type: 'value', name: '金额(元)' },
      series: [{ type: 'bar', data: hourMap.map(v => Number(v.toFixed(2))), barMaxWidth: 18, itemStyle: { color: '#409EFF' } }]
    })
  }
}

const calcYearTotalAmount = (records) => {
  const validRows = []

  records.forEach((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    const dt = new Date(String(timeRaw).replace(' ', 'T'))
    if (Number.isNaN(dt.getTime())) return

    validRows.push({
      year: dt.getFullYear(),
      amount: safeNum(r.amount || r.money || 0),
      ts: dt.getTime()
    })
  })

  if (!validRows.length) return 0

  // 数据可能是历史学年，使用最新消费记录所在年份作为“年累计”口径更贴近用户认知。
  const latest = validRows.reduce((a, b) => (a.ts > b.ts ? a : b))
  const targetYear = latest.year

  return validRows
    .filter(i => i.year === targetYear)
    .reduce((sum, i) => sum + i.amount, 0)
}

const buildPortrait = (clusterRow, studentRow, records, relativeLevel) => {
  const derived = deriveDailyMetrics(clusterRow)
  const dailyAvg = Number(derived.dailyAvg.toFixed(2))
  const dailyCount = Number(derived.dailyCount.toFixed(2))
  const gpa = safeNum(clusterRow?.gpa ?? clusterRow?.GPA ?? 0)
  const yearTotalAmount = calcYearTotalAmount(records)

  const hourly = new Array(24).fill(0)
  records.forEach((r) => {
    const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
    const date = new Date(String(timeRaw).replace(' ', 'T'))
    if (Number.isNaN(date.getTime())) return
    hourly[date.getHours()] += 1
  })
  const peakHour = hourly.indexOf(Math.max(...hourly))
  const schedule = peakHour < 9 ? '早高峰型' : peakHour < 18 ? '日间稳定型' : '晚间活跃型'

  basicInfo.value = {
    name: clusterRow?.name || studentRow?.name || studentRow?.studentName || '-',
    studentId: clusterRow?.studentId || studentRow?.studentId || uid || '-',
    gender: clusterRow?.gender || studentRow?.gender || '-',
    college: clusterRow?.college || studentRow?.college || '-',
    major: clusterRow?.major || studentRow?.major || '-',
    grade: clusterRow?.grade || studentRow?.grade || '-',
    className: clusterRow?.className || studentRow?.className || '-'
  }

  metrics.value = {
    dailyAvg,
    dailyCount,
    monthAvgAmount: derived.monthAvgAmount,
    monthAvgCount: derived.monthAvgCount,
    yearTotalAmount,
    favoriteWindow: clusterRow?.favoriteWindow || '-',
    peakPeriod: clusterRow?.peakPeriod || '-',
    gpa
  }

  portraitTag.value = {
    level: relativeLevel || clusterRow?.clusterType || clusterRow?.consumptionType || '未知',
    activity: dailyCount >= 3 ? '高频消费' : dailyCount >= 1.5 ? '中频消费' : '低频消费',
    schedule,
    studyState: gpa >= 3.5 ? '学习状态优秀' : gpa >= 3.0 ? '学习状态良好' : gpa > 0 ? '学习状态待提升' : '暂无成绩数据'
  }

  return {
    level: portraitTag.value.level,
    activity: portraitTag.value.activity,
    schedule: portraitTag.value.schedule,
    studyState: portraitTag.value.studyState,
    ...metrics.value,
    ...basicInfo.value,
    peakHour
  }
}

const buildFallbackExplain = (meta) => {
  return `从近期画像看，你当前属于“${meta.level}”，整体消费活跃度为${meta.activity}，常见消费高峰在${meta.peakHour}时附近，主要集中在${meta.favoriteWindow || '常用窗口'}。从金额口径看，日均约¥${fmtNum(meta.dailyAvg)}、月均约¥${fmtNum(meta.monthAvgAmount)}。这反映出你以规律就餐为主、消费节奏相对稳定。建议优先保持固定餐次，并在高峰时段关注单次消费波动，避免短时冲动消费。`
}

const buildDeepSeekExplain = async (clusterRow, meta) => {
  if (clusterRow?.llmExplanation) {
    explainText.value = String(clusterRow.llmExplanation)
    return
  }

  const llmMetrics = {
    ...metrics.value,
    dailyAvg: Number(safeNum(metrics.value.dailyAvg).toFixed(2)),
    dailyCount: Number(safeNum(metrics.value.dailyCount).toFixed(2)),
    monthAvgAmount: Number(safeNum(metrics.value.monthAvgAmount).toFixed(2)),
    monthAvgCount: Number(safeNum(metrics.value.monthAvgCount).toFixed(2)),
    yearTotalAmount: Number(safeNum(metrics.value.yearTotalAmount).toFixed(2))
  }

  const payload = {
    scene: 'personal-portrait',
    style: 'plain-chinese',
    data: {
      basicInfo: basicInfo.value,
      portrait: portraitTag.value,
      metrics: llmMetrics
    },
    prompt: '请基于用户基础信息与消费行为指标，输出180-260字的个性化解释。结构要求：1) 用1句话总结整体画像；2) 说明消费金额、消费频次、高峰餐别/时段及窗口偏好；3) 给出2-3条可执行建议（预算、作息、就餐结构）；4) 明确该结论仅反映消费行为特征，不代表行政认定。语气中性、具体，避免空泛套话。'
  }

  try {
    const res = await getDeepSeekExplanation(payload)
    const text = res?.text || res?.answer || res?.data?.text || res?.data?.answer
    explainText.value = text ? String(text) : buildFallbackExplain(meta)
  } catch {
    explainText.value = buildFallbackExplain(meta)
  }
}

const loadPortrait = async () => {
  if (!uid) {
    explainText.value = '未获取到当前用户学号，无法生成画像。'
    return
  }
  try {
    const [studentRes, records] = await Promise.all([
      getStudentInfo({ studentId: uid, page: 1, pageSize: 1 }).catch(() => null),
      fetchAllConsumptionRecords(uid).catch(() => [])
    ])

    const studentRow = getStudentRow(studentRes)
    // 与管理员“用户画像模块”默认口径保持一致：使用全样本基线做分位分层。
    const cohortParams = {
      clusterMethod: 'kmeans',
      includeDetails: false
    }

    const [personalRes, cohortRes, detailRes] = await Promise.all([
      getPovertyIdentification({ ...cohortParams, studentId: uid }).catch(() => null),
      getPovertyIdentification(cohortParams).catch(() => null),
      getClusterDetails({ studentIds: uid, includeLlm: false }).catch(() => null)
    ])

    const personalRows = normalizePortraitRows(personalRes)
    const cohortRows = normalizePortraitRows(cohortRes)
    const detailRows = detailRes?.results || detailRes?.data?.results || []
    const detail = Array.isArray(detailRows) && detailRows.length ? detailRows[0] : null

    let row = personalRows.find(i => String(i.studentId) === String(uid))
    if (!row && cohortRows.length) {
      row = cohortRows.find(i => String(i.studentId) === String(uid)) || null
    }
    if (!row) {
      row = {
        studentId: uid,
        name: studentRow?.name || '-',
        dailyAvg: 0,
        dailyCount: 0,
        monthAvgAmount: 0,
        monthAvgCount: 0,
        gpa: 0,
        peakPeriod: '-',
        favoriteWindow: '-'
      }
    }

    const mergedRow = {
      ...row,
      monthAvgAmount: Number(detail?.monthAvgAmount ?? row.monthAvgAmount ?? 0),
      monthAvgCount: Number(detail?.monthAvgCount ?? row.monthAvgCount ?? 0),
      favoriteWindow: detail?.favoriteWindow || row.favoriteWindow || '-',
      peakPeriod: detail?.peakPeriod || row.peakPeriod || '-',
      gpa: Number(detail?.gpa ?? row.gpa ?? 0)
    }

    const reference = cohortRows.length ? cohortRows : personalRows
    const refVals = reference.map(i => Number(i.dailyAvg || 0)).filter(v => v > 0)
    const q1 = quantile(refVals, 0.25)
    const q2 = quantile(refVals, 0.5)
    const q3 = quantile(refVals, 0.75)
    const relativeLevel = refVals.length
      ? mapLevel(Number(mergedRow.dailyAvg || 0), q1, q2, q3)
      : (mergedRow.clusterType || '未知')
    const finalLevel = mergedRow.clusterType || relativeLevel

    const meta = buildPortrait(mergedRow, studentRow, records, finalLevel)
    await nextTick()
    renderCharts(records)
    await buildDeepSeekExplain(mergedRow, meta)
  } catch (error) {
    console.error('加载个人画像失败:', error)
    ElMessage.error('加载个人画像失败，请稍后重试')
    explainText.value = '暂时无法生成画像解释，请稍后再试。'
  }
}

const resizeHandler = () => {
  Object.values(charts).forEach(c => c && c.resize && c.resize())
}

onMounted(() => {
  loadPortrait()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  Object.values(charts).forEach(c => c && c.dispose && c.dispose())
})
</script>

<style scoped>
.user-portrait-page {
  padding: 16px;
}

.item-title {
  color: #909399;
  font-size: 13px;
}

.item-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.section-card {
  margin-top: 16px;
}

.metric-item {
  background: #f8fafc;
  border: 1px solid #edf2f7;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #606266;
}

.metric-item strong {
  color: #1f2937;
  font-size: 15px;
}

.portrait-chart {
  width: 100%;
  height: 320px;
}

.explain-text {
  line-height: 1.8;
  color: #303133;
}
</style>
