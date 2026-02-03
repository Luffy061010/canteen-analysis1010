<script setup>
import {ref, onMounted, watch, nextTick} from 'vue'
import * as echarts from 'echarts'
import { getStudentInfo } from '@/api/user.js'
import { getStudentScores } from '@/api/user.js'
import { exportStudents } from '@/api/user.js'
import { ElMessage } from 'element-plus'
import {COLLEGES_MAJORS, generateClassNames} from '@/utils/const_value.js'
import { downloadBlob, exportCsv } from '@/utils/download'

const queryForm = ref({
  college: '',
  major: '',
  grade: '',
  class: '',
  studentId: '',
  name: '',
  phone: ''
})
// 监听学院变化
watch(queryForm, (new_val) => {
  if(new_val.college != null && new_val.college !== '') {
    console.log('new_val', new_val)
    majors.value = COLLEGES_MAJORS[new_val.college]?.['majors'] || []
  }
}, { deep: true })

const colleges = ref([])
const majors = ref([])
const classes = ref([])
const studentList = ref([])
const loading = ref(false)
const gpaChart = ref(null)
const scoreData = ref({})
const loadingScores = ref(false)
const pagination = ref({
  currentPage: 1,
  // 默认每页 20 条，可由前端分页
  pageSize: 20,
  total: 0
})

function fill_colleges() {
  Object.keys(COLLEGES_MAJORS).forEach(key => {
    colleges.value.push(key)
  })
}

onMounted(() => {
  fill_colleges()
  loadStudents()
})
// 成绩详情相关
const scoreDialogVisible = ref(false)
const selectedStudent = ref({})
const selectedSemester = ref('2023-2024-1')
const scoreRecords = ref([])
const semesters = ref([
  { value: '2023-2024-1', label: '2023-2024学年第一学期' },
  { value: '2022-2023-2', label: '2022-2023学年第二学期' },
  { value: '2022-2023-1', label: '2022-2023学年第一学期' }
])
const currentGPA = ref(3.6)
const handleSemesterChange = () => {
  updateScoreView()
}

watch(selectedSemester, () => {
  updateScoreView()
})
// 数据联动
const handleCollegeChange = (collegeId) => {
  if (collegeId) {
    majors.value = COLLEGES_MAJORS[collegeId]?.['majors'] || []
  } else {
    majors.value = []
    classes.value = []
  }
  queryForm.value.major = ''
  queryForm.value.class = ''
}
const handleMajorChange = (majorId) => {
  if (majorId && queryForm.value.grade) {
    classes.value = generateClassNames(majorId, queryForm.value.grade + '级')
  } else {
    classes.value = []
  }
  queryForm.value.class = ''
}

// 监听年级变化，更新班级选项
watch(() => queryForm.value.grade, (newGrade) => {
  if (newGrade && queryForm.value.major) {
    classes.value = generateClassNames(queryForm.value.major, newGrade + '级')
  } else {
    classes.value = []
  }
  queryForm.value.class = ''
})
// 查询学生数据
// const handleQuery = async () => {
//   loading.value = true
//   try {
//     const result = await getStudentInfo(queryForm.value)
//     console.log('API返回数据:', result)
//     const allData = result.data || result || []
//     if (allData.length > 0 && allData[0].student_id) {
//       studentList.value = allData.map(item => ({
//         studentId: item.student_id,
//         name: item.name,
//         gender: item.gender_display,
//         college: item.college,
//         major: item.major,
//         className: item.class_name,
//         phone: item.phone_number
//       }))}
//       else {
//         studentList.value = records.data
//     }
const buildQueryParams = () => {
  const params = {
    college: queryForm.value.college?.trim() || undefined,
    major: queryForm.value.major?.trim() || undefined,
    grade: queryForm.value.grade?.trim() || undefined,
    className: queryForm.value.class?.trim() || undefined,
    studentId: queryForm.value.studentId?.trim() || undefined,
    name: queryForm.value.name?.trim() || undefined,
    phone: queryForm.value.phone?.trim() || undefined,
    page: pagination.value.currentPage,
    pageSize: pagination.value.pageSize || 20
  }
  Object.keys(params).forEach(k => {
    if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
  })
  return params
}

const loadStudents = async () => {
  loading.value = true
  try {
    const result = await getStudentInfo(buildQueryParams())
    console.log('[student] params', buildQueryParams(), 'resp', result)

    let records = []
    if (Array.isArray(result?.records)) {
      records = result.records
      pagination.value.total = result.total || result.totalCount || records.length
      pagination.value.pageSize = result.pageSize || pagination.value.pageSize
      pagination.value.currentPage = result.page || pagination.value.currentPage
    } else if (result?.data?.records) {
      records = result.data.records
      pagination.value.total = result.data.total || result.data.totalCount || records.length
      pagination.value.pageSize = result.data.pageSize || pagination.value.pageSize
      pagination.value.currentPage = result.data.page || pagination.value.currentPage
    } else if (Array.isArray(result?.data)) {
      records = result.data
      pagination.value.total = records.length
    } else if (Array.isArray(result)) {
      records = result
      pagination.value.total = records.length
    } else {
      records = []
      pagination.value.total = 0
    }

    const normalizeGender = (val) => {
      if (val === 'M') return '男'
      if (val === 'F') return '女'
      return val || ''
    }

    studentList.value = records.map(item => {
      const genderRaw = item.gender_display || item.gender
      return {
        studentId: item.student_id || item.studentId || item.student_id,
        name: item.name || item.student_name,
        gender: normalizeGender(genderRaw),
        college: item.college || item.college_name,
        major: item.major || item.major_name,
        className: item.class_name || item.className || item.class,
        grade: item.grade || '',
        phone: item.phoneNumber || item.phone_number || item.phone || item.telephone || item.contact_phone || ''
      }
    })

    if (!studentList.value.length) {
      ElMessage.warning('未查询到学生数据，请检查筛选条件')
    }
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败，请稍后重试')
    studentList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

const handleQuery = async () => {
  pagination.value.currentPage = 1
  await loadStudents()
}


    // } else {
    //   studentList.value = response.data.records;
    // }
//     pagination.value.total = studentList.value.length
//     pagination.value.currentPage = 1
//   } catch (error) {
//     console.error('查询失败', error)
//     studentList.value = [
//       {
//         studentId: '2021001001',
//         name: '张三',
//         gender: '男',
//         college: '计算机学院',
//         major: '软件工程',
//         className: '软工2101',
//         phone: '13800138000',
//       }
//     ]
//     pagination.value.total = studentList.value.length
//     pagination.value.currentPage = 1
//   } finally {
//     loading.value = false
//   }
// }
const handleReset = () => {
  queryForm.value = {
    college: '',
    major: '',
    grade: '',
    class: '',
    studentId: '',
    name: '',
    phone: ''
  }
  majors.value = []
  classes.value = []
  pagination.value.currentPage = 1
  loadStudents()
}

const fetchAllStudentsForExport = async () => {
  const baseParams = buildQueryParams()
  const pageSize = 500
  const maxPages = 100
  let page = 1
  let all = []
  let total = null

  while (page <= maxPages) {
    const params = { ...baseParams, page, pageSize }
    const result = await getStudentInfo(params)
    let records = []
    if (Array.isArray(result?.records)) {
      records = result.records
      total = result.total || result.totalCount || total
    } else if (result?.data?.records) {
      records = result.data.records
      total = result.data.total || result.data.totalCount || total
    } else if (Array.isArray(result?.data)) {
      records = result.data
    } else if (Array.isArray(result)) {
      records = result
    }

    if (Array.isArray(records)) all = all.concat(records)
    if (!records || records.length < pageSize) break
    if (total && all.length >= total) break
    page += 1
  }

  const normalizeGender = (val) => {
    if (val === 'M') return '男'
    if (val === 'F') return '女'
    return val || ''
  }

  return all.map(item => {
    const genderRaw = item.gender_display || item.gender
    return {
      studentId: item.student_id || item.studentId || item.student_id,
      name: item.name || item.student_name,
      gender: normalizeGender(genderRaw),
      college: item.college || item.college_name,
      major: item.major || item.major_name,
      className: item.class_name || item.className || item.class,
      grade: item.grade || '',
      phone: item.phoneNumber || item.phone_number || item.phone || item.telephone || item.contact_phone || ''
    }
  })
}

const handleExport = async () => {
  try {
    const params = buildQueryParams()
    delete params.page
    delete params.pageSize
    const blob = await exportStudents(params)
    if (blob instanceof Blob) {
      downloadBlob(blob, `students_${Date.now()}.csv`, 'text/csv')
      ElMessage.success('学生数据导出成功')
      return
    }
  } catch (error) {
    console.warn('后端导出失败，尝试前端导出', error)
  }

  try {
    loading.value = true
    const rows = await fetchAllStudentsForExport()
    if (!rows.length) {
      ElMessage.warning('无可导出数据')
      return
    }
    exportCsv(
      rows,
      [
        { label: '学号', key: 'studentId' },
        { label: '姓名', key: 'name' },
        { label: '性别', key: 'gender' },
        { label: '学院', key: 'college' },
        { label: '专业', key: 'major' },
        { label: '班级', key: 'className' },
        { label: '年级', key: 'grade' },
        { label: '联系电话', key: 'phone' }
      ],
      `students_${Date.now()}.csv`
    )
    ElMessage.success('学生数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('学生数据导出失败')
  } finally {
    loading.value = false
  }
}

// 分页控制
const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  loadStudents()
}

const handleCurrentChange = (page) => {
  pagination.value.currentPage = page
  loadStudents()
}

const showScoreDetail = async (student) => {
  selectedStudent.value = student
  scoreDialogVisible.value = true
  loadingScores.value = true
  try {
    // 根据后端API文档，studentId 是必需参数
    const result = await getStudentScores({
      studentId: student.studentId
    })

    const records = Array.isArray(result?.data) ? result.data : Array.isArray(result) ? result : []
    scoreRecords.value = records

    if (records.length > 0) {
      semesters.value = records
        .map(r => ({ value: r.term, label: getSemesterDisplay(r.term) }))
        .filter(r => r.value)
      if (!semesters.value.length) {
        semesters.value = [{ value: selectedSemester.value, label: getSemesterDisplay(selectedSemester.value) }]
      }
      if (!records.find(r => r.term === selectedSemester.value)) {
        selectedSemester.value = records[0].term
      }
      updateScoreView()
    } else {
      currentGPA.value = 0
      scoreData.value = getDefaultScoreData()
      nextTick(() => {
        initGPAChart([], [], '')
      })
    }
  } catch (error) {
    console.error('获取成绩失败', error)
    ElMessage.error('获取成绩信息失败: ' + (error.message || '未知错误'))

    // 错误处理时也保持数据一致性
    currentGPA.value = 0
    scoreData.value = getDefaultScoreData()
    nextTick(() => {
      initGPAChart([], [], '')
    })
  } finally {
    loadingScores.value = false
  }
}

const updateScoreView = () => {
  if (!scoreRecords.value.length) return
  const records = scoreRecords.value
  const match = records.find(r => r.term === selectedSemester.value) || records[0]
  currentGPA.value = parseFloat(match.gpa || 0)

  const sorted = records.slice().sort((a, b) => (a.term || '').localeCompare(b.term || ''))
  const labels = sorted.map(r => getSemesterDisplay(r.term || ''))
  const trend = sorted.map(r => parseFloat(r.gpa || 0))

  scoreData.value = {
    student: selectedStudent.value.name,
    term: match.term || selectedSemester.value,
    term_display: getSemesterDisplay(match.term || selectedSemester.value),
    gpa: currentGPA.value,
    gpaTrend: trend
  }

  nextTick(() => {
    initGPAChart(trend, labels, match.term || selectedSemester.value)
  })
}

// 简化转换函数，直接使用后端数据
const transformBackendData = (backendData) => {
  if (!backendData) {
    return getDefaultScoreData()
  }

  return {
    student: selectedStudent.value.name,
    term: selectedSemester.value,
    term_display: backendData.term_display || getSemesterDisplay(selectedSemester.value),
    gpa: parseFloat(backendData.gpa) || 0,
    gpaTrend: []  // 单次请求无法获取历史GPA趋势
  }
}

// 保留图表初始化函数，但处理空数据情况
const initGPAChart = (gpaTrend, labels = [], activeTerm = '') => {
  if (!gpaChart.value) return

  const chart = echarts.init(gpaChart.value)

  // 处理空数据情况
  if (!gpaTrend || gpaTrend.length === 0) {
    const option = {
      title: {
        text: '暂无历史GPA数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14,
          fontWeight: 'normal'
        }
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: []
    }
    chart.setOption(option)
    return
  }

  const semesterLabels = labels.length ? labels : generateSemesterLabels(gpaTrend.length)
  const activeIndex = activeTerm ? semesterLabels.findIndex(l => l === getSemesterDisplay(activeTerm)) : -1
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = params[0]
        return `第${data.dataIndex + 1}学期: GPA ${data.value}`
      }
    },
    xAxis: {
      type: 'category',
      data: semesterLabels
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 4.0,
      interval: 0.5
    },
    series: [{
      data: gpaTrend,
      type: 'line',
      smooth: true,
      lineStyle: { color: '#409EFF', width: 3 },
      itemStyle: { color: '#409EFF' },
      markPoint: activeIndex >= 0 ? {
        symbolSize: 12,
        data: [{
          coord: [semesterLabels[activeIndex], gpaTrend[activeIndex]],
          itemStyle: { color: '#f56c6c' }
        }]
      } : undefined,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ]
        }
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    }
  }

  chart.setOption(option)
}

// 以下函数保持不变（因为逻辑简单且通用）
const generateSemesterLabels = (count) => {
  return Array.from({length: count}, (_, i) => `第${i + 1}学期`)
}

const getDefaultScoreData = () => {
  return {
    student: selectedStudent.value.name,
    term: selectedSemester.value,
    term_display: getSemesterDisplay(selectedSemester.value),
    gpa: 0,
    gpaTrend: []
  }
}

// 学期显示名称
const getSemesterDisplay = (semester) => {
  const semesterMap = {
    '2023-2024-1': '2023-2024学年第一学期',
    '2022-2023-2': '2022-2023学年第二学期',
    '2022-2023-1': '2022-2023学年第一学期'
  }
  return semesterMap[semester] || semester
}
</script>

<template>
  <!-- 页面：学生基础信息与成绩详情 -->
  <div class="student-info">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>学生基本信息查询</h2>
    </div>

    <!-- 查询表单 -->
    <div class="query-card">
      <el-form :model="queryForm" inline>
        <el-form-item label="学院" class="form-item">
          <el-select v-model="queryForm.college" placeholder="请选择学院" clearable @change="handleCollegeChange">
            <el-option v-for="college in colleges" :key="college" :label="college" :value="college"/>
            <el-option label="全部" value="" />
          </el-select>
        </el-form-item>

        <el-form-item label="专业" class="form-item">
          <el-select v-model="queryForm.major" placeholder="请选择专业" clearable @change="handleMajorChange">
            <el-option v-for="major in majors" :key="major" :label="major" :value="major"/>
            <el-option label="全部" value="" />
          </el-select>
        </el-form-item>

        <el-form-item label="年级" class="form-item">
          <el-select v-model="queryForm.grade" placeholder="请选择年级" clearable>
            <el-option label="全部" value="" />
            <el-option label="2021级" value="2021" />
            <el-option label="2022级" value="2022" />
            <el-option label="2023级" value="2023" />
            <el-option label="2024级" value="2024" />
          </el-select>
        </el-form-item>

        <el-form-item label="班级" class="form-item">
          <el-select v-model="queryForm.class" placeholder="请选择班级" clearable>
            <el-option label="全部" value="" />
            <el-option v-for="classItem in classes" :key="classItem" :label="classItem" :value="classItem"/>
          </el-select>
        </el-form-item>

            <el-form-item label="姓名" class="form-item">
              <el-input v-model="queryForm.name" placeholder="请输入姓名" clearable />
            </el-form-item>

            <el-form-item label="电话" class="form-item">
              <el-input v-model="queryForm.phone" placeholder="请输入电话" clearable />
            </el-form-item>

        <el-form-item label="学号" class="form-item">
          <el-input v-model="queryForm.studentId" placeholder="请输入学号" clearable />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 学生表格 -->
    <div class="table-card">
      <el-table :data="studentList" v-loading="loading">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="80">
          <template #default="{ row }">
            <el-tag :type="row.gender === '男' ? 'primary' : 'danger'">{{ row.gender }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="college" label="学院" />
        <el-table-column prop="major" label="专业" />
        <el-table-column prop="className" label="班级" width="100" />
        <el-table-column prop="phone" label="联系电话" width="120">
          <template #default="{ row }">
            {{ row.phone || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showScoreDetail(row)">成绩详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 成绩详情对话框 -->
    <el-dialog v-model="scoreDialogVisible" :title="`学生成绩详情 - ${selectedStudent.name} (${selectedStudent.studentId})`" width="500px">
      <div class="score-dialog">
        <div class="semester-selector">
          <el-select v-model="selectedSemester" placeholder="请选择学期" @change="handleSemesterChange">
            <el-option v-for="semester in semesters" :key="semester.value" :label="semester.label" :value="semester.value"/>
          </el-select>
          <div class="semester-hint">
            学期显示为后端返回的 term 值；“1/2”分别表示第1学期/第2学期。
          </div>
        </div>

        <div class="gpa-info">
          <div class="gpa-card">
            <div class="gpa-value">{{ currentGPA.toFixed(2) }}</div>
            <div class="gpa-label">学期绩点</div>
            <div class="gpa-term">{{ getSemesterDisplay(selectedSemester) }}</div>
          </div>
          <div class="gpa-trend">
            <div ref="gpaChart" style="height: 200px;"></div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header { margin-bottom: 20px; }

.query-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-item {
  margin-right: 20px;
  margin-bottom: 10px;
  width: 180px;
}

.table-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pagination { margin-top: 20px; text-align: right; }

.score-dialog { padding: 10px 0; }

.semester-selector { margin-bottom: 20px; }
.semester-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.gpa-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.gpa-card {
  text-align: center;
  padding: 20px;
  background: #f0f7ff;
  border-radius: 8px;
  min-width: 120px;
}

.gpa-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.gpa-label { font-size: 14px; color: #909399; }

.gpa-term {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.gpa-trend { flex: 1; height: 200px; }
</style>