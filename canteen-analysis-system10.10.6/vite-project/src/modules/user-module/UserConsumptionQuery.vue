<template>
  <div>
    <el-form :model="form" inline>
      <el-form-item label="开始">
        <el-date-picker v-model="form.start" type="date" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item label="结束">
        <el-date-picker v-model="form.end" type="date" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="query">查询</el-button>
      </el-form-item>
    </el-form>

    <el-card style="margin-top:12px">
      <template #header>我的消费明细</template>
      <el-table :data="records" style="width:100%">
        <el-table-column prop="consume_time" label="时间" width="180"/>
        <el-table-column prop="amount" label="金额" width="120"/>
        <el-table-column prop="window" label="窗口" width="120"/>
      </el-table>
      <el-pagination
        style="margin-top:12px"
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConsumptionData } from '@/api/user'
import { getStoredUserInfo } from '@/utils/auth'

const userInfo = getStoredUserInfo() || {}
const uid = userInfo.username || userInfo.userId || ''

const form = ref({ start: '', end: '' })
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const query = async () => {
  if (!uid) return
  try {
    const params = {
      studentId: uid,
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (form.value.start) params.timeBegin = form.value.start
    if (form.value.end) params.timeEnd = form.value.end
    const res = await getConsumptionData(params)
    // getConsumptionData 使用 request 实例，会返回接口的 data 部分或自定义结构
    const raw = res?.records || res?.data || res || []
    total.value = Number(res?.total || res?.data?.total || raw.length || 0)
    records.value = (raw || []).map(r => {
      const timeRaw = r.consumptionTime || r.consumption_time || r.consume_time || r.consumeTime || ''
      const timeStr = typeof timeRaw === 'string' ? timeRaw.replace('T',' ') : (timeRaw ? new Date(timeRaw).toISOString().replace('T',' ').slice(0,19) : '')
      return {
        consume_time: timeStr,
        amount: (Number(r.amount || r.money || 0)).toFixed(2),
        window: r.window || r.windowId || r.window_id || r.windowNo || '-'
      }
    })
  } catch (e) {
    console.error('query error', e)
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  query()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  query()
}

onMounted(() => {
  // 默认不限制日期，避免与历史导入数据年份不一致导致空结果
  form.value.start = ''
  form.value.end = ''
  query()
})
</script>

<style scoped>
/* lightweight styles */
</style>
