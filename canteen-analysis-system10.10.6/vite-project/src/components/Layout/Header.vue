<template>
  <div class="header">
    <!-- 品牌信息 -->
    <div class="brand-info">
      <img src="@/assets/logo.png" alt="山西大学" class="logo" @error="handleLogoError">
      <div class="system-name">
        <h1 class="system-title">贫困生识别与用户画像构建系统</h1>
        <p class="system-subtitle">基于大学生食堂消费数据流分析</p>
      </div>
    </div>
    
    <!-- 用户信息 -->
    <div class="user-info">
      <el-dropdown>
        <span class="user-trigger">
          <el-avatar :size="36" :src="user.avatar" />
          <span class="username">{{ user.name }}</span>
          <el-icon><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogin" v-if="!user.isLoggedIn">
              <el-icon><user /></el-icon>
              登录
            </el-dropdown-item>
            <el-dropdown-item @click="handleLogout" v-else>
              <el-icon><switch-button /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import { logout as logoutApi } from '@/api/user.js'
import {
  clearAuthToken,
  clearStoredUserId,
  clearStoredUserInfo,
  getAuthToken,
  getStoredUserInfo
} from '@/utils/auth'

const router = useRouter()

const user = ref({
  name: '未登录',
  avatar: '',
  isLoggedIn: false
})

const syncUserFromStorage = () => {
  const token = getAuthToken()
  const rawUser = getStoredUserInfo()
  if (!token) {
    user.value = { name: '未登录', avatar: '', isLoggedIn: false }
    return
  }
  if (rawUser) {
    user.value = {
      name: rawUser.name || rawUser.username || rawUser.realName || '已登录用户',
      avatar: rawUser.avatar || '',
      isLoggedIn: true
    }
  } else {
    user.value = { name: '已登录用户', avatar: '', isLoggedIn: true }
  }
}

const handleLogoError = (event) => {
  console.log('Logo加载失败')
  event.target.style.display = 'none'
}

const handleLogin = () => {
  router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    try {
      await logoutApi()
    } catch (e) {
      // 忽略接口错误，继续退出
    }

    clearAuthToken()
    clearStoredUserInfo()
    clearStoredUserId()
    syncUserFromStorage()
    ElMessage.success('退出登录成功')
    router.replace('/login')
  } catch (error) {
    // 用户取消退出
  }
}

onMounted(() => {
  syncUserFromStorage()
  window.addEventListener('storage', syncUserFromStorage)
})
</script>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 80px;
  background: white;
  color: #303133;
  z-index: 2000;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.brand-info {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  width: 40px;
  height: 40px;
  margin-right: 12px;
  border-radius: 4px;
}

.system-name {
  display: flex;
  flex-direction: column;
}

.system-title {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
  line-height: 1.2;
}

.system-subtitle {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  color: #303133;
  transition: background-color 0.3s;
}

.user-trigger:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .system-title {
    font-size: 18px;
  }
  
  .system-subtitle {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .username {
    display: none;
  }
  
  .system-title {
    font-size: 16px;
  }
}
</style>