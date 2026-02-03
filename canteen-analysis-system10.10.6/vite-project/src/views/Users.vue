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

    <el-dialog title="添加用户" v-model:visible="showAddDialog">
      <el-form :model="addForm">
        <el-form-item label="用户名">
          <el-input v-model="addForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input type="password" v-model="addForm.password" />
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
const addForm = ref({ username: '', password: '' })

const fetchUsers = async (p = page.value) => {
  try {
    const res = await getUsers({ page: p, pageSize: page_size.value })
    total.value = res.total || 0
    users.value = res.items || []
    page.value = res.page || p
  } catch (e) {
    ElMessage.error(e.message || '获取用户失败')
  }
}

const openAddUser = () => {
  addForm.value = { username: '', password: '' }
  showAddDialog.value = true
}

const submitAdd = async () => {
  try {
    await addUserApi(addForm.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    fetchUsers(1)
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.message || '添加失败')
  }
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
