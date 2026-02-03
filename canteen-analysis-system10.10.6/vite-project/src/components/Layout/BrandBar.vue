<template>
  <div class="brand-bar">
    <div class="brand-content">
      <!-- Logo -->
      <div class="logo-container">
        <img 
          src="@/assets/logo.png" 
          alt="山西大学" 
          class="university-logo"
          @error="handleLogoError"
        />
      </div>
      
      <!-- 系统名称和副标题 -->
      <div class="system-info">
        <h1 class="system-title">贫困生识别与用户画像构建系统</h1>
        <p class="system-subtitle">基于大学生食堂消费数据流分析</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const handleLogoError = (event) => {
  console.log('Logo加载失败')
  event.target.style.display = 'none'
}
</script>

<style scoped>
.brand-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 80px;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: white;
  z-index: 2000;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.brand-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.logo-container {
  display: flex;
  align-items: center;
  margin-right: 16px;
}

.university-logo {
  width: 50px;
  height: 50px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px;
}

.system-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.system-title {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  line-height: 1.2;
}

.system-subtitle {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
  font-weight: normal;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .brand-content {
    padding: 0 16px;
  }
  
  .system-title {
    font-size: 20px;
  }
  
  .system-subtitle {
    font-size: 12px;
  }
  
  .university-logo {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 480px) {
  .system-title {
    font-size: 18px;
  }
  
  .brand-content {
    padding: 0 12px;
  }
}
</style>