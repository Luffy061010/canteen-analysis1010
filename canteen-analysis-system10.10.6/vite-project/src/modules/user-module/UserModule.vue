<template>
  <div class="user-module" style="padding:16px">
    <el-card>
      <template #header>
        <span>用户中心（模块化）</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人消费查询" name="query">
          <user-consumption-query />
        </el-tab-pane>
        <el-tab-pane label="个人用户画像" name="portrait">
          <user-portrait />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserConsumptionQuery from './UserConsumptionQuery.vue'
import UserPortrait from './UserPortrait.vue'

const activeTab = ref('query')
</script>

<style scoped>
.user-module { min-height: 600px }
</style>
