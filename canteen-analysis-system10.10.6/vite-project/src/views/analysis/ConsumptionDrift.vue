<template>
  <!-- 页面：消费漂移检测与趋势展示 -->
  <div class="consumption-drift">
    <el-card>
      <template #header>
        <span>消费漂移检测</span>
      </template>

      <!-- 筛选条件 -->
      <el-form :model="queryForm" ref="queryForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="学院">
              <el-select v-model="queryForm.college" placeholder="全部学院" style="width: 100%">
                <el-option label="全部" value=""></el-option>
                <el-option v-for="college in colleges" :key="college" :label="college" :value="college"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="专业">
              <el-select v-model="queryForm.major" placeholder="全部专业" style="width: 100%">
                <el-option label="全部" value=""></el-option>
                <el-option v-for="major in majors" :key="major" :label="major" :value="major"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="年级">
              <el-select v-model="queryForm.grade" placeholder="全部年级" style="width: 100%">
                <el-option label="全部" value=""></el-option>
                <el-option v-for="grade in grades" :key="grade" :label="grade" :value="grade"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="班级">
              <el-select v-model="queryForm.class" placeholder="全部班级" style="width: 100%">
                <el-option label="全部" value=""></el-option>
                <el-option v-for="cls in classes" :key="cls" :label="cls" :value="cls"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="时间窗口">
              <el-select v-model="queryForm.timeWindow" placeholder="请选择时间窗口" style="width: 100%">
                <el-option label="7天" value="7"></el-option>
                <el-option label="15天" value="15"></el-option>
                <el-option label="30天" value="30"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
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
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="handleQuery">检测</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <!-- 消费漂移检测图表 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>消费漂移检测分析</span>
        </template>
        <div id="driftChart" ref="driftChart" class="drift-chart"></div>
      </el-card>

      <!-- 消费趋势图表（消费模式） -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>消费趋势分析（消费模式）</span>
        </template>
        <div id="consumptionChart" ref="consumptionChart" class="consumption-chart"></div>
      </el-card>

      <!-- 检测结果 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>漂移检测结果</span>
        </template>
        <el-table
            :data="pagedDriftResults"
            style="width: 100%"
            :empty-text="'暂无数据（后端未返回漂移结果）'"
        >
          <el-table-column prop="studentId" label="学号" width="120"></el-table-column>
          <el-table-column prop="name" label="姓名" width="100"></el-table-column>
          <el-table-column prop="college" label="学院" width="120"></el-table-column>
          <el-table-column prop="beforeDrift" label="漂移前均值" width="100">
            <template #default="scope">¥{{ scope.row.beforeDrift }}</template>
          </el-table-column>
          <el-table-column prop="afterDrift" label="漂移后均值" width="100">
            <template #default="scope">¥{{ scope.row.afterDrift }}</template>
          </el-table-column>
          <el-table-column prop="changeRate" label="变化率" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.changeRate > 0 ? 'danger' : 'success'">
                {{ scope.row.changeRate > 0 ? '+' : '' }}{{ scope.row.changeRate }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="scope">{{ scope.row.confidence }}%</template>
          </el-table-column>
          <el-table-column prop="detectDate" label="检测日期" width="120"></el-table-column>
        </el-table>
        <div class="pagination" style="margin-top: 12px; text-align: right;">
          <el-pagination
              v-model:current-page="resultPagination.currentPage"
              v-model:page-size="resultPagination.pageSize"
              :page-sizes="[20, 50, 100]"
              :total="resultPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleResultSizeChange"
              @current-change="handleResultPageChange"
          />
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import {getConsumptionDrift} from "@/api/user.js";
import {COLLEGES_MAJORS, generateClassNames} from '@/utils/const_value.js'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

export default {
  name: 'ConsumptionDrift',
  components: {},
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        timeWindow: '7',
        driftMethod: 'ElKmeans',
        studentId: '',
        timeBegin: '',
        timeEnd: '',
        dateRange: []
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      loading: false,
      driftResults: [],
      driftChartData: {
        dates: [],
        actual: [],
        trend: [],
        driftPoints: []
      },
      consumptionChartData: {
        dates: [],
        actual: [],
        trend: [],
        driftPoints: []
      },
      resultPagination: {
        currentPage: 1,
        pageSize: 20,
        total: 0
      },
      charts: {},
      resizeHandler: null,
      threshold: 0.05,
      chartMode: 'consumption' // consumption | pvalue
    }
  },
  mounted() {
    this.handleQuery()
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
  computed: {
    pagedDriftResults() {
      const start = (this.resultPagination.currentPage - 1) * this.resultPagination.pageSize
      const end = start + this.resultPagination.pageSize
      return this.driftResults.slice(start, end)
    }
  },
  methods: {
    async handleQuery() {
      const windowDays = Number(this.queryForm.timeWindow || 7)
      if (!this.queryForm.dateRange || this.queryForm.dateRange.length !== 2) {
        ElMessage.warning('请选择日期范围')
        return
      }
      const [start, end] = this.queryForm.dateRange
      const diff = Math.floor((new Date(end) - new Date(start)) / (24 * 60 * 60 * 1000)) + 1
      if (diff < windowDays * 2) {
        ElMessage.warning(`日期跨度需不少于 ${windowDays * 2} 天，以形成对比区间`)
        return
      }

      this.loading = true
      try {
        // 构建查询参数
        const params = {
          ...this.queryForm,
          className: this.queryForm.class || undefined,
          grade: this.queryForm.grade || undefined,
          timeWindow: windowDays
        }

        if (this.queryForm.dateRange?.length === 2) {
          params.timeBegin = this.queryForm.dateRange[0]
          params.timeEnd = this.queryForm.dateRange[1]
          params.startDate = this.queryForm.dateRange[0]
          params.endDate = this.queryForm.dateRange[1]
          // FastAPI 下划线风格兜底
          params.time_begin = this.queryForm.dateRange[0]
          params.time_end = this.queryForm.dateRange[1]
        }

        // 移除空值
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null || params[key] === undefined) {
            delete params[key]
          }
        })

        const result = await getConsumptionDrift(params)

        // 处理返回数据
        if (result?.detail) {
          throw new Error(result.detail)
        }

        if (result) {
          const data = result.data || result

          // 处理漂移检测结果
          if (data.results && Array.isArray(data.results)) {
            this.driftResults = data.results
          } else if (data.driftResults && Array.isArray(data.driftResults)) {
            this.driftResults = data.driftResults
          } else if (Array.isArray(data)) {
            this.driftResults = data
          } else {
            this.driftResults = []
          }

          this.resultPagination.total = this.driftResults.length
          this.resultPagination.currentPage = 1

          // 处理漂移图表数据
          if (Array.isArray(data.p_values)) {
            this.chartMode = 'pvalue'
            // 后端返回 p_values 数组时，绘制 p 值曲线并标记显著点
            const dates = (data.chartData && data.chartData.dates)
              ? data.chartData.dates
              : (() => {
                const base = data.time_begin || params.timeBegin || this.queryForm.dateRange?.[0] || '1970-01-01'
                const start = new Date(base)
                const step = Number(data.time_window || params.timeWindow || this.queryForm.timeWindow || 7)
                return data.p_values.map((_, idx) => {
                  const d = new Date(start)
                  d.setDate(d.getDate() + step * (idx + 1))
                  return d.toISOString().slice(0, 10)
                })
              })()
            const pvals = data.p_values.map(Number)
            this.driftChartData = {
              dates,
              actual: pvals, // 直接展示 p 值
              trend: [],
              driftPoints: pvals.map(v => ({
                value: v,
                itemStyle: { color: v < this.threshold ? '#ee6666' : '#91cc75' },
                symbolSize: v < this.threshold ? 12 : 6
              }))
            }
          } else if (data.chartData && data.chartData.dates && data.chartData.values) {
            this.chartMode = 'consumption'
            this.driftChartData = {
              dates: data.chartData.dates,
              actual: data.chartData.values.actual || [],
              trend: data.chartData.values.trend || [],
              driftPoints: data.chartData.values.driftPoints || []
            }
          } else if (data.timeSeries && Array.isArray(data.timeSeries)) {
            this.chartMode = 'consumption'
            // 从时间序列数据中提取
            this.driftChartData = {
              dates: data.timeSeries.map(item => item.date || item.time),
              actual: data.timeSeries.map(item => item.consumption || item.value),
              trend: data.timeSeries.map(item => item.trend || null),
              driftPoints: data.timeSeries.map((item) => item.isDrift ? (item.consumption || item.value) : null)
            }
          } else {
            this.chartMode = 'consumption'
            this.driftChartData = {
              dates: [],
              actual: [],
              trend: [],
              driftPoints: []
            }
          }

          // 构建消费模式图表数据（与 p 值模式并存）
          if (data.chartData && data.chartData.dates && data.chartData.values) {
            this.consumptionChartData = {
              dates: data.chartData.dates,
              actual: data.chartData.values.actual || [],
              trend: data.chartData.values.trend || [],
              driftPoints: data.chartData.values.driftPoints || []
            }
          } else if (data.timeSeries && Array.isArray(data.timeSeries)) {
            this.consumptionChartData = {
              dates: data.timeSeries.map(item => item.date || item.time),
              actual: data.timeSeries.map(item => item.consumption || item.value),
              trend: data.timeSeries.map(item => item.trend || null),
              driftPoints: data.timeSeries.map((item) => item.isDrift ? (item.consumption || item.value) : null)
            }
          } else if (this.driftResults.length) {
            const dates = this.driftResults.map(r => r.detectDate || r.date || '')
            const actual = this.driftResults.map(r => Number(r.afterDrift ?? r.after ?? r.value ?? 0))
            const trend = this.driftResults.map(r => Number(r.beforeDrift ?? r.before ?? 0))
            const driftPoints = this.driftResults.map((r, idx) => {
              const val = Number(r.changeRate ?? 0)
              return Math.abs(val) > 0 ? actual[idx] : null
            })
            this.consumptionChartData = { dates, actual, trend, driftPoints }
          } else {
            this.consumptionChartData = { dates: [], actual: [], trend: [], driftPoints: [] }
          }

          // 如果 chart 数据为空但有表格结果，使用表格结果兜底生成序列
          if ((!this.driftChartData.dates || this.driftChartData.dates.length === 0) && this.driftResults.length) {
            this.chartMode = 'consumption'
            const dates = this.driftResults.map(r => r.detectDate || r.date || '')
            const actual = this.driftResults.map(r => Number(r.afterDrift ?? r.after ?? r.value ?? 0))
            const trend = this.driftResults.map(r => Number(r.beforeDrift ?? r.before ?? 0))
            const driftPoints = this.driftResults.map((r, idx) => {
              const val = Number(r.changeRate ?? 0)
              return Math.abs(val) > 0 ? actual[idx] : null
            })
            this.driftChartData = { dates, actual, trend, driftPoints }
          }

          if (!this.driftChartData.dates?.length) {
            ElMessage.info('暂无漂移检测数据，请调整筛选条件')
          }
          console.log('drift chart data:', this.chartMode, this.driftChartData)
        } else {
          this.driftResults = []
          this.resultPagination.total = 0
          this.driftChartData = {
            dates: [],
            actual: [],
            trend: [],
            driftPoints: []
          }
        }

        // 初始化图表
        this.$nextTick(() => {
          this.initDriftChart()
          this.initConsumptionChart()
        })
      } catch (error) {
        console.error('漂移检测失败:', error)
        ElMessage.error('漂移检测失败: ' + (error.message || '未知错误'))
        this.driftResults = []
        this.resultPagination.total = 0
        this.driftChartData = {
          dates: [],
          actual: [],
          trend: [],
          driftPoints: []
        }
        this.consumptionChartData = {
          dates: [],
          actual: [],
          trend: [],
          driftPoints: []
        }
        this.chartMode = 'consumption'
      } finally {
        this.loading = false
      }
    },
    handleResultPageChange(page) {
      this.resultPagination.currentPage = page
    },
    handleResultSizeChange(size) {
      this.resultPagination.pageSize = size
      this.resultPagination.currentPage = 1
    },
    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        timeWindow: '7',
        driftMethod: 'ElKmeans',
        studentId: '',
        timeBegin: '',
        timeEnd: '',
        dateRange: []
      }
      this.majors = []
      this.classes = []
      this.driftResults = []
      this.resultPagination = { currentPage: 1, pageSize: 20, total: 0 }
      this.driftChartData = {
        dates: [],
        actual: [],
        trend: [],
        driftPoints: []
      }
      this.chartMode = 'consumption'

      // 清理图表
      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler)
        this.resizeHandler = null
      }
      Object.values(this.charts || {}).forEach(c => c?.dispose())
      this.charts = {}
    },
    initDriftChart() {
      const el = this.$refs.driftChart || document.getElementById('driftChart')
      if (!el) return
      const rect = el.getBoundingClientRect()
      console.log('drift chart dom size:', rect.width, rect.height)
      if (!rect.width || !rect.height) {
        // 强制一个可见尺寸，防止父容器折叠导致看不到图
        el.style.width = '100%'
        el.style.minWidth = '600px'
        el.style.height = '400px'
        el.style.minHeight = '400px'
      }
      const chart = echarts.getInstanceByDom(el) || echarts.init(el)
      chart.clear()
      this.charts.driftChart = chart

      const isPValue = this.chartMode === 'pvalue'
      const legendNames = isPValue
          ? ['p值', `显著性阈值(p<${this.threshold})`, '检测点']
          : ['实际消费', '趋势线', '检测点']

      const dates = [...(this.driftChartData.dates || [])]
      const actual = [...(this.driftChartData.actual || [])]
      const trend = [...(this.driftChartData.trend || [])]
      const driftPoints = [...(this.driftChartData.driftPoints || [])]

      if (dates.length > 0) {
        const series = []

        series.push({
          name: isPValue ? 'p值' : '实际消费',
          type: 'line',
          data: actual,
          smooth: true,
          lineStyle: {
            color: '#5470c6',
            width: 3
          },
          symbol: 'circle',
          symbolSize: 6,
          showSymbol: true,
          showAllSymbol: true,
          connectNulls: true,
          areaStyle: isPValue ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(84,112,198,0.25)' },
              { offset: 1, color: 'rgba(84,112,198,0)' }
            ])
          } : undefined
        })

        if (!isPValue && trend.length) {
          series.push({
            name: '趋势线',
            type: 'line',
            data: trend,
            smooth: true,
            lineStyle: {
              color: '#91cc75',
              type: 'dashed',
              width: 2
            }
          })
        }

        if (isPValue) {
          series.push({
            name: `显著性阈值(p<${this.threshold})`,
            type: 'line',
            data: new Array(dates.length).fill(this.threshold),
            smooth: false,
            lineStyle: { color: '#fac858', type: 'dotted', width: 1.5 },
            symbol: 'none'
          })
        }

        series.push({
          name: '检测点',
          type: 'scatter',
          data: driftPoints,
          symbolSize: 12,
          itemStyle: {
            color: '#ee6666'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        })

        const option = {
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              let result = params[0].name + '<br/>'
              params.forEach(param => {
                if (param.value !== null && param.value !== undefined) {
                  const val = Number(param.value)
                  const formatted = isNaN(val) ? param.value : (Math.abs(val) < 1 ? val.toFixed(4) : val.toFixed(2))
                  result += param.seriesName + ': ' + formatted + '<br/>'
                }
              })
              return result
            }
          },
          legend: {
            data: legendNames
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '8%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
            axisLabel: {
              color: '#666'
            },
            axisLine: { lineStyle: { color: '#ccc' } }
          },
          yAxis: {
            type: 'value',
            name: isPValue ? 'p-value' : '消费金额(元)',
            min: isPValue ? 0 : undefined,
            max: isPValue ? 1 : undefined,
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#eee' } }
          },
          series
        }
        console.log('setOption option:', option)
        chart.setOption(option, true)
        chart.resize({
          width: el.clientWidth || 800,
          height: el.clientHeight || 400
        })
      } else {
        chart.setOption({
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: {
              color: '#999',
              fontSize: 14
            }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        })
      }

      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler)
      }
      this.resizeHandler = () => {
        Object.values(this.charts || {}).forEach(c => c?.resize())
      }
      window.addEventListener('resize', this.resizeHandler)
    }
    ,
    initConsumptionChart() {
      const el = this.$refs.consumptionChart || document.getElementById('consumptionChart')
      if (!el) return
      const rect = el.getBoundingClientRect()
      if (!rect.width || !rect.height) {
        el.style.width = '100%'
        el.style.minWidth = '600px'
        el.style.height = '400px'
        el.style.minHeight = '400px'
      }
      const chart = echarts.getInstanceByDom(el) || echarts.init(el)
      chart.clear()
      this.charts.consumptionChart = chart

      const dates = [...(this.consumptionChartData.dates || [])]
      const actual = [...(this.consumptionChartData.actual || [])]
      const trend = [...(this.consumptionChartData.trend || [])]
      const driftPoints = [...(this.consumptionChartData.driftPoints || [])]

      if (dates.length > 0) {
        const series = []
        series.push({
          name: '实际消费',
          type: 'line',
          data: actual,
          smooth: true,
          lineStyle: { color: '#5470c6', width: 3 },
          symbol: 'circle',
          symbolSize: 6,
          showSymbol: true,
          connectNulls: true
        })

        if (trend.length) {
          series.push({
            name: '趋势线',
            type: 'line',
            data: trend,
            smooth: true,
            lineStyle: { color: '#91cc75', type: 'dashed', width: 2 }
          })
        }

        series.push({
          name: '检测点',
          type: 'scatter',
          data: driftPoints,
          symbolSize: 12,
          itemStyle: { color: '#ee6666' }
        })

        const option = {
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              let result = params[0].name + '<br/>'
              params.forEach(param => {
                if (param.value !== null && param.value !== undefined) {
                  const val = Number(param.value)
                  const formatted = isNaN(val) ? param.value : val.toFixed(2)
                  result += param.seriesName + ': ' + formatted + '<br/>'
                }
              })
              return result
            }
          },
          legend: { data: ['实际消费', '趋势线', '检测点'] },
          grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
            axisLabel: { color: '#666' },
            axisLine: { lineStyle: { color: '#ccc' } }
          },
          yAxis: {
            type: 'value',
            name: '消费金额(元)',
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#eee' } }
          },
          series
        }
        chart.setOption(option, true)
        chart.resize({
          width: el.clientWidth || 800,
          height: el.clientHeight || 400
        })
      } else {
        chart.setOption({
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        })
      }
    }
  }
}
</script>

<style scoped>
.consumption-drift {
  padding: 20px;
}

.drift-chart {
  width: 100%;
  min-width: 600px;
  height: 400px;
  min-height: 400px;
}

.consumption-chart {
  width: 100%;
  min-width: 600px;
  height: 400px;
  min-height: 400px;
}
</style>