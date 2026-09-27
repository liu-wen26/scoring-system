<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28"><DocumentChecked /></el-icon>
        <span>智能阅卷系统</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/exam">
          <el-icon><Document /></el-icon>
          <span>考试列表</span>
        </el-menu-item>
        
        <el-menu-item index="/scan">
          <el-icon><Upload /></el-icon>
          <span>扫描上传</span>
        </el-menu-item>
        
        <el-sub-menu index="/mark">
          <template #title>
            <el-icon><EditPen /></el-icon>
            <span>阅卷</span>
          </template>
          <el-menu-item index="/mark">阅卷监控</el-menu-item>
          <el-menu-item index="/mark/my-tasks">我的阅卷任务</el-menu-item>
          <el-menu-item index="/mark/question">按题阅卷</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/report">
          <el-icon><TrendCharts /></el-icon>
          <span>成绩报告</span>
        </el-menu-item>

        <el-menu-item index="/answer-card">
          <el-icon><Grid /></el-icon>
          <span>答题卡制作</span>
        </el-menu-item>
        
        <el-sub-menu index="/archive">
          <template #title>
            <el-icon><Collection /></el-icon>
            <span>档案管理</span>
          </template>
          <el-menu-item index="/archive/student">学生档案</el-menu-item>
          <el-menu-item index="/archive/teacher">教师档案</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/user">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta?.title || '当前页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              {{ userStore.userInfo?.real_name || userStore.userInfo?.name || '用户' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    })
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}

.logo .el-icon {
  margin-right: 10px;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
