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

const query = async () => {
  if (!uid) return
  try {
    const params = { studentId: uid }
    if (form.value.start) params.timeBegin = form.value.start
    if (form.value.end) params.timeEnd = form.value.end
    const res = await getConsumptionData(params)
    // getConsumptionData 使用 request 实例，会返回接口的 data 部分或自定义结构
    const raw = res?.records || res?.data || res || []
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

onMounted(() => {
  // 默认查询最近 7 天
  const d2 = new Date()
  const d1 = new Date(Date.now() - 6 * 24 * 3600 * 1000)
  form.value.start = d1.toISOString().slice(0,10)
  form.value.end = d2.toISOString().slice(0,10)
  query()
})
</script>

<style scoped>
/* lightweight styles */
</style>
