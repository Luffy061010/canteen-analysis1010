<template>
  <div class="system-management">
    <h2>系统管理</h2>
    <div class="cards">
      <el-card class="card" shadow="hover" @click="goUsers">
        <template #header>用户管理</template>
        <div>查看/添加/修改/删除系统用户。</div>
      </el-card>

      <el-card class="card" shadow="hover" @click="goLogs">
        <template #header>系统日志</template>
        <div>查看系统操作日志并导出。</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goUsers = () => {
  router.push('/users')
}

const goLogs = () => {
  router.push('/logs')
}
</script>

<style scoped>
.system-management {
  padding: 20px;
}
.cards {
  display: flex;
  gap: 16px;
}
.card {
  width: 280px;
  cursor: pointer;
}
</style>
