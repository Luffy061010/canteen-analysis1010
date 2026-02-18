<template>
  <!-- 页面：系统日志查询与统计 -->
  <div class="log-query">
    <div class="page-header">
      <h2 class="page-title">系统日志查询</h2>
      <p class="page-subtitle">查询和分析系统操作日志</p>
    </div>

    <!-- 日志查询表单 -->
    <div class="query-card">
      <el-form :model="queryForm" ref="queryFormRef" inline>
        <el-form-item label="操作类型" prop="operationType" class="form-item">
          <el-select
              v-model="queryForm.operationType"
              placeholder="全部类型"
              clearable
              style="width: 150px;"
          >
            <el-option label="全部类型" value="" />
            <el-option label="登录" value="login" />
            <el-option label="查询" value="query" />
            <el-option label="新增" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="导出" value="export" />
          </el-select>
        </el-form-item>

        <el-form-item label="操作人员" prop="operator" class="form-item">
          <el-input
              v-model="queryForm.operator"
              placeholder="请输入操作人员"
              clearable
              style="width: 150px;"
          />
        </el-form-item>

        <el-form-item label="操作模块" prop="module" class="form-item">
          <el-select
              v-model="queryForm.module"
              placeholder="全部模块"
              clearable
              style="width: 150px;"
          >
            <el-option label="全部模块" value="" />
            <el-option label="学生信息管理" value="student_info" />
            <el-option label="消费信息查询" value="consumption_query" />
            <el-option label="贫困生鉴别" value="poverty_identification" />
            <el-option label="成绩关联分析" value="score_correlation" />
            <el-option label="系统管理" value="system_management" />
          </el-select>
        </el-form-item>

        <el-form-item label="操作结果" prop="result" class="form-item">
          <el-select
              v-model="queryForm.result"
              placeholder="全部结果"
              clearable
              style="width: 120px;"
          >
            <el-option label="全部结果" value="" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>

        <el-form-item label="IP地址" prop="ipAddress" class="form-item">
          <el-input
              v-model="queryForm.ipAddress"
              placeholder="请输入IP地址"
              clearable
              style="width: 150px;"
          />
        </el-form-item>

        <el-form-item label="时间范围" prop="timeRange" class="form-item">
          <el-date-picker
              v-model="queryForm.timeRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 240px;"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="success" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出日志
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计信息 -->
    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-icon">
          <el-icon><List /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.totalLogs }}</div>
          <div class="stat-label">总日志数</div>
        </div>
      </div>

      <div class="stat-card success">
        <div class="stat-icon">
          <el-icon><SuccessFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.successLogs }}</div>
          <div class="stat-label">成功操作</div>
        </div>
      </div>

      <div class="stat-card warning">
        <div class="stat-icon">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.failureLogs }}</div>
          <div class="stat-label">失败操作</div>
        </div>
      </div>

      <div class="stat-card danger">
        <div class="stat-icon">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.uniqueUsers }}</div>
          <div class="stat-label">操作用户数</div>
        </div>
      </div>
    </div>

    <!-- 日志表格 -->
    <div class="table-card">
      <el-table
          :data="logList"
          v-loading="loading"
          style="width: 100%"
          @sort-change="handleSortChange"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="operationTime" label="操作时间" width="160" sortable="custom">
          <template #default="{ row }">
            <div class="time-cell">
              <div class="date">{{ formatDate(row.operationTime) }}</div>
              <div class="time">{{ formatTime(row.operationTime) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人员" width="120" />
        <el-table-column prop="operationType" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getOperationTypeColor(row.operationType)" size="small">
              {{ getOperationTypeText(row.operationType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="操作模块" width="140">
          <template #default="{ row }">
            <span class="module-name">{{ getModuleText(row.module) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="operationDetail" label="操作详情" min-width="200">
          <template #default="{ row }">
            <div class="detail-cell">
              <span class="detail-text">{{ row.operationDetail }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ipAddress" label="IP地址" width="130" />
        <el-table-column prop="result" label="操作结果" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
              {{ row.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executionTime" label="执行时间" width="100" align="right">
          <template #default="{ row }">
            <span v-if="row.executionTime">{{ row.executionTime }}ms</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
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

    <!-- 日志详情对话框 -->
    <el-dialog
        v-model="detailDialogVisible"
        :title="`日志详情 - ${selectedLog ? selectedLog.operationDetail : ''}`"
        width="600px"
    >
      <div class="log-detail" v-if="selectedLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="操作时间">
            {{ formatFullTime(selectedLog.operationTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="操作人员">
            {{ selectedLog.operator }}
          </el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getOperationTypeColor(selectedLog.operationType)">
              {{ getOperationTypeText(selectedLog.operationType) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作模块">
            {{ getModuleText(selectedLog.module) }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedLog.ipAddress }}
          </el-descriptions-item>
          <el-descriptions-item label="操作结果">
            <el-tag :type="selectedLog.result === 'success' ? 'success' : 'danger'">
              {{ selectedLog.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间" :span="2">
            {{ selectedLog.executionTime ? selectedLog.executionTime + 'ms' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作详情" :span="2">
            <div class="detail-content">
              {{ selectedLog.operationDetail }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="请求参数" :span="2" v-if="selectedLog.requestParams">
            <div class="request-params">
              <pre>{{ JSON.stringify(selectedLog.requestParams, null, 2) }}</pre>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="响应结果" :span="2" v-if="selectedLog.responseResult">
            <div class="response-result">
              <pre>{{ JSON.stringify(selectedLog.responseResult, null, 2) }}</pre>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, View, List, SuccessFilled, Warning, User } from '@element-plus/icons-vue'
import { getSystemLogs, getSystemLogStats } from '@/api/user.js'
import { exportXlsx } from '@/utils/download'

// 查询表单数据
const queryForm = reactive({
  operationType: '',
  operator: '',
  module: '',
  result: '',
  ipAddress: '',
  timeRange: []
})

const queryFormRef = ref(null)
const logList = ref([])
const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedLog = ref(null)

const statistics = reactive({
  totalLogs: 0,
  successLogs: 0,
  failureLogs: 0,
  uniqueUsers: 0
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

const sortParams = reactive({
  prop: '',
  order: ''
})

onMounted(() => {
  loadLogData()
})

// 加载日志数据
const buildParams = () => {
  const params = {
    operationType: queryForm.operationType || undefined,
    operator: queryForm.operator?.trim() || undefined,
    module: queryForm.module || undefined,
    result: queryForm.result || undefined,
    ipAddress: queryForm.ipAddress?.trim() || undefined,
    page: pagination.currentPage,
    pageSize: pagination.pageSize
  }
  if (queryForm.timeRange && queryForm.timeRange.length === 2) {
    params.timeBegin = queryForm.timeRange[0]
    params.timeEnd = queryForm.timeRange[1]
  }
  Object.keys(params).forEach((k) => {
    if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
  })
  return params
}

const loadLogData = async () => {
  loading.value = true
  try {
    const params = buildParams()
    const [listResult, statsResult] = await Promise.all([
      getSystemLogs(params),
      getSystemLogStats(params)
    ])

    const records = Array.isArray(listResult?.records)
      ? listResult.records
      : Array.isArray(listResult?.data?.records)
        ? listResult.data.records
        : Array.isArray(listResult)
          ? listResult
          : []

    logList.value = records
    pagination.total = listResult?.total || listResult?.totalCount || records.length

    if (statsResult) {
      statistics.totalLogs = statsResult.totalLogs || 0
      statistics.successLogs = statsResult.successLogs || 0
      statistics.failureLogs = statsResult.failureLogs || 0
      statistics.uniqueUsers = statsResult.uniqueUsers || 0
    } else {
      updateStatistics(records)
    }

  } catch (error) {
    console.error('加载日志数据失败:', error)
    ElMessage.error('加载日志数据失败')
  } finally {
    loading.value = false
  }
}

// 更新统计信息
const updateStatistics = (logs) => {
  statistics.totalLogs = logs.length
  statistics.successLogs = logs.filter(log => log.result === 'success').length
  statistics.failureLogs = logs.filter(log => log.result === 'failure').length
  statistics.uniqueUsers = new Set(logs.map(log => log.operator)).size
}

// 查询按钮点击事件
const handleQuery = () => {
  pagination.currentPage = 1
  loadLogData()
}

// 重置表单
const handleReset = () => {
  queryFormRef.value?.resetFields()
  pagination.currentPage = 1
  sortParams.prop = ''
  sortParams.order = ''
  loadLogData()
}

// 导出日志
const handleExport = async () => {
  try {
    loading.value = true
    const rows = Array.isArray(logList.value) ? logList.value : []
    if (!rows.length) {
      ElMessage.warning('无可导出日志')
      return
    }
    await exportXlsx(
      rows,
      [
        { label: 'ID', key: 'id' },
        { label: '用户ID', key: 'user_id' },
        { label: '用户名', key: 'username' },
        { label: '操作', key: 'action' },
        { label: '详情', key: 'detail' },
        { label: '时间', key: 'created_at' }
      ],
      `system_logs_${Date.now()}.xlsx`,
      '系统日志'
    )
    ElMessage.success('日志导出成功')
  } catch (error) {
    ElMessage.error('日志导出失败')
  } finally {
    loading.value = false
  }
}

// 分页大小改变
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadLogData()
}

// 页码改变
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  loadLogData()
}

// 排序改变
const handleSortChange = ({ prop, order }) => {
  sortParams.prop = prop
  sortParams.order = order
  loadLogData()
}

// 查看详情
const handleViewDetail = (log) => {
  selectedLog.value = log
  detailDialogVisible.value = true
}

// 格式化日期
const formatDate = (datetime) => {
  if (!datetime) return '-'
  const val = String(datetime)
  return val.includes(' ') ? val.split(' ')[0] : val.split('T')[0]
}

// 格式化时间
const formatTime = (datetime) => {
  if (!datetime) return '-'
  const val = String(datetime)
  if (val.includes(' ')) return val.split(' ')[1]
  if (val.includes('T')) return val.split('T')[1]
  return val
}

// 格式化完整时间
const formatFullTime = (datetime) => {
  if (!datetime) return '-'
  return String(datetime).replace('T', ' ')
}

// 获取操作类型颜色
const getOperationTypeColor = (type) => {
  const colorMap = {
    login: 'primary',
    query: 'info',
    create: 'success',
    update: 'warning',
    delete: 'danger',
    export: 'primary'
  }
  return colorMap[type] || 'info'
}

// 获取操作类型文本
const getOperationTypeText = (type) => {
  const textMap = {
    login: '登录',
    query: '查询',
    create: '新增',
    update: '修改',
    delete: '删除',
    export: '导出'
  }
  return textMap[type] || type
}

// 获取模块文本
const getModuleText = (module) => {
  const textMap = {
    student_info: '学生信息管理',
    consumption_query: '消费信息查询',
    poverty_identification: '贫困生鉴别',
    score_correlation: '成绩关联分析',
    system_management: '系统管理'
  }
  return textMap[module] || module
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.query-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-item {
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-card.primary {
  border-left: 4px solid #409EFF;
}

.stat-card.success {
  border-left: 4px solid #67C23A;
}

.stat-card.warning {
  border-left: 4px solid #E6A23C;
}

.stat-card.danger {
  border-left: 4px solid #F56C6C;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: white;
  font-size: 24px;
}

.stat-card.primary .stat-icon {
  background: #409EFF;
}

.stat-card.success .stat-icon {
  background: #67C23A;
}

.stat-card.warning .stat-icon {
  background: #E6A23C;
}

.stat-card.danger .stat-icon {
  background: #F56C6C;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #303133;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.table-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.time-cell {
  line-height: 1.4;
}

.time-cell .date {
  font-weight: 500;
  color: #303133;
}

.time-cell .time {
  font-size: 12px;
  color: #909399;
}

.module-name {
  font-weight: 500;
  color: #606266;
}

.detail-cell {
  max-width: 300px;
}

.detail-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

/* 日志详情样式 */
.log-detail {
  padding: 10px 0;
}

.detail-content {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.5;
}

.request-params,
.response-result {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.request-params pre,
.response-result pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
}
</style>
