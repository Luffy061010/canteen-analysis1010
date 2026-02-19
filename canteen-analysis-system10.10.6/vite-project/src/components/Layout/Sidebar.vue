<template>
  <div class="sidebar">
    <!-- 确保所有菜单项都包含在el-menu组件内 -->
    <el-menu
        :default-active="currentRoute"
        class="sidebar-menu"
        background-color="#ffffff"
        text-color="#606266"
        active-text-color="#409EFF"
        router
        unique-opened
    >
      <template v-if="isAdmin">
        <!-- 系统总览 -->
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>系统总览</span>
        </el-menu-item>

        <!-- 学生信息管理 -->
        <el-menu-item index="/student-info">
          <el-icon><User /></el-icon>
          <span>学生基本信息管理</span>
        </el-menu-item>

        <!-- 消费信息查询 -->
        <el-menu-item index="/consumption-query">
          <el-icon><Search /></el-icon>
          <span>消费信息查询</span>
        </el-menu-item>

        <!-- 消费数据分析 -->
        <el-sub-menu index="analysis">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>消费数据分析</span>
          </template>

          <el-menu-item index="/consumption-analysis/data-query">
            <el-icon><TrendCharts /></el-icon>
            <span>消费数据统计</span>
          </el-menu-item>

          <el-menu-item index="/consumption-analysis/drift-detection">
            <el-icon><Warning /></el-icon>
            <span>消费漂移检测</span>
          </el-menu-item>

          <el-menu-item index="/consumption-analysis/poverty-identification">
            <el-icon><Star /></el-icon>
            <span>贫困生识别</span>
          </el-menu-item>

          <el-menu-item index="/consumption-analysis/score-correlation">
            <el-icon><Connection /></el-icon>
            <span>成绩关联分析</span>
          </el-menu-item>
        </el-sub-menu>
      </template>

      <template v-else>
        <!-- 简化的用户侧边栏：指向用户模块的消费查询与近期变化 -->
        <el-menu-item index="/user-consumption">
          <el-icon><Search /></el-icon>
          <span>我的消费查询</span>
        </el-menu-item>

        <el-menu-item index="/user-recent-changes">
          <el-icon><TrendCharts /></el-icon>
          <span>近期消费变化</span>
        </el-menu-item>
      </template>

      <!-- 系统管理（仅管理员可见） -->
      <el-sub-menu v-if="isAdmin" index="system">
        <template #title>
          <el-icon><User /></el-icon>
          <span>系统管理</span>
        </template>

        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>

        <el-menu-item index="/logs">
          <el-icon><Connection /></el-icon>
          <span>系统日志</span>
        </el-menu-item>
      </el-sub-menu>

    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  House,
  User,
  Search,
  DataAnalysis,
  TrendCharts,
  Warning,
  Star,
  Connection
} from '@element-plus/icons-vue'
import { getStoredUserInfo } from '@/utils/auth'

const route = useRoute()

// 计算当前路由
const currentRoute = computed(() => {
  return route.path
})

// 根据 localStorage 中的 userInfo 判断是否为管理员
const isAdmin = computed(() => {
  const info = getStoredUserInfo()
  return !!(info && info.is_admin)
})
</script>

<style scoped>
.sidebar {
  width: 200px;
  background-color: white;
  height: calc(100vh - 80px);
  position: fixed;
  left: 0;
  top: 80px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border: none;
  width: 100%;
}

.sidebar-menu .el-menu-item,
.sidebar-menu .el-sub-menu__title {
  height: 50px;
  line-height: 50px;
  font-size: 14px;
  border-left: 3px solid transparent;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover {
  background-color: #f5f7fa !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #f0f7ff !important;
  border-left-color: #409EFF;
}

.sidebar-menu .el-sub-menu .el-menu-item {
  height: 45px;
  line-height: 45px;
  min-width: 0;
  padding-left: 50px !important;
}

.sidebar-menu .el-sub-menu .el-menu-item:hover {
  background-color: #f5f7fa !important;
}

.sidebar-menu .el-sub-menu .el-menu-item.is-active {
  background-color: #f0f7ff !important;
  border-left-color: #409EFF;
}

/* 图标样式 */
.sidebar-menu .el-icon {
  font-size: 18px;
  margin-right: 8px;
  vertical-align: middle;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s;
    width: 200px;
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }
}
</style>