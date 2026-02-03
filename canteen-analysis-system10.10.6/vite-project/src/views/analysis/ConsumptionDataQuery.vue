<template>
  <!-- 页面：消费数据查询与分析明细 -->
  <div class="consumption-data-query">
    <el-card>
      <template #header>
        <span>消费数据统计</span>
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
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="queryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="handleQuery">查询</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <!-- 统计信息 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="6">
          <el-card>
            <div style="text-align: center;">
              <div style="font-size: 24px; color: #409EFF; font-weight: bold;">{{ stat.totalStudents }}</div>
              <div style="color: #909399; margin-top: 5px;">查询学生数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div style="text-align: center;">
              <div style="font-size: 24px; color: #67C23A; font-weight: bold;">¥{{ stat.totalAmount }}</div>
              <div style="color: #909399; margin-top: 5px;">总消费金额</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div style="text-align: center;">
              <div style="font-size: 24px; color: #E6A23C; font-weight: bold;">{{ stat.totalRecords }}</div>
              <div style="color: #909399; margin-top: 5px;">消费记录数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div style="text-align: center;">
              <div style="font-size: 24px; color: #F56C6C; font-weight: bold;">¥{{ stat.averageConsumption }}</div>
              <div style="color: #909399; margin-top: 5px;">人均消费额</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 图表展示 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>TOP消费窗口排行</span>
            </template>
            <div id="topWindowChart" style="height: 300px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>各窗口消费分布</span>
            </template>
            <div id="windowDistributionChart" style="height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>日消费趋势</span>
            </template>
            <div id="consumptionTrendChart" style="height: 320px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>餐别消费占比</span>
            </template>
            <div id="mealTypeChart" style="height: 320px;"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 消费明细表格 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>消费明细</span>
        </template>
        <el-table :data="tableData" v-loading="loading" style="width: 100%">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="studentId" label="学号" width="120" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="college" label="学院" width="140" />
          <el-table-column prop="major" label="专业" width="160" />
          <el-table-column prop="consumptionTime" label="消费时间" min-width="160" />
          <el-table-column prop="windowId" label="窗口" width="100" />
          <el-table-column prop="amount" label="消费金额" width="120">
            <template #default="scope">¥{{ scope.row.amount?.toFixed ? scope.row.amount.toFixed(2) : scope.row.amount }}</template>
          </el-table-column>
          <el-table-column prop="mealType" label="餐别" width="100" />
        </el-table>
        <div style="margin-top: 12px; text-align: right;">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSize"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import {getConsumptionTop, getConsumptionGroup, getConsumption, getConsumptionData} from "@/api/user.js";
import {COLLEGES_MAJORS, generateClassNames} from '@/utils/const_value.js'
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
        timeBegin: '',
        timeEnd: '',
        studentId: '',
        page: 1,
        pageSize: 20
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      loading: false,
      stat: {
        totalStudents: 0,
        totalAmount: 0,
        totalRecords: 0,
        averageConsumption: 0
      },
      topData: [],
      groupData: [],
      tableData: [],
      trendData: [],
      mealTypeData: [],
      charts: {},
      resizeHandler: null,
      chartPageSize: 5000,
      pagination: {
        currentPage: 1,
        pageSize: 20,
        total: 0
      }
    }
  },
  mounted() {
    this.loadData();
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
    buildQueryParams() {
      const [timeBegin, timeEnd] = Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2
        ? this.queryForm.dateRange
        : []

      const params = {
        college: this.queryForm.college?.trim() || undefined,
        major: this.queryForm.major?.trim() || undefined,
        grade: this.queryForm.grade?.trim() || undefined,
        className: this.queryForm.class?.trim() || undefined,
        studentId: this.queryForm.studentId?.trim() || undefined,
        timeBegin: timeBegin || undefined,
        timeEnd: timeEnd || undefined,
        page: this.pagination.currentPage,
        pageSize: this.pagination.pageSize
      }

      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })

      return params
    },
    async loadData() {
      this.loading = true
      try {
        const params = this.buildQueryParams()
        console.log('[consumption] query params', params)

        const chartParams = {
          ...params,
          page: 1,
          pageSize: this.chartPageSize
        }
        
        // 并行请求数据
        const [statResult, listResult, topResult, groupResult, chartListResult] = await Promise.all([
          getConsumption(params),
          getConsumptionData(params),
          getConsumptionTop(params),
          getConsumptionGroup(params),
          getConsumptionData(chartParams)
        ])

        // 统计卡片
        if (statResult && (statResult.totalAmount !== undefined || statResult.totalRecords !== undefined)) {
          this.stat = {
            totalStudents: statResult.totalStudents || 0,
            totalAmount: statResult.totalAmount || 0,
            totalRecords: statResult.totalRecords || 0,
            averageConsumption: statResult.averageConsumption || 0
          }
        } else {
          this.stat = { totalStudents: 0, totalAmount: 0, totalRecords: 0, averageConsumption: 0 }
        }

        // 表格数据
        if (listResult) {
          const records = listResult.records || listResult.data?.records || listResult.data || []
          const arr = Array.isArray(records) ? records : []

          const mapped = arr.map(item => {
            const studentId = item.studentId || item.student_id || ''
            const college = item.college || item.collegeName || '-'
            const major = item.major || item.majorName || '-'
            const name = item.name || item.studentName || '-'
            return {
              studentId: studentId || '-',
              name,
              college,
              major,
              consumptionTime: this.formatTime(item.consumptionTime || item.consumption_time),
              windowId: item.windowId || item.window_id || '-',
              amount: item.amount || 0,
              mealType: item.mealType || item.meal_type || '未知'
            }
          })
          const total = listResult.total || listResult.totalCount || listResult.data?.total || mapped.length
          this.tableData = mapped
          this.pagination.total = total
          if (!mapped.length) {
            ElMessage.warning('未查询到消费明细，请检查筛选条件')
          }
        }
        
        // 处理TOP数据 - API返回格式: {windowNames: [], windowAmounts: [], windowPercent: []}
        if (topResult && topResult.data) {
          const data = topResult.data
          if (data.windowNames && Array.isArray(data.windowNames)) {
            // 转换为图表需要的格式
            this.topData = data.windowNames.map((name, index) => ({
              window: name || `窗口${index + 1}`,
              name: name || `窗口${index + 1}`,
              amount: data.windowAmounts && data.windowAmounts[index] ? data.windowAmounts[index] : 0,
              percent: data.windowPercent && data.windowPercent[index] ? data.windowPercent[index] : 0
            }))
          } else if (Array.isArray(data)) {
            this.topData = data
          } else if (data.results && Array.isArray(data.results)) {
            this.topData = data.results
          } else if (data.topData && Array.isArray(data.topData)) {
            this.topData = data.topData
          } else {
            this.topData = []
          }
        } else {
          this.topData = []
        }
        
        // 处理群体数据 - API返回格式: {windowNames: [], windowAmounts: [], windowPercent: []}
        if (groupResult && groupResult.data) {
          const data = groupResult.data
          if (data.windowNames && Array.isArray(data.windowNames)) {
            // 转换为图表需要的格式
            this.groupData = data.windowNames.map((name, index) => ({
              window: name || `窗口${index + 1}`,
              name: name || `窗口${index + 1}`,
              amount: data.windowAmounts && data.windowAmounts[index] ? data.windowAmounts[index] : 0,
              percent: data.windowPercent && data.windowPercent[index] ? data.windowPercent[index] : 0
            }))
          } else if (Array.isArray(data)) {
            this.groupData = data
          } else if (data.results && Array.isArray(data.results)) {
            this.groupData = data.results
          } else if (data.groupData && Array.isArray(data.groupData)) {
            this.groupData = data.groupData
          } else {
            this.groupData = []
          }
        } else {
          this.groupData = []
        }
        
        // 初始化图表
        const chartRecords = (() => {
          const records = chartListResult?.records || chartListResult?.data?.records || chartListResult?.data || []
          return Array.isArray(records) ? records : []
        })()

        this.$nextTick(() => {
          this.buildAggregations(chartRecords)
          this.initCharts()
        })
      } catch (error) {
        console.error('加载统计数据失败:', error)
        ElMessage.error('加载统计数据失败: ' + (error.message || '未知错误'))
      } finally {
        this.loading = false
      }
    },
    formatTime(val) {
      if (!val) return ''
      if (typeof val === 'string') return val.replace('T', ' ')
      return val
    },
    async handleQuery() {
      this.pagination.currentPage = 1
      this.queryForm.page = 1
      await this.loadData()
    },
    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: [],
        timeBegin: '',
        timeEnd: '',
        studentId: '',
        page: 1,
        pageSize: 20
      }
      this.pagination.currentPage = 1
      this.pagination.pageSize = 20
      this.majors = []
      this.classes = []
      this.topData = []
      this.groupData = []
      this.tableData = []
      this.stat = { totalStudents: 0, totalAmount: 0, totalRecords: 0, averageConsumption: 0 }
      this.loadData()
    },
    handlePageChange(page) {
      this.pagination.currentPage = page
      this.queryForm.page = page
      this.loadData()
    },
    handlePageSize(size) {
      this.pagination.pageSize = size
      this.queryForm.pageSize = size
      this.pagination.currentPage = 1
      this.queryForm.page = 1
      this.loadData()
    },

    // 聚合：消费趋势、餐别占比，缺省兜底窗口聚合
    buildAggregations(sourceRows = null) {
      const trendMap = new Map()
      const mealMap = new Map()
      const windowMap = new Map()
      const rows = Array.isArray(sourceRows) && sourceRows.length ? sourceRows : this.tableData
      rows.forEach(row => {
        const dateKey = (row.consumptionTime || '').split(' ')[0] || ''
        const amt = Number(row.amount || 0)
        if (dateKey) {
          trendMap.set(dateKey, (trendMap.get(dateKey) || 0) + amt)
        }

        const meal = row.mealType || '未知'
        mealMap.set(meal, (mealMap.get(meal) || 0) + amt)

        const windowKey = row.windowId || row.window || '未知'
        windowMap.set(windowKey, (windowMap.get(windowKey) || 0) + amt)
      })

      this.trendData = Array.from(trendMap.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([date, val]) => ({ date, value: Number(val.toFixed(2)) }))

      const totalMeal = Array.from(mealMap.values()).reduce((s, v) => s + v, 0) || 1
      this.mealTypeData = Array.from(mealMap.entries()).map(([name, val]) => ({
        name,
        value: Number(val.toFixed(2)),
        percent: Number(((val * 100) / totalMeal).toFixed(2))
      }))

      // 兜底窗口聚合：当接口无数据时使用表格聚合结果
      if (!this.topData.length && windowMap.size > 0) {
        const windowTotal = Array.from(windowMap.values()).reduce((s, v) => s + v, 0) || 1
        const windowList = Array.from(windowMap.entries())
          .map(([name, val]) => ({
            window: name,
            name,
            amount: Number(val.toFixed(2)),
            percent: Number(((val * 100) / windowTotal).toFixed(2))
          }))
          .sort((a, b) => b.amount - a.amount)
        this.topData = windowList
      }

      if (!this.groupData.length && this.topData.length) {
        // groupData 需要 value 字段给饼图
        this.groupData = this.topData.map(item => ({
          window: item.window || item.name,
          name: item.name || item.window,
          amount: item.amount || item.value || 0,
          value: item.amount || item.value || 0,
          percent: item.percent || 0
        }))
      }
    },
    initCharts() {
      const getChart = (id) => {
        const el = document.getElementById(id)
        if (!el) return null
        const existing = echarts.getInstanceByDom(el)
        const inst = existing || echarts.init(el)
        inst.clear()
        this.charts[id] = inst
        return inst
      }

      // TOP消费窗口柱形图
      const topWindowChart = getChart('topWindowChart')
      if (topWindowChart) {
      if (this.topData && this.topData.length > 0) {
        const windowNames = this.topData.map(item => item.window || item.name || '未知')
        const amounts = this.topData.map(item => item.amount || item.value || 0)
        
        topWindowChart.setOption({
          title: { show: false },
          tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: '{b}: ¥{c}'
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: windowNames,
            axisLabel: {
              rotate: 45
            }
          },
          yAxis: {
            type: 'value',
            name: '消费金额(元)'
          },
          series: [{
            name: '消费金额',
            data: amounts,
            type: 'bar',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#5470c6' },
                { offset: 1, color: '#91cc75' }
              ])
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        })
      } else {
        topWindowChart.setOption({
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        })
      }
      }

      // 各窗口消费分布饼图
      const windowDistributionChart = getChart('windowDistributionChart')
      if (windowDistributionChart) {
      if (this.groupData && this.groupData.length > 0) {
        const pieData = this.groupData.map(item => ({
          name: item.name || item.window || '未知',
          value: item.value || item.amount || 0
        }))
        
        windowDistributionChart.setOption({
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: ¥{c} ({d}%)'
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: '#606266' }
          },
          series: [{
            name: '消费分布',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            data: pieData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              show: true,
              formatter: '{b}: {d}%'
            }
          }]
        })
      } else {
        windowDistributionChart.setOption({
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          series: []
        })
      }
      }

      // 日消费趋势
      const trendChart = getChart('consumptionTrendChart')
      if (trendChart) {
      if (this.trendData && this.trendData.length > 0) {
        trendChart.setOption({
          title: { show: false },
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              const d = params[0]
              return `${d.name}<br/>消费总额: ¥${d.value}`
            }
          },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: { type: 'category', data: this.trendData.map(i => i.date), axisLabel: { rotate: 45 } },
          yAxis: { type: 'value', name: '金额(元)' },
          series: [{
            name: '消费总额',
            data: this.trendData.map(i => i.value),
            type: 'line',
            smooth: true,
            lineStyle: { color: '#5470c6', width: 3 },
            areaStyle: {
              color: {
                type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(84,112,198,0.35)' },
                  { offset: 1, color: 'rgba(84,112,198,0.05)' }
                ]
              }
            }
          }]
        })
      } else {
        trendChart.setOption({
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
          xAxis: { show: false }, yAxis: { show: false }, series: []
        })
      }
      }

      // 餐别消费占比
      const mealTypeChart = getChart('mealTypeChart')
      if (mealTypeChart) {
      if (this.mealTypeData && this.mealTypeData.length > 0) {
        mealTypeChart.setOption({
          title: { show: false },
          tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
          legend: { orient: 'vertical', left: 'left' },
          series: [{
            name: '餐别占比',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            data: this.mealTypeData,
            emphasis: {
              itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }
            },
            label: { formatter: '{b}: {d}%'}
          }]
        })
      } else {
        mealTypeChart.setOption({
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
          series: []
        })
      }
      }
      
      // 响应式调整
      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler)
      }
      this.resizeHandler = () => {
        Object.values(this.charts || {}).forEach(c => {
          if (c && typeof c.resize === 'function') c.resize()
        })
      }
      window.addEventListener('resize', this.resizeHandler)
    }
  }
}
</script>

<style scoped>
.consumption-data-query {
  padding: 20px;
}
</style>