<template>
  <!-- 页面：贫困生鉴别与聚类分析 -->
  <div class="poverty-identification">
    <el-card>
      <template #header>
        <span>贫困生识别</span>
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
            <el-form-item label="聚类算法">
              <el-tag type="info">K-Means</el-tag>
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
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleIdentify">鉴别</el-button>
              <el-button :disabled="loading" @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <!-- 聚类分析图表 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>消费聚类分析</span>
            </template>
            <BaseChart
                :options="scatterOptions"
                :loading="loading"
                :container-style="{ width: '100%', height: '400px' }"
            />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>群体分布统计</span>
            </template>
            <BaseChart
                :options="pieOptions"
                :loading="loading"
                :container-style="{ width: '100%', height: '400px' }"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 鉴别结果 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>贫困生鉴别结果</span>
        </template>
        <el-table :data="pagedPovertyResults" style="width: 100%">
          <el-table-column prop="studentId" label="学号" width="140">
            <template #default="scope">{{ scope.row.studentId || '-' }}</template>
          </el-table-column>
          <el-table-column prop="name" label="姓名" width="100">
            <template #default="scope">{{ scope.row.name || '-' }}</template>
          </el-table-column>
          <el-table-column prop="college" label="学院" min-width="140">
            <template #default="scope">{{ scope.row.college || '-' }}</template>
          </el-table-column>
          <el-table-column prop="major" label="专业" min-width="160">
            <template #default="scope">{{ scope.row.major || '-' }}</template>
          </el-table-column>
          <el-table-column prop="className" label="班级" min-width="120">
            <template #default="scope">{{ scope.row.className || '-' }}</template>
          </el-table-column>
          <el-table-column prop="monthlyAvg" label="月均消费" width="100">
            <template #default="scope">¥{{ Number(scope.row.monthlyAvg || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="dailyAvg" label="日均消费" width="100">
            <template #default="scope">¥{{ Number(scope.row.dailyAvg || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="clusterType" label="消费类型" width="120">
            <template #default="scope">
              <el-tag :type="getClusterType(scope.row.clusterType)">
                {{ scope.row.clusterType || '-' }}
              </el-tag>
            </template>
          </el-table-column>
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
import {getPovertyIdentification} from "@/api/user.js";
import {COLLEGES_MAJORS, generateClassNames} from '@/utils/const_value.js'
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/Charts/BaseChart.vue'

export default {
  name: 'PovertyIdentification',
  components: {
    BaseChart
  },
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        clusterMethod: 'kmeans',
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
      povertyResults: [],
      clusterScatterData: [],
      distributionPieData: [],
      resultPagination: {
        currentPage: 1,
        pageSize: 20,
        total: 0
      }
    }
  },
  mounted() {
    // 初始化图表
  },
  computed: {
    pagedPovertyResults() {
      const start = (this.resultPagination.currentPage - 1) * this.resultPagination.pageSize
      const end = start + this.resultPagination.pageSize
      return this.povertyResults.slice(start, end)
    },
    scatterOptions() {
      const hasData = this.clusterScatterData.length > 0 && this.clusterScatterData[0].data?.length > 0
      if (!hasData) {
        return {
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      return {
        toolbox: {
          feature: {
            dataZoom: { yAxisIndex: 'none' },
            restore: {},
            saveAsImage: {}
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const point = params.data || {}
            const dailyAmount = point.value ? point.value[0] : params.value?.[0]
            const dailyCount = point.value ? point.value[1] : params.value?.[1]
            const clusterType = point.clusterType || '未知'
            const sid = point.studentId || '未知'
            const name = point.name || '未知'
            return `学号: ${sid}<br/>姓名: ${name}<br/>日均消费: ${Number(dailyAmount || 0).toFixed(2)} 元<br/>日均次数: ${Number(dailyCount || 0).toFixed(2)} 次<br/>类型: ${clusterType}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '16%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '日均消费(元)',
          nameLocation: 'middle',
          nameGap: 32,
          splitLine: { lineStyle: { color: '#f0f2f5' } }
        },
        yAxis: {
          type: 'value',
          name: '日均次数',
          nameLocation: 'end',
          splitLine: { lineStyle: { color: '#f0f2f5' } }
        },
        series: [
          {
            name: '消费聚类分析',
            type: 'scatter',
            data: this.clusterScatterData[0].data,
            symbolSize: (val, params) => {
              const p = params?.data || {}
              const base = Number(p.povertyIndex || 0)
              return Math.min(18, Math.max(8, 8 + base * 20))
            },
            itemStyle: {
              color: (params) => {
                const clusterType = params.data?.clusterType
                const colorMap = {
                  '高消费': '#ee6666',
                  '低消费': '#5470c6',
                  '中等消费': '#91cc75',
                  '普通消费1': '#5470c6',
                  '普通消费2': '#91cc75',
                  '贫困生': '#fac858'
                }
                return colorMap[clusterType] || '#909399'
              },
              opacity: 0.9
            }
          }
        ]
      }
    },
    pieOptions() {
      const hasData = this.distributionPieData.length > 0
      if (!hasData) {
        return {
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          series: []
        }
      }

      return {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '消费群体分布',
            type: 'pie',
            radius: '55%',
            data: this.distributionPieData,
            label: { formatter: '{b}: {d}%' },
            itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    }
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
      const params = {
        college: this.queryForm.college?.trim() || undefined,
        major: this.queryForm.major?.trim() || undefined,
        grade: this.queryForm.grade || undefined,
        className: this.queryForm.class?.trim() || undefined,
        clusterMethod: this.queryForm.clusterMethod || 'kmeans',
        studentId: this.queryForm.studentId?.trim() || undefined
      }

      if (this.queryForm.dateRange?.length === 2) {
        params.timeBegin = this.queryForm.dateRange[0]
        params.timeEnd = this.queryForm.dateRange[1]
        params.startDate = this.queryForm.dateRange[0]
        params.endDate = this.queryForm.dateRange[1]
      }

      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      return params
    },
    async handleIdentify() {
      this.loading = true
      try {
        const params = this.buildQueryParams()

        const result = await getPovertyIdentification(params)
        // 注意：后端本身包含 data 字段（特征数据），不能直接优先取 result.data
        const hasRootResults = result && (result.results || result.clusterData || result.distributionData || result.centers)
        const data = hasRootResults ? result : (result && result.data ? result.data : result)

        // 处理返回数据
        if (data) {

          // 处理贫困生鉴别结果，并做字段兜底
          if (data.results && Array.isArray(data.results)) {
            this.povertyResults = data.results
          } else if (data.povertyResults && Array.isArray(data.povertyResults)) {
            this.povertyResults = data.povertyResults
          } else if (Array.isArray(data)) {
            this.povertyResults = data
          } else {
            this.povertyResults = []
          }

          this.resultPagination.total = this.povertyResults.length
          this.resultPagination.currentPage = 1

          // 兜底缺失字段
          this.povertyResults = this.povertyResults.map(item => ({
            studentId: item.studentId || item.student_id || '-',
            name: (item.name ?? item.studentName ?? item.student_name ?? '-').toString(),
            college: (item.college ?? item.collegeName ?? item.college_name ?? '-').toString(),
            major: (item.major ?? item.majorName ?? item.major_name ?? '-').toString(),
            className: (item.className ?? item.class_name ?? '-').toString(),
            monthlyAvg: Number(item.monthlyAvg ?? item.monthly_avg ?? 0),
            dailyAvg: Number(item.dailyAvg ?? item.daily_avg ?? 0),
            clusterType: item.clusterType || item.type || '普通消费',
            povertyIndex: Number(item.povertyIndex ?? item.poverty_index ?? 0)
          }))


          // 聚类散点图使用结果列表，保证和表格索引一致
          if (data.clusterData && Array.isArray(data.clusterData) && data.clusterData.length > 0) {
            this.clusterScatterData = [{
              name: '消费聚类分析',
              data: data.clusterData.map(p => ({
                value: [Number(p.x ?? p.monthlyAvg ?? 0), Number(p.y ?? p.dailyAvg ?? 0)],
                clusterType: p.label || p.clusterType || '普通消费',
                studentId: p.studentId || '-',
                name: p.name || '-',
                major: p.major || '-',
                className: p.className || p.class_name || '-',
                povertyIndex: Number(p.povertyIndex ?? p.poverty_index ?? 0)
              }))
            }]
          } else {
            this.clusterScatterData = this.povertyResults.length > 0 ? [{
              name: '消费聚类分析',
              data: this.povertyResults.map(item => ({
                value: [Number(item.monthlyAvg || 0), Number(item.dailyAvg || 0)],
                clusterType: item.clusterType,
                studentId: item.studentId,
                name: item.name,
                povertyIndex: Number(item.povertyIndex || 0)
              }))
            }] : []
          }


          // 处理群体分布饼图数据
          if (data.distributionData && Array.isArray(data.distributionData)) {
            this.distributionPieData = data.distributionData
          } else {
            const distributionMap = {}
            this.povertyResults.forEach(item => {
              const type = item.clusterType || item.type || '未知'
              distributionMap[type] = (distributionMap[type] || 0) + 1
            })
            this.distributionPieData = Object.keys(distributionMap).map(key => ({
              name: key,
              value: distributionMap[key]
            }))
          }
        } else {
          this.povertyResults = []
          this.clusterScatterData = []
          this.distributionPieData = []
          this.resultPagination.total = 0
        }

      } catch (error) {
        console.error('贫困生鉴别失败:', error)
        ElMessage.error('贫困生鉴别失败: ' + (error.message || '未知错误'))
        this.povertyResults = []
        this.clusterScatterData = []
        this.distributionPieData = []
        this.resultPagination.total = 0
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
        clusterMethod: 'kmeans',
        studentId: '',
        timeBegin: '',
        timeEnd: '',
        dateRange: []
      }
      this.majors = []
      this.classes = []
      this.povertyResults = []
      this.clusterScatterData = []
      this.distributionPieData = []
      this.resultPagination = { currentPage: 1, pageSize: 20, total: 0 }
    },
    getClusterType(type) {
      const typeMap = {
        '贫困生': 'danger',
        '普通消费1': 'info',
        '普通消费2': 'warning',
        '高消费': 'success'
      }
      return typeMap[type] || 'info'
    },
  }
}
</script>

<style scoped>
.poverty-identification {
  padding: 20px;
}

</style>