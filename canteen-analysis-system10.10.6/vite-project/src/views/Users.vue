<template>
  <div class="page-users">
    <el-card>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div>
          <el-input v-model="filters.username" placeholder="搜索用户名" style="width:220px" @keyup.enter="fetchUsers"/>
          <el-select v-model="filters.is_admin" placeholder="角色" clearable style="width:120px;margin-left:8px">
            <el-option :label="'全部'" :value="''" />
            <el-option :label="'管理员'" :value="1" />
            <el-option :label="'普通'" :value="0" />
          </el-select>
        </div>
        <div>
          <el-button type="primary" @click="openAddUser">添加用户</el-button>
        </div>
      </div>

      <el-table :data="users" style="width:100%">
        <el-table-column prop="id" label="ID" width="80"/>
        <el-table-column prop="username" label="用户名"/>
        <el-table-column prop="is_admin" label="管理员" width="120">
          <template #default="{ row }">
            <el-tag type="success" v-if="row.is_admin">是</el-tag>
            <el-tag v-else>否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="120">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleStatus(row)" active-text="启用" inactive-text="禁用" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="mini" @click="toggleAdmin(row)">{{ row.is_admin ? '撤销管理员' : '设为管理员' }}</el-button>
            <el-button size="mini" type="danger" @click="removeUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end;align-items:center;gap:12px">
        <el-pagination
          background
          :page-size="page_size"
          v-model:current-page="page"
          :total="total"
          @current-change="fetchUsers"
        />
      </div>
    </el-card>

    <el-dialog title="添加用户" v-model="showAddDialog">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="addForm.password" placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="addForm.is_admin" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="addForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, addUserApi, deleteUserApi, setUserRoleApi, updateUserStatusApi } from '@/api/user.js'

const users = ref([])
const page = ref(1)
const page_size = ref(20)
const total = ref(0)
const filters = ref({ username: '', is_admin: '' })

const showAddDialog = ref(false)
const addFormRef = ref(null)
const addForm = ref({ username: '', password: '', is_admin: false, is_active: true })
const addRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const fetchUsers = async (p = page.value) => {
  try {
    const res = await getUsers({
      page: p,
      page_size: page_size.value,
      username: filters.value.username,
      is_admin: filters.value.is_admin
    })
    total.value = res.total || 0
    users.value = res.items || []
    page.value = res.page || p
  } catch (e) {
    ElMessage.error(e.message || '获取用户失败')
  }
}

const openAddUser = () => {
  addForm.value = { username: '', password: '', is_admin: false, is_active: true }
  showAddDialog.value = true
}

const submitAdd = async () => {
  if (!addFormRef.value) return
  addFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请完整填写新增用户信息')
      return
    }
    try {
      const payload = {
        username: String(addForm.value.username || '').trim(),
        password: addForm.value.password,
        is_admin: !!addForm.value.is_admin,
        is_active: !!addForm.value.is_active
      }
      await addUserApi(payload)
      ElMessage.success('添加成功')
      showAddDialog.value = false
      fetchUsers(1)
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || e.response?.data?.message || e.message || '添加失败')
    }
  })
}

const removeUser = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除该用户？', '删除', { type: 'warning' })
    await deleteUserApi(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (e) {
    // ignore
  }
}

const toggleAdmin = async (row) => {
  try {
    await setUserRoleApi(row.id, !row.is_admin)
    ElMessage.success('角色更新')
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.message || '更新失败')
  }
}

const toggleStatus = async (row) => {
  try {
    await updateUserStatusApi(row.id, row.is_active)
    ElMessage.success('状态更新')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.message || '更新失败')
  }
}

onMounted(() => fetchUsers())
</script>

<style scoped>
.page-users { padding: 16px }
</style>
