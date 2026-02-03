<template>
  <!-- 页面：学生成绩查询与趋势展示 -->
  <div class="student-scores">
    <!-- 学生基本信息 -->
    <div class="student-info">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="学号">{{ studentId }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ studentName }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 学期选择 -->
    <div class="semester-selector">
      <el-form :model="scoreForm" inline>
        <el-form-item label="选择学期">
          <el-select v-model="scoreForm.semester" placeholder="请选择学期" @change="handleSemesterChange">
            <el-option 
              v-for="semester in semesters" 
              :key="semester.value" 
              :label="semester.label" 
              :value="semester.value" 
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 绩点信息 -->
    <div class="gpa-card">
      <div class="gpa-header">
        <h3>绩点信息</h3>
        <div class="gpa-value">
          <span class="gpa-number">{{ currentGPA }}</span>
          <span class="gpa-label">当前绩点</span>
        </div>
      </div>
      <div class="gpa-chart">
        <div ref="gpaChart" style="height: 220px;"></div>
      </div>
    </div>

    <!-- 绩点列表 -->
    <div class="scores-table">
      <el-table :data="gpaEntries" v-loading="loading">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="term" label="学期" width="120" />
        <el-table-column prop="gpa" label="绩点" width="100">
          <template #default="{ row }">
            <el-tag :type="row.gpa >= 3.5 ? 'success' : (row.gpa >= 3 ? 'primary' : (row.gpa >= 2 ? 'warning' : 'danger'))">
              {{ row.gpa.toFixed(2) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409EFF;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ termsCount }}</div>
              <div class="stat-label">学期数量</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67C23A;">
              <el-icon><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ bestGPA }}</div>
              <div class="stat-label">最高绩点</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: #E6A23C;">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ avgGPA }}</div>
              <div class="stat-label">平均绩点</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: #F56C6C;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ lowestGPA }}</div>
              <div class="stat-label">最低绩点</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import {getStudentScores}from '@/api/user.js'
import * as echarts from 'echarts'
import { 
  Document, 
  SuccessFilled, 
  TrendCharts, 
  Warning 
} from '@element-plus/icons-vue'

const props = defineProps({
  studentId: {
    type: String,
    required: true
  },
  studentName: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const scoreForm = ref({
  semester: 'all'
})

const semesters = ref([
  { value: 'all', label: '全部学期' },
  { value: '2024-1', label: '2024学年第一学期' },
  { value: '2023-2', label: '2023学年第二学期' },
  { value: '2023-1', label: '2023学年第一学期' },
  { value: '2022-2', label: '2022学年第二学期' }
])

const courseScores = ref([])
const loading = ref(false)
const gpaChart = ref(null)
const allGPA = ref([])

const filteredScores = computed(() => {
  if (scoreForm.value.semester === 'all') return allGPA.value
  return allGPA.value.filter(item => item.term === scoreForm.value.semester)
})

const currentGPA = computed(() => {
  if (!filteredScores.value.length) return '0.00'
  const avg = filteredScores.value.reduce((sum, item) => sum + item.gpa, 0) / filteredScores.value.length
  return avg.toFixed(2)
})

const termsCount = computed(() => allGPA.value.length)
const bestGPA = computed(() => allGPA.value.length ? Math.max(...allGPA.value.map(i => i.gpa)).toFixed(2) : '0.00')
const lowestGPA = computed(() => allGPA.value.length ? Math.min(...allGPA.value.map(i => i.gpa)).toFixed(2) : '0.00')
const avgGPA = computed(() => {
  if (!allGPA.value.length) return '0.00'
  return (allGPA.value.reduce((s,i)=>s+i.gpa,0)/allGPA.value.length).toFixed(2)
})

const gpaEntries = computed(() => filteredScores.value)

const handleSemesterChange = () => {
  courseScores.value = filteredScores.value
  updateGPAChart()
}

const updateGPAChart = () => {
  if (!gpaChart.value) return

  const chart = echarts.init(gpaChart.value)
  const semesterData = filteredScores.value

  chart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: {c}' },
    xAxis: {
      type: 'category',
      data: semesterData.map(s => s.term),
      axisLabel: { rotate: 30 }
    },
    yAxis: { type: 'value', min: 0, max: 4.0, name: 'GPA' },
    series: [{
      data: semesterData.map(s => s.gpa),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#409EFF', width: 3 },
      itemStyle: { color: '#409EFF' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(64, 158, 255, 0.3)' }, { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }]
        }
      }
    }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
  })
}

const loadScores = async () => {
  loading.value = true
  try {
    const res = await getStudentScores({ studentId: props.studentId })
    const data = Array.isArray(res?.data) ? res.data : Array.isArray(res) ? res : []
    allGPA.value = data.map(item => ({
      term: item.term || item.semester || '',
      gpa: Number(item.gpa || item.GPA || item.score || 0)
    })).filter(i => i.term)
    courseScores.value = filteredScores.value
    updateGPAChart()
  } catch (e) {
    console.error('加载成绩失败', e)
    allGPA.value = []
    courseScores.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadScores()
})

watch(() => props.studentId, (newVal) => {
  if (newVal) {
    loadScores()
  }
})
</script>

<style scoped>
.student-scores {
  padding: 0;
}

.student-info {
  margin-bottom: 20px;
}

.semester-selector {
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.gpa-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.gpa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.gpa-header h3 {
  margin: 0;
  color: #303133;
}

.gpa-value {
  text-align: center;
}

.gpa-number {
  display: block;
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.gpa-label {
  font-size: 14px;
  color: #909399;
}

.gpa-chart {
  height: 200px;
}

.scores-table {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: 100%;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: white;
  font-size: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #303133;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.el-table {
  margin-top: 15px;
}
</style>
