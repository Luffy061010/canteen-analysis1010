<template>
  <div class="page-logs">
    <el-card>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div style="display:flex;gap:8px;align-items:center">
              <el-input v-model="filters.username" placeholder="用户名" style="width:160px" />
              <el-input v-model="filters.action" placeholder="操作类型" style="width:160px" />
              <el-date-picker
                v-model="filters.range"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="yyyy-MM-dd"
                style="width:320px"
              />
              <el-button type="primary" @click="fetchLogs">搜索</el-button>
            </div>
            <div>
              <el-button @click="exportCsv" type="primary" style="margin-right:8px">导出 CSV</el-button>
              <el-button type="danger" @click="deleteSelected" :disabled="selected.length===0">删除选中</el-button>
            </div>
          </div>

      <el-table :data="logs" style="width:100%" @selection-change="onSelectionChange" ref="logsTable" :row-key="row => row.id"  :selectable="() => true" show-header>
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80"/>
        <el-table-column prop="username" label="用户名"/>
        <el-table-column prop="action" label="操作"/>
        <el-table-column prop="detail" label="详情"/>
        <el-table-column prop="created_at" label="时间" width="180"/>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end;align-items:center;gap:12px">
        <el-pagination
          background
          :page-size="page_size"
          v-model:current-page="page"
          :total="total"
          @current-change="fetchLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSystemLogs, exportSystemLogs, searchLogs, deleteSystemLogs } from '@/api/user.js'
import { downloadBlob } from '@/utils/download'

const logs = ref([])
const page = ref(1)
const page_size = ref(50)
const total = ref(0)
const filters = ref({ username: '', action: '', range: [] })

const buildParams = (p = page.value) => {
  const params = { page: p, pageSize: page_size.value }
  if (filters.value.username) params.username = filters.value.username
  if (filters.value.action) params.action = filters.value.action
  if (filters.value.range && filters.value.range.length === 2) {
    params.start_date = filters.value.range[0]
    params.end_date = filters.value.range[1]
  }
  return params
}

const fetchLogs = async (p = page.value) => {
  try {
    const res = await searchLogs(buildParams(p))
    total.value = res.total || 0
    logs.value = res.items || []
    page.value = res.page || p
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.message || '获取日志失败')
  }
}

const exportCsv = async () => {
  try {
    const blob = await exportSystemLogs(buildParams(1))
    downloadBlob(blob, `logs_${Date.now()}.csv`, 'text/csv')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.message || '导出失败')
  }
}

const selected = ref([])
const onSelectionChange = (val) => {
  selected.value = val
}

const deleteSelected = async () => {
  if (!selected.value.length) return
  try {
    await ElMessageBox.confirm('确认删除选中的日志？', '删除', { type: 'warning' })
    const ids = selected.value.map(i => i.id)
    await deleteSystemLogs(ids)
    ElMessage.success('删除成功')
    fetchLogs(1)
  } catch (e) {
    // ignore or show
  }
}

onMounted(() => fetchLogs())
</script>

<style scoped>
.page-logs { padding: 16px }
</style>
