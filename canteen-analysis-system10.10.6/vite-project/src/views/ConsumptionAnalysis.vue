<template>
  <!-- 页面：消费数据分析入口（标签页容器） -->
  <div class="consumption-analysis">
    <div class="page-header">
      <h2>消费行为分析</h2>
      <p class="page-description">基于校园餐饮消费数据流的深度分析</p>
    </div>
    
    <div class="analysis-tabs">
      <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick">
        <el-tab-pane label="概念漂移检测" name="drift-detection">
          <router-view />
        </el-tab-pane>
        <el-tab-pane label="用户画像构建" name="user-portrait-analysis">
          <router-view />
        </el-tab-pane>
        <el-tab-pane label="成绩关联性分析" name="score-correlation">
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
const activeTab = ref('drift-detection')

// 监听路由变化更新激活的标签
watch(() => route.name, (newName) => {
  const tabMap = {
    'ConsumptionDrift': 'drift-detection',
    'UserPortraitAnalysis': 'user-portrait-analysis',
    'ScoreCorrelation': 'score-correlation'
  }
  activeTab.value = tabMap[newName] || 'drift-detection'
}, { immediate: true })

const handleTabClick = (tab) => {
  const routeMap = {
    'drift-detection': '/consumption-analysis/drift-detection',
    'user-portrait-analysis': '/consumption-analysis/user-portrait-analysis',
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
