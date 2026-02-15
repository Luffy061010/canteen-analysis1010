<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-hero">
        <div class="hero-badge">安全 · 便捷 · 数据可视化</div>
        <div class="hero-title">贫困生识别与用户画像构建系统</div>
        <div class="hero-subtitle">面向大学生食堂消费数据流分析</div>
        <ul class="hero-list">
          <li>实时消费趋势与异常识别</li>
          <li>多维度查询与统计分析</li>
          <li>安全可靠的登录与权限控制</li>
        </ul>
      </div>

      <div class="login-card">
        <div class="login-title">系统登录</div>
        <div class="login-subtitle">欢迎回来，请使用学号登录</div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="账号" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入账号" autocomplete="username" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="loginForm.remember">记住登录</el-checkbox>
        </div>

        <div class="login-actions">
          <el-button type="primary" :loading="loading" class="login-button" native-type="submit">登录</el-button>
          <div class="login-links">
            <el-button type="text" @click="openRegister">注册账号</el-button>
            <el-button type="text" @click="openForgotPassword">忘记密码</el-button>
          </div>
        </div>
        <div class="login-tip">建议首次登录后及时修改密码，保护账号安全。</div>
      </el-form>
    </div>

    <!-- 注册对话框 -->
    <el-dialog title="注册" v-model="showRegister" width="460px" destroy-on-close align-center>
      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="registerForm.password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input type="password" v-model="registerForm.confirm" placeholder="请再次输入密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="registerForm.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员（需审批）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="registerForm.role === 'admin'" label="申请理由" prop="reason">
          <el-input type="textarea" v-model="registerForm.reason" placeholder="说明需要管理员权限的理由（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeRegister">取消</el-button>
        <el-button type="primary" :loading="regLoading" @click="submitRegisterWrapper">注册</el-button>
      </template>
    </el-dialog>

    <el-dialog title="忘记密码" v-model="showForgotPassword" width="460px" destroy-on-close align-center>
      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="forgotForm.username" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input type="password" v-model="forgotForm.new_password" placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm">
          <el-input type="password" v-model="forgotForm.confirm" placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeForgotPassword">取消</el-button>
        <el-button type="primary" :loading="forgotLoading" @click="submitForgotPasswordWrapper">确认重置</el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login as loginApi, registerApi, getUserInfo, applyAdmin, forgotPasswordApi } from '@/api/user.js'
import {
  clearStoredUserId,
  clearStoredUserInfo,
  getStoredUserInfo,
  setAuthToken,
  setStoredUserId,
  setStoredUserInfo
} from '@/utils/auth'

const router = useRouter()

const loginFormRef = ref(null)
const registerFormRef = ref(null)
const forgotFormRef = ref(null)
const loading = ref(false)
const regLoading = ref(false)
const forgotLoading = ref(false)

const loginForm = ref({ username: '', password: '', remember: true })
const showRegister = ref(false)
const registerForm = ref({ username: '', password: '', confirm: '', role: 'user', reason: '' })
const showForgotPassword = ref(false)
const forgotForm = ref({ username: '', new_password: '', confirm: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules = {
  username: [
    { required: true, message: '请输入学号（账号为学号）', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      const v = String(value || '')
      if (!/^[0-9]{6,20}$/.test(v)) {
        callback(new Error('学号需为 6-20 位数字'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (value !== registerForm.value.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ]
}

const forgotRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少6位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== forgotForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const normalizeLoginResponse = (res) => {
  if (!res) return { token: '', user: null }
  const data = res.data || res
  const token = data.token || data.accessToken || data.access_token || ''
  const user = data.user || data.userInfo || data.profile || null
  return { token, user }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const payload = { username: loginForm.value.username.trim(), password: loginForm.value.password }
      const res = await loginApi(payload)
      const { token } = normalizeLoginResponse(res)
      if (!token) {
        ElMessage.error('登录失败：未返回有效 token')
        return
      }
      // 覆盖旧的 token/userInfo，使用 /me 接口作为权威来源
      setAuthToken(token, loginForm.value.remember)
      try {
        const me = await getUserInfo()
        setStoredUserInfo(me, loginForm.value.remember)
        // 存储便捷 userId/学号 供用户模块使用
        const uidVal = me?.id || me?.userId || me?.username || me?.studentId || ''
        if (uidVal) setStoredUserId(uidVal, loginForm.value.remember)
      } catch (e) {
        clearStoredUserInfo()
        clearStoredUserId()
      }
      ElMessage.success('登录成功')
      const userInfo = getStoredUserInfo()
      const redirect = router.currentRoute.value.query?.redirect
      if (redirect) {
        router.replace(String(redirect))
      } else if (userInfo && userInfo.is_admin) {
        // 管理员登录后首先展示系统首页（Dashboard）而非系统管理页
        router.replace('/')
      } else {
        router.replace('/user-consumption')
      }
    } catch (error) {
      const msg = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '登录失败'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}

const openRegister = () => {
  showRegister.value = true
}
const closeRegister = () => {
  showRegister.value = false
}

const openForgotPassword = () => {
  forgotForm.value = { username: '', new_password: '', confirm: '' }
  showForgotPassword.value = true
}

const closeForgotPassword = () => {
  showForgotPassword.value = false
}

const submitRegisterWrapper = () => {
  if (!registerFormRef.value) return submitRegister()
  registerFormRef.value.validate((valid) => {
    if (valid) {
      submitRegister()
    } else {
      ElMessage.warning('请完整填写注册信息')
    }
  })
}

const submitRegister = async () => {
  regLoading.value = true
  try {
    const payload = { username: registerForm.value.username.trim(), password: registerForm.value.password }
    const res = await registerApi(payload)
    const { token } = normalizeLoginResponse(res)
    if (token) {
      setAuthToken(token, loginForm.value.remember)
      try {
        const me = await getUserInfo()
        setStoredUserInfo(me, loginForm.value.remember)
        const uidVal = me?.id || me?.userId || me?.username || me?.studentId || ''
        if (uidVal) setStoredUserId(uidVal, loginForm.value.remember)
      } catch (e) {
        clearStoredUserInfo()
        clearStoredUserId()
      }
      ElMessage.success('注册并已登录')
      showRegister.value = false
      const userInfo = getStoredUserInfo()
      if (registerForm.value.role === 'admin') {
        try {
          await applyAdmin({ reason: registerForm.value.reason })
          ElMessage.success('管理员申请已提交，请等待审批')
        } catch (e) {
          console.warn('applyAdmin failed', e)
        }
      }
      if (userInfo && userInfo.is_admin) router.replace('/')
      else router.replace('/user-consumption')
    } else {
      ElMessage.success('注册成功，请登录')
      showRegister.value = false
    }
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '注册失败'
    ElMessage.error(msg)
  } finally {
    regLoading.value = false
  }
}

const submitForgotPasswordWrapper = () => {
  if (!forgotFormRef.value) return submitForgotPassword()
  forgotFormRef.value.validate((valid) => {
    if (valid) {
      submitForgotPassword()
    } else {
      ElMessage.warning('请完整填写重置信息')
    }
  })
}

const submitForgotPassword = async () => {
  forgotLoading.value = true
  try {
    const payload = {
      username: String(forgotForm.value.username || '').trim(),
      new_password: forgotForm.value.new_password
    }
    await forgotPasswordApi(payload)
    ElMessage.success('密码重置成功，请使用新密码登录')
    showForgotPassword.value = false
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '密码重置失败'
    ElMessage.error(msg)
  } finally {
    forgotLoading.value = false
  }
}

</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(1200px 600px at 10% 10%, rgba(64, 158, 255, 0.12), transparent 60%),
    radial-gradient(1000px 500px at 90% 20%, rgba(103, 194, 58, 0.10), transparent 60%),
    linear-gradient(180deg, #f7f9fc 0%, #eef2f7 100%);
}

.login-container {
  width: 960px;
  max-width: 100%;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  align-items: stretch;
}

.login-hero {
  background: linear-gradient(135deg, #1f6feb 0%, #47b2ff 100%);
  color: #fff;
  border-radius: 16px;
  padding: 36px 32px;
  box-shadow: 0 20px 50px rgba(31, 111, 235, 0.25);
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-hero::after {
  content: '';
  position: absolute;
  width: 220px;
  height: 220px;
  right: -60px;
  bottom: -60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
  letter-spacing: 0.5px;
  margin-bottom: 14px;
  width: fit-content;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.hero-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 18px;
}

.hero-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
  font-size: 14px;
}

.hero-list li::before {
  content: '•';
  margin-right: 8px;
  color: rgba(255, 255, 255, 0.9);
}

.login-card {
  padding: 32px 36px;
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
  background: #fff;
  position: relative;
}
.login-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}
.login-subtitle {
  color: #888;
  margin-bottom: 18px;
}
.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.login-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.login-button {
  width: 100%;
}

.login-links {
  display: flex;
  justify-content: space-between;
}

.login-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 900px) {
  .login-container {
    grid-template-columns: 1fr;
  }

  .login-hero {
    display: none;
  }
}
</style>
