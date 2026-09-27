<template>
  <div class="exam-detail-page">
    <el-page-header title="考试详情" @back="$router.back()" />
    
    <el-card v-if="exam" class="detail-card">
      <template #header>
        <div class="detail-header">
          <div>
            <el-tag :type="getStatusType(exam.status)">{{ getStatusText(exam.status) }}</el-tag>
            <span class="exam-title">{{ exam.examName }}</span>
          </div>
          <el-button type="primary" @click="handleEdit">编辑</el-button>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="考试类型">{{ exam.examType }}</el-descriptions-item>
        <el-descriptions-item label="考试级别">{{ exam.examLevel }}</el-descriptions-item>
        <el-descriptions-item label="参考年级">{{ exam.grade }}</el-descriptions-item>
        <el-descriptions-item label="总分">{{ exam.totalScore }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(exam.startTime) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatDate(exam.endTime) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ exam.description || '无' }}</el-descriptions-item>
      </el-descriptions>
      
      <h3 class="section-title">科目进度</h3>
      <el-table :data="exam.subjects" border>
        <el-table-column prop="subjectName" label="科目" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getSubjectStatusType(scope.row.status)">
              {{ getSubjectStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="totalScore" label="总分" />
        <el-table-column label="扫描进度">
          <template #default="scope">
            <el-progress :percentage="scope.row.progress" />
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" link @click="handleSubjectDetail(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getExam } from '@/api/exam'

const route = useRoute()
const router = useRouter()
const exam = ref(null)

const fetchExam = async () => {
  try {
    const res = await getExam(route.params.id)
    exam.value = res
  } catch (error) {
    console.error('获取考试详情失败:', error)
  }
}

const getStatusType = (status) => {
  const map = { draft: 'info', ongoing: 'primary', finished: 'success' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { draft: '草稿', ongoing: '进行中', finished: '已结束' }
  return map[status] || status
}

const getSubjectStatusType = (status) => {
  const map = { pending: 'info', scanning: 'warning', marking: 'primary', finished: 'success' }
  return map[status] || 'info'
}

const getSubjectStatusText = (status) => {
  const map = { pending: '待开始', scanning: '扫描中', marking: '阅卷中', finished: '已完成' }
  return map[status] || status
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

const handleEdit = () => {
  router.push(`/exam/create?id=${route.params.id}`)
}

const handleSubjectDetail = (subject) => {
  router.push(`/mark?examId=${route.params.id}&subjectId=${subject.subjectId}`)
}

onMounted(() => {
  fetchExam()
})
</script>

<style scoped>
.exam-detail-page {
  padding: 0;
}

.detail-card {
  margin-top: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exam-title {
  font-size: 18px;
  font-weight: bold;
  margin-left: 12px;
}

.section-title {
  margin: 20px 0 12px;
  font-size: 16px;
  font-weight: bold;
}
</style>
