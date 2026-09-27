<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 左侧个人信息卡片 -->
      <el-col :span="8">
        <el-card class="profile-card">
          <div class="profile-header">
            <el-avatar :size="80" :src="userInfo.avatar" class="profile-avatar">
              {{ userInfo.name ? userInfo.name.charAt(0) : 'U' }}
            </el-avatar>
            <h3 class="profile-name">{{ userInfo.name }}</h3>
            <p class="profile-role">
              <el-tag :type="userInfo.role === 'admin' ? 'danger' : 'primary'">
                {{ getRoleLabel(userInfo.role) }}
              </el-tag>
            </p>
          </div>

          <el-divider />

          <div class="profile-info">
            <div class="info-item">
              <el-icon><User /></el-icon>
              <span class="info-label">用户名</span>
              <span class="info-value">{{ userInfo.username }}</span>
            </div>
            <div class="info-item">
              <el-icon><Message /></el-icon>
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ userInfo.email }}</span>
            </div>
            <div class="info-item">
              <el-icon><Phone /></el-icon>
              <span class="info-label">电话</span>
              <span class="info-value">{{ userInfo.phone || '未设置' }}</span>
            </div>
            <div class="info-item">
              <el-icon><OfficeBuilding /></el-icon>
              <span class="info-label">学校</span>
              <span class="info-value">{{ userInfo.school || '未设置' }}</span>
            </div>
            <div class="info-item">
              <el-icon><Timer /></el-icon>
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ userInfo.createdAt }}</span>
            </div>
            <div class="info-item">
              <el-icon><Clock /></el-icon>
              <span class="info-label">最后登录</span>
              <span class="info-value">{{ userInfo.lastLogin }}</span>
            </div>
          </div>
        </el-card>

        <!-- 统计卡片 -->
        <el-card class="stats-card" style="margin-top: 20px;">
          <template #header>
            <span>工作统计</span>
          </template>
          <div class="work-stats">
            <div class="work-stat-item">
              <div class="work-stat-value">{{ workStats.examCount }}</div>
              <div class="work-stat-label">参与考试</div>
            </div>
            <div class="work-stat-item">
              <div class="work-stat-value">{{ workStats.markCount }}</div>
              <div class="work-stat-label">阅卷数量</div>
            </div>
            <div class="work-stat-item">
              <div class="work-stat-value">{{ workStats.onlineHours }}</div>
              <div class="work-stat-label">在线时长(小时)</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧内容区 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="tabs-header">
              <el-tabs v-model="activeTab">
                <el-tab-pane label="基本信息" name="basic" />
                <el-tab-pane label="修改密码" name="password" />
                <el-tab-pane label="通知设置" name="notification" />
                <el-tab-pane label="操作日志" name="logs" />
              </el-tabs>
            </div>
          </template>

          <!-- 基本信息 -->
          <div v-if="activeTab === 'basic'" class="tab-content">
            <el-form
              ref="basicFormRef"
              :model="basicForm"
              :rules="basicRules"
              label-width="100px"
              style="max-width: 500px;"
            >
              <el-form-item label="头像">
                <el-upload
                  class="avatar-uploader"
                  action="/api/upload"
                  :show-file-list="false"
                  :on-success="handleAvatarSuccess"
                  :before-upload="beforeAvatarUpload"
                >
                  <el-avatar v-if="basicForm.avatar" :size="80" :src="basicForm.avatar" />
                  <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                </el-upload>
              </el-form-item>
              <el-form-item label="姓名" prop="name">
                <el-input v-model="basicForm.name" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="basicForm.email" />
              </el-form-item>
              <el-form-item label="电话" prop="phone">
                <el-input v-model="basicForm.phone" />
              </el-form-item>
              <el-form-item label="学校">
                <el-input v-model="basicForm.school" />
              </el-form-item>
              <el-form-item label="个人简介">
                <el-input
                  v-model="basicForm.bio"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入个人简介..."
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSaveBasic">保存修改</el-button>
                <el-button @click="handleResetBasic">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 修改密码 -->
          <div v-if="activeTab === 'password'" class="tab-content">
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="120px"
              style="max-width: 500px;"
            >
              <el-form-item label="当前密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  show-password
                  placeholder="请输入当前密码"
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  show-password
                  placeholder="请输入新密码"
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次输入新密码"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
                <el-button @click="handleResetPassword">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 通知设置 -->
          <div v-if="activeTab === 'notification'" class="tab-content">
            <el-form label-width="200px" style="max-width: 600px;">
              <el-form-item label="阅卷任务通知">
                <el-switch v-model="notificationForm.markTask" />
                <span class="form-hint">有新的阅卷任务时通知我</span>
              </el-form-item>
              <el-form-item label="成绩发布通知">
                <el-switch v-model="notificationForm.scorePublish" />
                <span class="form-hint">考试成绩发布时通知我</span>
              </el-form-item>
              <el-form-item label="系统公告">
                <el-switch v-model="notificationForm.systemNotice" />
                <span class="form-hint">接收系统维护和功能更新通知</span>
              </el-form-item>
              <el-form-item label="邮件通知">
                <el-switch v-model="notificationForm.emailNotify" />
                <span class="form-hint">通过邮件接收通知</span>
              </el-form-item>
              <el-form-item label="短信通知">
                <el-switch v-model="notificationForm.smsNotify" />
                <span class="form-hint">通过短信接收紧急通知</span>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSaveNotification">保存设置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 操作日志 -->
          <div v-if="activeTab === 'logs'" class="tab-content">
            <el-timeline>
              <el-timeline-item
                v-for="(log, index) in operationLogs"
                :key="index"
                :type="log.type"
                :timestamp="log.time"
                :icon="log.icon"
              >
                <h4>{{ log.title }}</h4>
                <p class="log-detail">{{ log.detail }}</p>
                <p class="log-ip">IP: {{ log.ip }}</p>
              </el-timeline-item>
            </el-timeline>
            <el-pagination
              v-model:current-page="logPagination.page"
              v-model:page-size="logPagination.pageSize"
              :total="logPagination.total"
              layout="prev, pager, next"
              @current-change="handleLogPageChange"
              class="pagination"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Message, Phone, OfficeBuilding, Timer, Clock, Plus } from '@element-plus/icons-vue'

// 当前激活的标签页
const activeTab = ref('basic')

// 用户信息
const userInfo = reactive({
  name: '管理员',
  username: 'admin',
  role: 'admin',
  email: 'admin@school.edu.cn',
  phone: '13800138000',
  school: '实验中学',
  avatar: '',
  createdAt: '2024-01-15 09:00:00',
  lastLogin: '2024-03-20 14:30:00'
})

// 工作统计
const workStats = reactive({
  examCount: 12,
  markCount: 356,
  onlineHours: 128
})

// 角色标签
const getRoleLabel = (role) => {
  const map = {
    admin: '系统管理员',
    teacher: '教师',
    marker: '阅卷老师',
    student: '学生'
  }
  return map[role] || role
}

// 基本信息表单
const basicFormRef = ref(null)
const basicForm = reactive({
  name: userInfo.name,
  email: userInfo.email,
  phone: userInfo.phone,
  school: userInfo.school,
  avatar: userInfo.avatar,
  bio: ''
})

const basicRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ]
}

// 密码表单
const passwordFormRef = ref(null)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 通知设置
const notificationForm = reactive({
  markTask: true,
  scorePublish: true,
  systemNotice: true,
  emailNotify: true,
  smsNotify: false
})

// 操作日志
const operationLogs = ref([
  {
    title: '登录系统',
    detail: '成功登录阅卷系统',
    time: '2024-03-20 14:30:00',
    ip: '192.168.1.100',
    type: 'primary',
    icon: 'User'
  },
  {
    title: '修改密码',
    detail: '成功修改登录密码',
    time: '2024-03-18 10:15:00',
    ip: '192.168.1.100',
    type: 'warning',
    icon: 'Lock'
  },
  {
    title: '完成阅卷',
    detail: '完成数学期中考试阅卷任务，批阅 50 份试卷',
    time: '2024-03-15 16:45:00',
    ip: '192.168.1.100',
    type: 'success',
    icon: 'Check'
  },
  {
    title: '创建考试',
    detail: '创建了 "2024年春季期中考试"',
    time: '2024-03-10 09:00:00',
    ip: '192.168.1.100',
    type: 'success',
    icon: 'Document'
  },
  {
    title: '上传答题卡',
    detail: '上传了 120 份答题卡扫描件',
    time: '2024-03-10 10:30:00',
    ip: '192.168.1.100',
    type: 'primary',
    icon: 'Upload'
  }
])

const logPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 50
})

// 事件处理
const handleAvatarSuccess = (res) => {
  basicForm.avatar = res.url
  ElMessage.success('头像上传成功')
}

const beforeAvatarUpload = (file) => {
  const isJPG = file.type === 'image/jpeg'
  const isPNG = file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG && !isPNG) {
    ElMessage.error('只支持 JPG/PNG 格式')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

const handleSaveBasic = () => {
  basicFormRef.value.validate((valid) => {
    if (valid) {
      Object.assign(userInfo, basicForm)
      ElMessage.success('基本信息保存成功')
    }
  })
}

const handleResetBasic = () => {
  Object.assign(basicForm, userInfo)
}

const handleChangePassword = () => {
  passwordFormRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success('密码修改成功')
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    }
  })
}

const handleResetPassword = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

const handleSaveNotification = () => {
  ElMessage.success('通知设置保存成功')
}

const handleLogPageChange = (val) => {
  logPagination.page = val
}

onMounted(() => {
  Object.assign(basicForm, userInfo)
})
</script>

<style scoped>
.profile-page {
  padding: 20px;
}

.profile-card {
  text-align: center;
}

.profile-header {
  padding: 20px 0;
}

.profile-avatar {
  margin-bottom: 15px;
  font-size: 32px;
  background: #409EFF;
  color: white;
}

.profile-name {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: bold;
}

.profile-role {
  margin: 0;
}

.profile-info {
  text-align: left;
  padding: 0 10px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .el-icon {
  font-size: 18px;
  color: #909399;
  margin-right: 12px;
}

.info-label {
  color: #606266;
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  color: #303133;
  flex: 1;
  text-align: right;
}

.work-stats {
  display: flex;
  justify-content: space-around;
  text-align: center;
}

.work-stat-item {
  flex: 1;
}

.work-stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.work-stat-label {
  font-size: 13px;
  color: #909399;
}

.tabs-header {
  margin: -20px -20px 0;
  padding: 0 20px;
}

.tab-content {
  padding: 20px 0;
}

.avatar-uploader {
  display: inline-block;
}

.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.avatar-uploader .el-upload:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 80px;
  height: 80px;
  text-align: center;
  line-height: 80px;
}

.form-hint {
  margin-left: 15px;
  color: #909399;
  font-size: 13px;
}

.log-detail {
  color: #606266;
  margin: 5px 0;
}

.log-ip {
  color: #909399;
  font-size: 12px;
  margin: 0;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
