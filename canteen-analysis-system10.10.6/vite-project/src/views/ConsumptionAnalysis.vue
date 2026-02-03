<template>
  <!-- 页面：消费数据分析入口（标签页容器） -->
  <div class="consumption-analysis">
    <div class="page-header">
      <h2>消费数据分析</h2>
      <p class="page-description">基于学生消费数据的深度分析与贫困生鉴别</p>
    </div>
    
    <div class="analysis-tabs">
      <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick">
        <el-tab-pane label="消费数据统计" name="data-query">
          <router-view />
        </el-tab-pane>
        <el-tab-pane label="消费漂移检测" name="drift-detection">
          <router-view />
        </el-tab-pane>
        <el-tab-pane label="贫困生鉴别" name="poverty-identification">
          <router-view />
        </el-tab-pane>
        <el-tab-pane label="成绩关联分析" name="score-correlation">
          <router-view />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeTab = ref('data-query')

// 监听路由变化更新激活的标签
watch(() => route.name, (newName) => {
  const tabMap = {
    'ConsumptionDataQuery': 'data-query',
    'ConsumptionDrift': 'drift-detection',
    'PovertyIdentification': 'poverty-identification',
    'ScoreCorrelation': 'score-correlation'
  }
  activeTab.value = tabMap[newName] || 'data-query'
}, { immediate: true })

const handleTabClick = (tab) => {
  const routeMap = {
    'data-query': '/consumption-analysis/data-query',
    'drift-detection': '/consumption-analysis/drift-detection',
    'poverty-identification': '/consumption-analysis/poverty-identification',
    'score-correlation': '/consumption-analysis/score-correlation'
  }
  router.push(routeMap[tab.paneName])
}
</script>

<style scoped>
.consumption-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.analysis-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Move :deep selectors to top level */
:deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
}

:deep(.el-tab-pane) {
  height: 100%;
}
</style>
