<template>
  <div class="my-mark-tasks-page">
    <el-page-header title="我的阅卷任务" @back="$router.back()" />

    <el-card class="task-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>待批阅任务</span>
        </div>
      </template>

      <el-table :data="taskList" v-loading="loading" style="width: 100%">
        <el-table-column prop="examName" label="考试" min-width="180" />
        <el-table-column prop="subjectName" label="科目" width="120" />
        <el-table-column label="题号" width="120">
          <template #default="{ row }">
            {{ row.questionNosText }}
          </template>
        </el-table-column>
        <el-table-column prop="markModeText" label="批阅方式" width="100" />
        <el-table-column prop="allocationModeText" label="分配方式" width="120" />
        <el-table-column label="进度" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="row.progress >= 100 ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column prop="statusText" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.statusText }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="startMark(row)">
              开始批阅
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && taskList.length === 0" description="暂无阅卷任务" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { markApi } from '@/api/mark'

const router = useRouter()
const taskList = ref([])
const loading = ref(false)

const markModeMap = {
  single: '单批',
  double: '双批',
  multiple: '多批'
}

const allocationModeMap = {
  efficiency: '效率优先',
  balance: '平均分配',
  random: '随机分配'
}

const statusMap = {
  pending: { text: '待开始', type: 'info' },
  marking: { text: '阅卷中', type: 'warning' },
  paused: { text: '已暂停', type: 'danger' },
  completed: { text: '已完成', type: 'success' }
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await markApi.getTasks()
    taskList.value = (res.items || []).map(item => {
      const nos = item.questionNos || []
      return {
        ...item,
        questionNosText: nos.join('、') || '-',
        markModeText: markModeMap[item.markMode] || '单批',
        allocationModeText: allocationModeMap[item.allocationMode] || '效率优先',
        statusText: statusMap[item.status]?.text || item.status,
        progress: item.progress || 0
      }
    })
  } catch (error) {
    console.error('获取阅卷任务失败:', error)
    ElMessage.error('获取阅卷任务失败')
  } finally {
    loading.value = false
  }
}

const startMark = (row) => {
  const nos = row.questionNos || []
  const questionNo = nos[0] || ''
  if (!questionNo) {
    ElMessage.warning('该任务没有分配题号')
    return
  }
  router.push({
    path: '/mark/question',
    query: {
      examId: row.examId,
      subjectId: row.subjectId,
      questionNo
    }
  })
}

const getStatusType = (status) => {
  return statusMap[status]?.type || 'info'
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.my-mark-tasks-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.task-card {
  margin-top: 16px;
}

.card-header {
  font-weight: 500;
  font-size: 16px;
}
</style>
