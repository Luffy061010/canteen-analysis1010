<template>
  <!-- 页面：成绩与消费关联性分析 -->
  <div class="score-correlation">
    <el-card>
      <template #header>
        <span>成绩关联分析</span>
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
<!--          <el-col :span="8">-->
<!--            <el-form-item label="科目">-->
<!--              <el-select v-model="queryForm.subject" placeholder="请选择科目" style="width: 100%">-->
<!--                <el-option label="全部" value=""></el-option>-->
<!--                <el-option label="数学" value="math"></el-option>-->
<!--                <el-option label="英语" value="english"></el-option>-->
<!--                <el-option label="专业课" value="major"></el-option>-->
<!--                <el-option label="总绩点" value="gpa"></el-option>-->
<!--              </el-select>-->
<!--            </el-form-item>-->
<!--          </el-col>-->
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="handleAnalyze">分析</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <!-- 关联性分析图表（热力图） -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>成绩与消费关联性热力图</span>
        </template>
        <BaseChart
          :options="heatmapOptions"
          :loading="loading"
          :container-style="{ height: '420px', width: '100%' }"
        />
      </el-card>

      <!-- 单体分析 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>单体分析</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card shadow="never" class="single-card">
              <div class="single-title">学生画像</div>
              <el-row :gutter="8" class="single-input-row">
                <el-col :span="16">
                  <el-input v-model="queryForm.studentId" placeholder="输入学号" size="small" />
                </el-col>
                <el-col :span="8">
                  <el-button type="primary" size="small" @click="handleAnalyze">查询</el-button>
                </el-col>
              </el-row>
              <div class="single-item">
                <span class="label">学号：</span>
                <span class="value">{{ selectedStudent.studentId || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">姓名：</span>
                <span class="value">{{ selectedStudent.name || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">学院：</span>
                <span class="value">{{ selectedStudent.college || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">专业：</span>
                <span class="value">{{ selectedStudent.major || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">班级：</span>
                <span class="value">{{ selectedStudent.className || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">年级：</span>
                <span class="value">{{ selectedStudent.grade || '-' }}</span>
              </div>
              <div class="single-item">
                <span class="label">日均消费：</span>
                <span class="value">¥{{ Number(selectedStudent.dailyAvg || 0).toFixed(2) }}</span>
              </div>
              <div class="single-item">
                <span class="label">月均消费：</span>
                <span class="value">¥{{ Number(selectedStudent.monthlyAvg || 0).toFixed(2) }}</span>
              </div>
              <div class="single-item">
                <span class="label">绩点：</span>
                <span class="value">{{ Number(selectedStudent.gpa || 0).toFixed(2) }}</span>
              </div>
              <div class="single-item">
                <span class="label">消费群体：</span>
                <span class="value">{{ selectedStudent.consumptionGroup || '-' }}</span>
              </div>
              <div class="single-item hint">输入学号后点击“查询”</div>
            </el-card>
          </el-col>
          <el-col :span="16">
            <el-card shadow="never" class="single-card">
              <div class="single-title">个体对比（与群体均值）</div>
              <BaseChart
                :options="singleCompareOptions"
                :loading="loading"
                :container-style="{ height: '320px', width: '100%' }"
              />
            </el-card>
          </el-col>
        </el-row>
      </el-card>
      
      <!-- 分析结果 -->
      <el-card style="margin-top: 20px;">
        <template #header>
          <span>成绩与消费关联性分析结果</span>
        </template>
        <div class="result-meta" v-if="correlationMeta">
          <el-tag effect="plain">有效样本 n={{ correlationMeta.sampleSize || correlationMeta.mergedCount || 0 }}</el-tag>
          <el-tag effect="plain">方法={{ (correlationMeta.method || 'pearson').toUpperCase() }}</el-tag>
          <el-tag effect="plain">多重校正={{ correlationMeta.multipleTest || 'BH-FDR' }}</el-tag>
          <el-tag effect="plain">学期={{ correlationMeta.termUsed || '-' }}</el-tag>
        </div>
        <el-table :data="enhancedCorrelationResults" style="width: 100%">
          <el-table-column prop="rank" label="排序" width="80"></el-table-column>
          <el-table-column prop="factor" label="消费因素" width="150"></el-table-column>
          <el-table-column prop="sampleSize" label="样本量" width="90"></el-table-column>
          <el-table-column prop="correlation" label="相关系数" width="120">
            <template #default="scope">
              <el-tag :type="getCorrelationType(scope.row.correlation)">
                {{ scope.row.correlation.toFixed(3) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ciRange" label="95%CI" width="170">
            <template #default="scope">{{ formatCI(scope.row.ciLower, scope.row.ciUpper) }}</template>
          </el-table-column>
          <el-table-column prop="absCorrelation" label="绝对相关度" width="120">
            <template #default="scope">
              {{ scope.row.absCorrelation.toFixed(3) }}
            </template>
          </el-table-column>
          <el-table-column prop="direction" label="方向" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.direction === '正相关' ? 'success' : scope.row.direction === '负相关' ? 'danger' : 'info'">
                {{ scope.row.direction }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="strength" label="强度" width="100"></el-table-column>
          <el-table-column prop="pValue" label="P值" width="120">
            <template #default="scope">{{ formatPValue(scope.row.pValue) }}</template>
          </el-table-column>
          <el-table-column prop="qValue" label="q值(FDR)" width="130">
            <template #default="scope">{{ formatQValue(scope.row.qValue) }}</template>
          </el-table-column>
          <el-table-column prop="significance" label="显著性(FDR)" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.significance === '显著' ? 'success' : 'info'">
                {{ scope.row.significance }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="interpretation" label="解读"></el-table-column>
        </el-table>
        <el-divider content-position="left">梯度分布（Top5）</el-divider>
        <el-table :data="heatmapTopBins" style="width: 100%">
          <el-table-column prop="rank" label="排名" width="80"></el-table-column>
          <el-table-column prop="consumptionBand" label="消费梯度"></el-table-column>
          <el-table-column prop="gpaBand" label="GPA梯度"></el-table-column>
          <el-table-column prop="count" label="人数" width="120"></el-table-column>
        </el-table>
        <div class="result-note">说明：此处展示“相关性”而非“因果性”，显著性按 BH-FDR 校正后的 q 值判定。</div>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import {getScoreCorrelation} from "@/api/user.js";
import {COLLEGES_MAJORS, generateClassNames} from '@/utils/const_value.js'
import BaseChart from '@/components/Charts/BaseChart.vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'ScoreCorrelation',
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
        studentId: '',
        correlationMethod: 'pearson',
        variable1: 'gpa'
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      loading: false,
      correlationResults: [],
      consumptionScatterData: [],
      scatterPoints: [],
      selectedStudentId: '',
      studentProfile: null,
      correlationMeta: null
    }
  },
  mounted() {
    // 初始化数据
  },
  computed: {
    selectedStudent() {
      if (this.studentProfile) return this.studentProfile
      if (!this.selectedStudentId) return {}
      return this.scatterPoints.find(p => p.studentId === this.selectedStudentId) || {}
    },
    groupAverages() {
      if (this.correlationMeta && (this.correlationMeta.avgDaily || this.correlationMeta.avgGpa)) {
        return {
          consumption: Number(this.correlationMeta.avgDaily || 0),
          gpa: Number(this.correlationMeta.avgGpa || 0)
        }
      }
      if (!this.scatterPoints.length) return { consumption: 0, gpa: 0 }
      const sum = this.scatterPoints.reduce((acc, cur) => {
        acc.consumption += Number(cur.consumption || 0)
        acc.gpa += Number(cur.gpa || 0)
        return acc
      }, { consumption: 0, gpa: 0 })
      const len = this.scatterPoints.length
      return {
        consumption: Number((sum.consumption / len).toFixed(2)),
        gpa: Number((sum.gpa / len).toFixed(2))
      }
    },
    singleCompareOptions() {
      const student = this.selectedStudent
      if (!student.studentId) {
        return {
          title: {
            text: '请输入学号并分析',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      const avg = this.groupAverages
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['当前学生', '群体均值'], top: 10 },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
        xAxis: { type: 'category', data: ['日均消费(元)', '绩点(GPA)'] },
        yAxis: { type: 'value' },
        series: [
          {
            name: '当前学生',
            type: 'bar',
            data: [Number(student.dailyAvg || student.consumption || 0), Number(student.gpa || 0)],
            itemStyle: { color: '#409EFF' }
          },
          {
            name: '群体均值',
            type: 'bar',
            data: [avg.consumption, avg.gpa],
            itemStyle: { color: '#67C23A' }
          }
        ]
      }
    },
    heatmapBins() {
      const points = this.scatterPoints || []
      if (!points.length) return null

      const xBins = 5
      const yBins = 5
      const xs = points.map(p => Number(p.consumption || 0)).filter(v => !Number.isNaN(v))
      const ys = points.map(p => Number(p.gpa || 0)).filter(v => !Number.isNaN(v))
      const minX = Math.min(...xs)
      const maxX = Math.max(...xs)
      const minY = Math.min(...ys)
      const maxY = Math.max(...ys)
      const stepX = (maxX - minX) / xBins || 1
      const stepY = (maxY - minY) / yBins || 0.1

      const xLabels = Array.from({ length: xBins }, (_, i) => {
        const start = minX + i * stepX
        const end = i === xBins - 1 ? maxX : minX + (i + 1) * stepX
        return `${start.toFixed(2)}-${end.toFixed(2)}`
      })
      const yLabels = Array.from({ length: yBins }, (_, i) => {
        const start = minY + i * stepY
        const end = i === yBins - 1 ? maxY : minY + (i + 1) * stepY
        return `${start.toFixed(2)}-${end.toFixed(2)}`
      })

      const grid = Array.from({ length: xBins * yBins }, (_, idx) => {
        const x = idx % xBins
        const y = Math.floor(idx / xBins)
        return [x, y, 0]
      })

      points.forEach(p => {
        const x = Number(p.consumption || 0)
        const y = Number(p.gpa || 0)
        if (Number.isNaN(x) || Number.isNaN(y)) return
        const xi = Math.min(xBins - 1, Math.max(0, Math.floor((x - minX) / stepX)))
        const yi = Math.min(yBins - 1, Math.max(0, Math.floor((y - minY) / stepY)))
        const index = yi * xBins + xi
        grid[index][2] += 1
      })

      return { xLabels, yLabels, grid }
    },
    heatmapTopBins() {
      const bins = this.heatmapBins
      if (!bins) return []
      const { xLabels, yLabels, grid } = bins
      return grid
        .filter(item => item[2] > 0)
        .sort((a, b) => b[2] - a[2])
        .slice(0, 5)
        .map((item, idx) => ({
          rank: idx + 1,
          consumptionBand: xLabels[item[0]],
          gpaBand: yLabels[item[1]],
          count: item[2]
        }))
    },
    heatmapOptions() {
      const bins = this.heatmapBins
      if (!bins) {
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

      const { xLabels, yLabels, grid } = bins
      const data = grid

      return {
        title: {
          text: '消费水平梯度 × GPA 梯度热力图',
          left: 'center',
          top: 0,
          textStyle: { fontSize: 14, fontWeight: 'normal' }
        },
        tooltip: {
          position: 'top',
          formatter: (params) => {
            const x = xLabels[params.data[0]]
            const y = yLabels[params.data[1]]
            const v = Number(params.data[2])
            return `消费梯度: ${x}<br/>GPA 梯度: ${y}<br/>人数: ${v}`
          }
        },
        grid: { height: '65%', top: '14%', left: '8%', right: '6%' },
        xAxis: {
          type: 'category',
          data: xLabels,
          splitArea: { show: true },
          axisLabel: { interval: 0, rotate: 30, color: '#666' },
          axisTick: { show: false },
          axisLine: { lineStyle: { color: '#e4e7ed' } }
        },
        yAxis: {
          type: 'category',
          data: yLabels,
          splitArea: { show: true },
          axisTick: { show: false },
          axisLine: { lineStyle: { color: '#e4e7ed' } },
          axisLabel: { color: '#666' }
        },
        visualMap: {
          min: 0,
          max: Math.max(...data.map(d => d[2])) || 1,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '2%',
          text: ['人数多', '人数少'],
          textStyle: { color: '#666' },
          inRange: {
            color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
          }
        },
        series: [{
          name: '相关性',
          type: 'heatmap',
          data,
          label: { show: true, color: '#333', fontSize: 11, formatter: (p) => p.data[2] },
          itemStyle: { borderColor: '#fff', borderWidth: 1 },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
          }
        }]
      }
    },
    enhancedCorrelationResults() {
      const rows = this.correlationResults || []
      const strength = (v) => {
        const a = Math.abs(v)
        if (a >= 0.7) return '强'
        if (a >= 0.4) return '中'
        if (a >= 0.2) return '弱'
        return '极弱'
      }
      const enriched = rows.map((r) => {
        const corr = Number(r.correlation || 0)
        return {
          ...r,
          sampleSize: Number(r.sampleSize || this.correlationMeta?.sampleSize || this.correlationMeta?.mergedCount || 0),
          ciLower: r.ciLower ?? null,
          ciUpper: r.ciUpper ?? null,
          qValue: Number(r.qValue ?? 1),
          absCorrelation: Math.abs(corr),
          direction: corr > 0 ? '正相关' : corr < 0 ? '负相关' : '无相关',
          strength: strength(corr)
        }
      })
      return enriched
        .sort((a, b) => b.absCorrelation - a.absCorrelation)
        .map((r, idx) => ({ ...r, rank: idx + 1 }))
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
    async handleAnalyze() {
      this.loading = true
      try {
        // 构建查询参数
        const params = {
          ...this.queryForm,
          className: this.queryForm.class || undefined,
          grade: this.queryForm.grade || undefined,
          correlationMethod: (this.queryForm.correlationMethod || 'pearson').toLowerCase()
        }

        if (params.studentId) {
          params.studentId = String(params.studentId).trim()
        }
        
        // 移除空值
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null || params[key] === undefined) {
            delete params[key]
          }
        })
        
        const result = await getScoreCorrelation(params)

        // 处理返回数据（后端直接返回对象，不使用 result.data 包裹）
        const hasRoot = result && (result.scatterData || result.correlationResults || result.results)
        const data = hasRoot ? result : (result && result.data ? result.data : result)

        if (data) {
          if (data.meta) {
            console.info('相关性诊断:', data.meta)
          }
          this.correlationMeta = data.meta || null
          if (data.message) {
            const msg = data.meta?.termUsed ? `${data.message}（使用学期：${data.meta.termUsed}）` : data.message
            const detail = data.meta?.fallback ? `${msg}，说明：${data.meta.fallback}` : msg
            ElMessage.warning(detail)
          }
          
          // 单体画像
          this.studentProfile = data.studentProfile || null
          if (this.queryForm.studentId) {
            this.selectedStudentId = this.queryForm.studentId
          }

          // 保留散点数据用于热力图分箱
          if (data.scatterData && Array.isArray(data.scatterData)) {
            this.scatterPoints = data.scatterData.map(item => ({
              studentId: item.studentId || item.student_id || '',
              consumption: Number(item.consumption ?? item.x ?? 0),
              gpa: Number(item.gpa ?? item.y ?? 0)
            }))
          } else if (data.points && Array.isArray(data.points)) {
            this.scatterPoints = data.points.map(item => ({
              studentId: item.studentId || item.student_id || '',
              consumption: Number(item.consumption ?? item.x ?? 0),
              gpa: Number(item.gpa ?? item.y ?? 0)
            }))
          } else {
            this.scatterPoints = []
          }

          if (this.studentProfile && !this.studentProfile.consumptionGroup) {
            const daily = Number(this.studentProfile.dailyAvg || 0)
            this.studentProfile.consumptionGroup = this.computeConsumptionGroup(daily)
          }
          
          // 处理关联分析结果
          if (data.correlationResults && Array.isArray(data.correlationResults)) {
            this.correlationResults = data.correlationResults
          } else if (data.results && Array.isArray(data.results)) {
            this.correlationResults = data.results
          } else {
            this.correlationResults = []
          }

          if (!this.correlationResults.length) {
            ElMessage.info('暂无可分析数据，请调整筛选条件')
          }
        } else {
          this.consumptionScatterData = []
          this.correlationResults = []
          this.scatterPoints = []
          this.selectedStudentId = ''
          this.studentProfile = null
          this.correlationMeta = null
        }
      } catch (error) {
        console.error('关联分析失败:', error)
        ElMessage.error('关联分析失败: ' + (error.message || '未知错误'))
          this.consumptionScatterData = []
          this.correlationResults = []
          this.scatterPoints = []
          this.selectedStudentId = ''
          this.studentProfile = null
          this.correlationMeta = null
      } finally {
        this.loading = false
      }
    },
    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        studentId: '',
        correlationMethod: 'pearson',
        variable1: 'gpa'
      }
      this.majors = []
      this.classes = []
      this.correlationResults = []
      this.consumptionScatterData = []
      this.scatterPoints = []
      this.selectedStudentId = ''
      this.studentProfile = null
      this.correlationMeta = null
    },
    getCorrelationType(correlation) {
      if (Math.abs(correlation) > 0.5) return 'danger';
      if (Math.abs(correlation) > 0.3) return 'warning';
      if (Math.abs(correlation) > 0.1) return 'success';
      return 'info';
    },
    formatPValue(pValue) {
      const value = Number(pValue)
      if (Number.isNaN(value)) return '-'
      if (value === 0) return '0'
      if (value < 1e-4) return value.toExponential(2)
      return value.toFixed(4)
    },
    formatQValue(qValue) {
      const value = Number(qValue)
      if (Number.isNaN(value)) return '-'
      if (value === 0) return '0'
      if (value < 1e-4) return value.toExponential(2)
      return value.toFixed(4)
    },
    formatCI(ciLower, ciUpper) {
      const low = Number(ciLower)
      const high = Number(ciUpper)
      if (Number.isNaN(low) || Number.isNaN(high)) return '-'
      return `[${low.toFixed(3)}, ${high.toFixed(3)}]`
    },
    computeConsumptionGroup(dailyAvg) {
      const points = this.scatterPoints || []
      const values = points.map(p => Number(p.consumption || 0)).filter(v => !Number.isNaN(v))
      if (!values.length) return '未知'
      const sorted = values.sort((a, b) => a - b)
      const q = (p) => {
        const idx = Math.floor(p * (sorted.length - 1))
        return sorted[idx]
      }
      const q20 = q(0.2)
      const q50 = q(0.5)
      const q80 = q(0.8)
      if (dailyAvg <= q20) return '贫困生'
      if (dailyAvg <= q50) return '低消费'
      if (dailyAvg <= q80) return '中等消费'
      return '高消费'
    },
    handleScatterChartClick(params) {}
  //    initHeatmap() {
  //     const chart = echarts.init(document.getElementById('correlationHeatmap'));
  //     const option = {
  //       tooltip: {
  //         position: 'top'
  //       },
  //       grid: {
  //         height: '80%',
  //         top: '10%'
  //       },
  //       xAxis: {
  //         type: 'category',
  //         data: ['早餐', '午餐', '晚餐', '超市', '图书馆', '其他'],
  //         splitArea: { show: true }
  //       },
  //       yAxis: {
  //         type: 'category',
  //         data: ['数学', '英语', '专业课', '体育', '总绩点'],
  //         splitArea: { show: true }
  //       },
  //       visualMap: {
  //         min: -1,
  //         max: 1,
  //         calculable: true,
  //         orient: 'horizontal',
  //         left: 'center',
  //         bottom: '0%',
  //         inRange: {
  //           color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
  //         }
  //       },
  //       series: [{
  //         name: '相关性',
  //         type: 'heatmap',
  //         data: this.generateHeatmapData(),
  //         label: { show: true },
  //         emphasis: {
  //           itemStyle: {
  //             shadowBlur: 10,
  //             shadowColor: 'rgba(0, 0, 0, 0.5)'
  //           }
  //         }
  //       }]
  //     };
  //     chart.setOption(option);
  //   },
  //   generateHeatmapData() {
  //     const data = [];
  //     const xData = ['早餐', '午餐', '晚餐', '超市', '图书馆', '其他'];
  //     const yData = ['数学', '英语', '专业课', '体育', '总绩点'];
  //     console.log('生成热力图')
  //     yData.forEach((y, yIndex) => {
  //       xData.forEach((x, xIndex) => {
  //         // 模拟相关性数据
  //         let value;
  //         if (x === '早餐' && y === '总绩点') value = 0.31;
  //         else if (x === '图书馆' && y === '总绩点') value = 0.45;
  //         else if (x === '午餐' && y === '数学') value = 0.22;
  //         else if (x === '超市' && y === '体育') value = -0.15;
  //         else value = (Math.random() * 0.6 - 0.3).toFixed(2);
  //
  //         data.push([xIndex, yIndex, parseFloat(value)]);
  //       });
  //     });
  //     return data;
  //   }
  }
}
</script>

<style scoped>
.score-correlation {
  padding: 20px;
}

.single-card {
  background: #fafcff;
  border: 1px solid #eef2f7;
}

.single-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.single-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  color: #606266;
}

.single-item .label {
  color: #909399;
}

.single-item.hint {
  margin-top: 6px;
  font-size: 12px;
  color: #a0a4aa;
}

.single-input-row {
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.result-note {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
