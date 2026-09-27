<template>
  <div class="user-list-page">
    <el-page-header title="用户管理" @back="$router.back()" />
    
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>用户列表</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </template>
      
      <el-table :data="userList" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="realName" label="真实姓名" />
        <el-table-column prop="role" label="角色">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)">
              {{ getRoleText(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
              {{ scope.row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </el-card>
    
    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学科教师" value="subject_teacher" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, createUser, updateUser, deleteUser } from '@/api/user'

const userList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const form = reactive({
  username: '',
  password: '',
  realName: '',
  role: '',
  phone: '',
  email: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const getRoleType = (role) => {
  const map = { admin: 'danger', teacher: 'primary', subject_teacher: 'success' }
  return map[role] || 'info'
}

const getRoleText = (role) => {
  const map = { admin: '管理员', teacher: '教师', subject_teacher: '学科教师' }
  return map[role] || role
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    })
    userList.value = res
    pagination.total = res.length
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const handleCreate = () => {
  isEdit.value = false
  currentId.value = null
  Object.assign(form, {
    username: '',
    password: '',
    realName: '',
    role: '',
    phone: '',
    email: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该用户吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  })
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await updateUser(currentId.value, form)
    } else {
      await createUser(form)
    }
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchUsers()
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-list-page {
  padding: 0;
}

.table-card {
  margin-top: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
