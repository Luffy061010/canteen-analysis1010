<template>
  <div class="consumption-data-query">
    <el-alert v-if="loadError" type="error" :closable="false" show-icon style="margin-bottom: 16px;">
      <template #title>消费统计加载失败</template>
      <div class="error-actions">
        <span>{{ loadError }}</span>
        <el-button size="small" type="danger" plain :loading="loading" @click="loadData">重试</el-button>
      </div>
    </el-alert>

    <el-card>
      <template #header>
        <span>消费数据统计</span>
      </template>

      <el-form :model="queryForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="学院">
              <el-select v-model="queryForm.college" placeholder="全部学院" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="college in colleges" :key="college" :label="college" :value="college" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="专业">
              <el-select v-model="queryForm.major" placeholder="全部专业" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="major in majors" :key="major" :label="major" :value="major" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="年级">
              <el-select v-model="queryForm.grade" placeholder="全部年级" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="grade in grades" :key="grade" :label="grade" :value="grade" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="班级">
              <el-select v-model="queryForm.class" placeholder="全部班级" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="cls in classes" :key="cls" :label="cls" :value="cls" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :md="10" :lg="8">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="queryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8" :lg="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6" :lg="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleQuery">查询</el-button>
              <el-button :disabled="loading" @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card>
            <div class="stat-block">
              <div class="stat-num">{{ stat.totalStudents }}</div>
              <div class="stat-text">查询学生数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card>
            <div class="stat-block">
              <div class="stat-num">¥{{ stat.totalAmount }}</div>
              <div class="stat-text">总消费金额</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card>
            <div class="stat-block">
              <div class="stat-num">{{ stat.totalRecords }}</div>
              <div class="stat-text">消费记录数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card>
            <div class="stat-block">
              <div class="stat-num">¥{{ stat.averageConsumption }}</div>
              <div class="stat-text">人均消费额</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <span>消费窗口排行</span>
            </template>
            <div id="topWindowChart" class="chart" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <span>窗口消费分布</span>
            </template>
            <div id="windowDistributionChart" class="chart" />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <span>日消费趋势</span>
            </template>
            <div id="consumptionTrendChart" class="chart" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <el-card>
            <template #header>
              <span>餐别消费占比</span>
            </template>
            <div id="mealTypeChart" class="chart" />
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getConsumptionTop, getConsumptionGroup, getConsumption, getConsumptionData } from '@/api/user.js'
import { COLLEGES_MAJORS, generateClassNames } from '@/utils/const_value.js'
import { ElMessage } from 'element-plus'

export default {
  name: 'ConsumptionDataQuery',
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: [],
        studentId: ''
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      stat: {
        totalStudents: 0,
        totalAmount: 0,
        totalRecords: 0,
        averageConsumption: 0
      },
      topData: [],
      groupData: [],
      trendData: [],
      mealTypeData: [],
      charts: {},
      resizeHandler: null,
      loading: false,
      loadError: ''
    }
  },
  mounted() {
    this.loadData()
  },
  beforeUnmount() {
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler)
    }
    Object.values(this.charts).forEach((chart) => {
      if (chart && typeof chart.dispose === 'function') chart.dispose()
    })
  },
  watch: {
    'queryForm.college'(newVal) {
      if (newVal && COLLEGES_MAJORS[newVal]) {
        this.majors = COLLEGES_MAJORS[newVal].majors || []
      } else {
        this.majors = []
      }
      this.queryForm.major = ''
      this.queryForm.class = ''
      this.classes = []
    },
    'queryForm.major'(newVal) {
      if (newVal && this.queryForm.grade) {
        this.classes = generateClassNames(newVal, this.queryForm.grade + '级')
      } else {
        this.classes = []
      }
      this.queryForm.class = ''
    },
    'queryForm.grade'(newVal) {
      if (newVal && this.queryForm.major) {
        this.classes = generateClassNames(this.queryForm.major, newVal + '级')
      } else {
        this.classes = []
      }
      this.queryForm.class = ''
    }
  },
  methods: {
    withTimeout(promise, timeoutMs = 60000, message = '请求超时，请稍后重试') {
      let timer = null
      return Promise.race([
        promise,
        new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error(message)), timeoutMs)
        })
      ]).finally(() => {
        if (timer) clearTimeout(timer)
      })
    },

    buildParams(pageSize = 1000) {
      const [timeBegin, timeEnd] = Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2
        ? this.queryForm.dateRange
        : []

      const params = {
        college: this.queryForm.college || undefined,
        major: this.queryForm.major || undefined,
        grade: this.queryForm.grade || undefined,
        className: this.queryForm.class || undefined,
        studentId: this.queryForm.studentId || undefined,
        timeBegin: timeBegin || undefined,
        timeEnd: timeEnd || undefined,
        startDate: timeBegin || undefined,
        endDate: timeEnd || undefined,
        page: 1,
        pageSize
      }

      Object.keys(params).forEach((k) => {
        if (params[k] === '' || params[k] === undefined || params[k] === null) {
          delete params[k]
        }
      })
      return params
    },

    formatNum(v) {
      return Number(Number(v || 0).toFixed(2))
    },

    buildAggregations(rows) {
      const trendMap = new Map()
      const mealMap = new Map()
      const windowMap = new Map()

      rows.forEach((row) => {
        const timeRaw = row.consumptionTime || row.consumption_time || row.consume_time || ''
        const dateKey = String(timeRaw).split('T')[0].split(' ')[0]
        const amount = Number(row.amount || row.money || 0)
        const mealType = row.mealType || row.meal_type || '未知'
        const windowName = row.window || row.windowId || row.window_id || '未知窗口'

        if (dateKey) {
          trendMap.set(dateKey, (trendMap.get(dateKey) || 0) + amount)
        }
        mealMap.set(mealType, (mealMap.get(mealType) || 0) + amount)
        windowMap.set(windowName, (windowMap.get(windowName) || 0) + amount)
      })

      this.trendData = Array.from(trendMap.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([date, value]) => ({ date, value: this.formatNum(value) }))

      this.mealTypeData = Array.from(mealMap.entries()).map(([name, value]) => ({
        name,
        value: this.formatNum(value)
      }))

      const mergedWindow = Array.from(windowMap.entries())
        .map(([name, amount]) => ({ name, amount: this.formatNum(amount) }))
        .sort((a, b) => b.amount - a.amount)

      if (!this.topData.length) this.topData = mergedWindow
      if (!this.groupData.length) {
        this.groupData = mergedWindow.map((i) => ({ name: i.name, value: i.amount }))
      }
    },

    normalizeTopData(raw) {
      if (raw?.data?.windowNames && Array.isArray(raw.data.windowNames)) {
        return raw.data.windowNames.map((name, idx) => ({
          name,
          amount: this.formatNum(raw.data.windowAmounts?.[idx] || 0)
        }))
      }
      const records = raw?.data?.results || raw?.data || raw || []
      if (!Array.isArray(records)) return []
      return records.map((i) => ({
        name: i.window || i.name || '未知窗口',
        amount: this.formatNum(i.amount || i.value || 0)
      }))
    },

    renderCharts() {
      const init = (id) => {
        const el = document.getElementById(id)
        if (!el) return null
        const existed = echarts.getInstanceByDom(el)
        const chart = existed || echarts.init(el)
        chart.clear()
        this.charts[id] = chart
        return chart
      }

      const topChart = init('topWindowChart')
      if (topChart) {
        const topBarData = this.topData.slice(0, 12)
        if (!topBarData.length) {
          topChart.setOption({
            title: { text: '暂无窗口排行数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } },
            xAxis: { show: false },
            yAxis: { show: false },
            series: []
          })
        } else {
          topChart.setOption({
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { left: '3%', right: '4%', bottom: '4%', top: '10%', containLabel: true },
            xAxis: {
              type: 'category',
              data: topBarData.map(i => i.name),
              axisLabel: {
                interval: 0,
                rotate: 35,
                formatter: (value) => {
                  const text = String(value || '')
                  return text.length > 6 ? `${text.slice(0, 6)}...` : text
                }
              }
            },
            yAxis: { type: 'value', name: '金额(元)' },
            series: [{
              type: 'bar',
              data: topBarData.map(i => i.amount),
              barMaxWidth: 22,
              itemStyle: {
                borderRadius: [6, 6, 0, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#6D8BFF' },
                  { offset: 1, color: '#4A69E2' }
                ])
              }
            }]
          })
      }
      }

      const pieChart = init('windowDistributionChart')
      if (pieChart) {
        const total = this.groupData.reduce((sum, i) => sum + Number(i.value || 0), 0)
        if (!total) {
          pieChart.setOption({
            title: { text: '暂无窗口分布数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } },
            series: []
          })
        } else {
        pieChart.setOption({
          tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
          legend: {
            type: 'scroll',
            bottom: 0,
            icon: 'circle',
            textStyle: { fontSize: 12 }
          },
          series: [{
            type: 'pie',
            center: ['50%', '46%'],
            radius: ['40%', '72%'],
            data: this.groupData,
            avoidLabelOverlap: true,
            minShowLabelAngle: 10,
            labelLine: { length: 10, length2: 10 },
            labelLayout: { hideOverlap: true },
            label: {
              formatter: (params) => {
                const percent = Number(params.percent || 0)
                if (percent < 4) return ''
                return `${params.name}\n¥${Number(params.value || 0).toFixed(0)} (${percent.toFixed(1)}%)`
              },
              fontSize: 11
            },
            itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 }
          }]
        })
        }
      }

      const trendChart = init('consumptionTrendChart')
      if (trendChart) {
        if (!this.trendData.length) {
          trendChart.setOption({
            title: { text: '暂无趋势数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } },
            xAxis: { show: false },
            yAxis: { show: false },
            series: []
          })
        } else {
          trendChart.setOption({
          tooltip: { trigger: 'axis' },
          grid: { left: '3%', right: '4%', bottom: '4%', top: '10%', containLabel: true },
          xAxis: { type: 'category', data: this.trendData.map(i => i.date), axisLabel: { rotate: 35 }, boundaryGap: false },
          yAxis: { type: 'value', name: '金额(元)' },
          series: [{
            type: 'line',
            smooth: true,
            data: this.trendData.map(i => i.value),
            lineStyle: { width: 3, color: '#25A18E' },
            itemStyle: { color: '#25A18E' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(37,161,142,0.28)' },
                { offset: 1, color: 'rgba(37,161,142,0.03)' }
              ])
            }
          }]
        })
        }
      }

      const mealChart = init('mealTypeChart')
      if (mealChart) {
        const total = this.mealTypeData.reduce((sum, i) => sum + Number(i.value || 0), 0)
        if (!total) {
          mealChart.setOption({
            title: { text: '暂无餐别数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } },
            series: []
          })
        } else {
        mealChart.setOption({
          tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
          legend: { bottom: 0, icon: 'circle' },
          series: [{
            type: 'pie',
            center: ['50%', '46%'],
            radius: ['40%', '72%'],
            data: this.mealTypeData,
            avoidLabelOverlap: true,
            minShowLabelAngle: 8,
            labelLine: { length: 10, length2: 10 },
            labelLayout: { hideOverlap: true },
            itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 }
          }]
        })
        }
      }

      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler)
      }
      this.resizeHandler = () => {
        Object.values(this.charts).forEach((chart) => {
          if (chart && typeof chart.resize === 'function') chart.resize()
        })
      }
      window.addEventListener('resize', this.resizeHandler)
    },

    async loadData() {
      this.loading = true
      this.loadError = ''

      try {
        const chartParams = this.buildParams(5000)
        const [statResult, listResult, topResult, groupResult] = await this.withTimeout(Promise.all([
          getConsumption(chartParams),
          getConsumptionData(chartParams),
          getConsumptionTop(chartParams),
          getConsumptionGroup(chartParams)
        ])
        , 60000)

        this.stat = {
          totalStudents: Number(statResult?.totalStudents || 0),
          totalAmount: this.formatNum(statResult?.totalAmount || 0),
          totalRecords: Number(statResult?.totalRecords || 0),
          averageConsumption: this.formatNum(statResult?.averageConsumption || 0)
        }

        this.topData = this.normalizeTopData(topResult)
        const grouped = this.normalizeTopData(groupResult)
        this.groupData = grouped.map((i) => ({ name: i.name, value: i.amount }))

        const rows = listResult?.records || listResult?.data?.records || listResult?.data || []
        const list = Array.isArray(rows) ? rows : []
        this.buildAggregations(list)

        this.$nextTick(() => this.renderCharts())
      } catch (error) {
        console.error('加载消费统计失败:', error)
        this.loadError = error?.message || '请检查后端服务后重试。'
        ElMessage.error(this.loadError)
      } finally {
        this.loading = false
      }
    },

    handleQuery() {
      this.loadData()
    },

    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: [],
        studentId: ''
      }
      this.majors = []
      this.classes = []
      this.loadData()
    }
  }
}
</script>

<style scoped>
.consumption-data-query {
  padding: 20px;
}

.consumption-data-query :deep(.el-card) {
  border-radius: 12px;
  border: 1px solid #edf1f7;
  box-shadow: 0 6px 18px rgba(18, 38, 63, 0.05);
}

.consumption-data-query :deep(.el-card__header) {
  font-weight: 600;
  color: #2f3a4f;
}

.stat-block {
  text-align: center;
  padding: 8px 0;
}

.stat-num {
  font-size: 24px;
  color: #303133;
  font-weight: 700;
}

.stat-text {
  margin-top: 6px;
  color: #909399;
}

.chart {
  height: 320px;
}

.error-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 1200px) {
  .chart {
    height: 290px;
  }
}
</style>
