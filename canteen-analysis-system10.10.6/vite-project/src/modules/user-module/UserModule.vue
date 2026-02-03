<template>
  <div class="user-module" style="padding:16px">
    <el-card>
      <template #header>
        <span>用户中心（模块化）</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="消费查询" name="query">
          <user-consumption-query />
        </el-tab-pane>
        <el-tab-pane label="近期变化" name="recent">
          <user-recent-changes />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserConsumptionQuery from './UserConsumptionQuery.vue'
import UserRecentChanges from './UserRecentChanges.vue'

const activeTab = ref('query')
</script>

<style scoped>
.user-module { min-height: 600px }
</style>
