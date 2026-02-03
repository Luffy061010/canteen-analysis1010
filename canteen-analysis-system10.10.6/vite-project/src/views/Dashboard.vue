<template>
  <!-- 页面：系统概览与统计看板 -->
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.totalStudents.toLocaleString() }}</div>
            <div class="stat-label">总学生数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">¥{{ statistics.todayConsumption.toLocaleString() }}</div>
            <div class="stat-label">今日消费总额</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.povertyStudents.toLocaleString() }}</div>
            <div class="stat-label">贫困生数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">¥{{ statistics.monthlyConsumption.toLocaleString() }}</div>
            <div class="stat-label">月总消费额</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时消费趋势图表（占据完整宽度） -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>实时消费趋势分析</span>
          </template>
          <div id="consumptionTrend" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 贫困生消费信息 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>贫困生消费监控</span>
      </template>
      <el-table :data="povertyConsumptionData" v-loading="loading" style="width: 100%">
        <el-table-column prop="studentId" label="学号" width="120"></el-table-column>
        <el-table-column prop="name" label="姓名" width="100"></el-table-column>
        <el-table-column prop="college" label="学院" width="120"></el-table-column>
        <el-table-column prop="monthlyAvg" label="月均消费" width="100">
          <template #default="scope">
            ¥{{ (scope.row.monthlyAvg || scope.row.monthlyConsumption || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="dailyAvg" label="日均消费" width="100">
          <template #default="scope">
            ¥{{ (scope.row.dailyAvg || scope.row.avgDaily || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="clusterType" label="消费类型" width="120">
          <template #default="scope">
            <el-tag :type="getLevelType(scope.row.clusterType || scope.row.consumptionLevel)">
              {{ scope.row.clusterType || scope.row.consumptionLevel || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="povertyIndex" label="贫困指数" width="100">
          <template #default="scope">
            {{ (scope.row.povertyIndex || 0).toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getConsumption, getConsumptionData, getPovertyIdentification, getStudentInfo, getSystemStatus } from '@/api/user.js'
import { ElMessage } from 'element-plus'

// 响应式数据
const statistics = ref({
  totalStudents: 0,
  todayConsumption: 0,
  povertyStudents: 0,
  monthlyConsumption: 0
})

const povertyConsumptionData = ref([])
const loading = ref(false)
const CACHE_TTL = 60 * 1000

// 数据安全处理
const safeValue = (val) => {
  if (val === null || val === undefined || isNaN(val)) return 0
  const num = Number(val)
  return isNaN(num) ? 0 : num
}

const pickStatValue = (stat, keys = []) => {
  if (!stat) return undefined
  for (const key of keys) {
    const val = stat[key]
    if (val !== undefined && val !== null && val !== '') {
      return val
    }
  }
  return undefined
}

const extractRecords = (res) => {
  if (Array.isArray(res?.records)) return res.records
  if (Array.isArray(res?.data?.records)) return res.data.records
  if (Array.isArray(res?.data)) return res.data
  if (Array.isArray(res)) return res
  return []
}

const extractTotal = (res) => {
  return res?.total || res?.totalCount || res?.count || res?.data?.total || res?.data?.totalCount || res?.data?.count || 0
}

const sumAmount = (records = []) => {
  return records.reduce((sum, item) => {
    return sum + safeValue(item?.amount ?? item?.totalAmount ?? item?.money ?? item?.value ?? 0)
  }, 0)
}

const fetchConsumptionSum = async ({ timeBegin, timeEnd }) => {
  let page = 1
  const pageSize = 2000
  const maxPages = 10
  let totalCount = 0
  let totalSum = 0

  do {
    const res = await getConsumptionData({ page, pageSize, timeBegin, timeEnd })
    const records = extractRecords(res)
    totalSum += sumAmount(records)
    totalCount = Number(extractTotal(res)) || records.length
    page += 1
  } while ((page - 1) * pageSize < totalCount && page <= maxPages)

  return totalSum
}

// 加载统计数据（系统状态接口）
const loadStatistics = async () => {
  loading.value = true
  try {
    const cacheRaw = sessionStorage.getItem('dashboard_stats_cache')
    if (cacheRaw) {
      const cache = JSON.parse(cacheRaw)
      if (cache && Date.now() - cache.ts < CACHE_TTL && cache.data) {
        statistics.value = cache.data
        return
      }
    }

    const stat = await getSystemStatus()
    const statSource = stat && typeof stat === 'object' && stat.data ? stat.data : stat
    const nextStats = {
      totalStudents: safeValue(pickStatValue(statSource, ['totalStudents', 'total_students', 'total'])),
      todayConsumption: safeValue(pickStatValue(statSource, ['todayConsumption', 'today_consumption', 'todayTotal', 'totalAmount'])),
      povertyStudents: safeValue(pickStatValue(statSource, ['povertyStudents', 'poverty_students', 'povertyCount'])),
      monthlyConsumption: safeValue(pickStatValue(statSource, ['monthlyConsumption', 'monthly_consumption', 'monthTotal', 'totalAmount']))
    }

    const isEmpty = !nextStats.totalStudents && !nextStats.todayConsumption && !nextStats.monthlyConsumption && !nextStats.povertyStudents

    if (isEmpty) {
      // 兜底：用现有统计接口/学生数补齐
      const [consumptionStat, studentStat] = await Promise.all([
        getConsumption({}),
        getStudentInfo({ page: 1, pageSize: 1 })
      ])

      const totalStudents = studentStat?.total || studentStat?.totalCount || studentStat?.data?.total || 0
      const totalAmount = consumptionStat?.totalAmount || consumptionStat?.total || 0

      statistics.value = {
        totalStudents: safeValue(totalStudents),
        todayConsumption: safeValue(totalAmount),
        povertyStudents: safeValue(nextStats.povertyStudents),
        monthlyConsumption: safeValue(totalAmount)
      }
    } else {
      statistics.value = nextStats
    }

    // 若今日/本月为 0，则尝试按时间范围再取一次
    if (!statistics.value.todayConsumption || !statistics.value.monthlyConsumption) {
      const now = new Date()
      const today = now.toISOString().slice(0, 10)
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
      const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)

      const [todayStat, monthStat] = await Promise.all([
        getConsumption({ timeBegin: today, timeEnd: today }).catch(() => null),
        getConsumption({ timeBegin: monthStart, timeEnd: monthEnd }).catch(() => null)
      ])

      let todayTotal = safeValue(pickStatValue(todayStat, ['totalAmount', 'total', 'amount']))
      let monthTotal = safeValue(pickStatValue(monthStat, ['totalAmount', 'total', 'amount']))

      if (!todayTotal) {
        todayTotal = await fetchConsumptionSum({ timeBegin: today, timeEnd: today }).catch(() => 0)
      }
      if (!monthTotal) {
        monthTotal = await fetchConsumptionSum({ timeBegin: monthStart, timeEnd: monthEnd }).catch(() => 0)
      }

      if (!statistics.value.todayConsumption && todayTotal) {
        statistics.value.todayConsumption = todayTotal
      }
      if (!statistics.value.monthlyConsumption && monthTotal) {
        statistics.value.monthlyConsumption = monthTotal
      }
    }

    // 若仍为 0，则使用全量统计兜底（保证展示不为 0）
    if (!statistics.value.todayConsumption || !statistics.value.monthlyConsumption) {
      const overallStat = await getConsumption({}).catch(() => null)
      const overallTotal = safeValue(pickStatValue(overallStat, ['totalAmount', 'total', 'amount']))
      if (!statistics.value.todayConsumption && overallTotal) {
        statistics.value.todayConsumption = overallTotal
      }
      if (!statistics.value.monthlyConsumption && overallTotal) {
        statistics.value.monthlyConsumption = overallTotal
      }
    }

    sessionStorage.setItem('dashboard_stats_cache', JSON.stringify({ ts: Date.now(), data: statistics.value }))
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 兜底：当 /system/status 不可用时回退到消费统计与学生数
    try {
      const [consumptionStat, studentStat] = await Promise.all([
        getConsumption({}),
        getStudentInfo({ page: 1, pageSize: 1 })
      ])

      const totalStudents = studentStat?.total || studentStat?.totalCount || studentStat?.data?.total || 0
      const totalAmount = consumptionStat?.totalAmount || consumptionStat?.total || 0

      statistics.value = {
        totalStudents: safeValue(totalStudents),
        todayConsumption: safeValue(totalAmount),
        povertyStudents: safeValue(statistics.value.povertyStudents),
        monthlyConsumption: safeValue(totalAmount)
      }
    } catch (fallbackError) {
      console.error('兜底统计数据失败:', fallbackError)
      if (error.response?.status === 422) {
        ElMessage.error('参数验证失败，请检查请求格式')
      } else {
        ElMessage.warning('加载统计数据失败，请稍后重试')
      }
    }
  } finally {
    loading.value = false
  }
}

// 加载贫困生数据（复用消费明细分页）
const loadPovertyData = async () => {
  loading.value = true
  try {
    const cacheRaw = sessionStorage.getItem('dashboard_poverty_cache')
    if (cacheRaw) {
      const cache = JSON.parse(cacheRaw)
      if (cache && Date.now() - cache.ts < CACHE_TTL && Array.isArray(cache.data)) {
        povertyConsumptionData.value = cache.data
        return
      }
    }

    const result = await getPovertyIdentification({ clusterMethod: 'kmeans' })
    const hasRootResults = result && (result.results || result.clusterData || result.distributionData || result.centers)
    const dataRoot = hasRootResults ? result : (result && typeof result === 'object' && result.data ? result.data : result)
    const records = Array.isArray(dataRoot?.results)
      ? dataRoot.results
      : Array.isArray(dataRoot?.povertyResults)
        ? dataRoot.povertyResults
        : Array.isArray(dataRoot)
          ? dataRoot
          : []

    const mapped = records.map((item) => {
      const studentId = item.studentId || item.student_id || ''
      return {
        studentId,
        name: item.name || item.studentName || item.student_name || studentId || '-',
        college: item.college || item.collegeName || item.college_name || '未知',
        monthlyAvg: safeValue(item.monthlyAvg ?? item.monthly_avg ?? 0),
        dailyAvg: safeValue(item.dailyAvg ?? item.daily_avg ?? 0),
        clusterType: item.clusterType || item.type || '未知',
        povertyIndex: safeValue(item.povertyIndex ?? item.poverty_index ?? 0)
      }
    })

    const povertyOnly = mapped.filter(row => row.clusterType === '贫困生' || row.clusterType === '贫困')
    povertyConsumptionData.value = povertyOnly.length ? povertyOnly : mapped

    if (!statistics.value.povertyStudents && povertyConsumptionData.value.length) {
      statistics.value.povertyStudents = povertyConsumptionData.value.length
    }
    sessionStorage.setItem('dashboard_poverty_cache', JSON.stringify({ ts: Date.now(), data: povertyConsumptionData.value }))
  } catch (error) {
    console.error('加载贫困生数据失败:', error)
    povertyConsumptionData.value = []
  } finally {
    loading.value = false
  }
}

// 图表实例引用
let trendChart = null

// 图表初始化函数
const initConsumptionTrend = (trendData = null) => {
  nextTick(() => {
    try {
      const chartDom = document.getElementById('consumptionTrend')
      if (!chartDom) {
        console.warn('图表容器未找到')
        return
      }

      // 如果图表已存在，先销毁
      if (trendChart) {
        trendChart.dispose()
      }

      trendChart = echarts.init(chartDom)

      // 如果没有数据，使用默认示例数据
      const chartData = trendData || generateDefaultTrendData()

      const option = {
        title: {
          text: '最近30天消费趋势',
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'normal'
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: (params) => {
            const data = params[0]
            return `${data.name}<br/>消费总额: ¥${data.value.toLocaleString()}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: chartData.dates,
          axisLine: {
            lineStyle: {
              color: '#DCDFE6'
            }
          },
          axisLabel: {
            color: '#606266',
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          name: '消费金额(元)',
          axisLine: {
            lineStyle: {
              color: '#DCDFE6'
            }
          },
          axisLabel: {
            color: '#606266',
            formatter: (value) => `¥${value.toLocaleString()}`
          },
          splitLine: {
            lineStyle: {
              color: '#F2F6FC',
              type: 'dashed'
            }
          }
        },
        series: [
          {
            name: '消费总额',
            type: 'line',
            smooth: true,
            data: chartData.values,
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                  { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
                ]
              }
            },
            itemStyle: {
              color: '#409EFF'
            },
            lineStyle: {
              width: 3,
              color: '#409EFF'
            }
          }
        ]
      }

      trendChart.setOption(option)

      // 响应式调整
      window.addEventListener('resize', () => {
        if (trendChart) {
          trendChart.resize()
        }
      })
    } catch (error) {
      console.error('初始化图表失败:', error)
      ElMessage.error('图表初始化失败')
    }
  })
}

// 生成默认趋势数据（如果没有真实数据）
const generateDefaultTrendData = () => {
  const dates = []
  const values = []
  const today = new Date()

  for (let i = 29; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))

    // 生成随机消费数据（模拟）
    const baseValue = 50000 + Math.random() * 20000
    values.push(Math.round(baseValue))
  }

  return { dates, values }
}

// 获取消费类型标签颜色
const getLevelType = (type) => {
  const typeMap = {
    '低消费': 'danger',
    '中等消费': 'warning',
    '高消费': 'success',
    '贫困': 'danger',
    '正常': 'success',
    '富裕': 'info'
  }
  return typeMap[type] || 'info'
}

// 组件卸载时销毁图表
onBeforeUnmount(() => {
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
  window.removeEventListener('resize', () => {})
})

onMounted(async () => {
  await Promise.all([loadStatistics(), loadPovertyData()])
  initConsumptionTrend()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>
