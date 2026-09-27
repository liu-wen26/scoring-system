<template>
  <div class="exam-list-page">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="考试状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="finished" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="考试类型">
          <el-select v-model="filterForm.examType" placeholder="全部" clearable>
            <el-option label="月考" value="monthly" />
            <el-option label="期中" value="midterm" />
            <el-option label="期末" value="final" />
            <el-option label="模拟" value="simulation" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="参考年级">
          <el-select v-model="filterForm.grade" placeholder="全部" clearable>
            <el-option label="七年级" value="七年级" />
            <el-option label="八年级" value="八年级" />
            <el-option label="九年级" value="九年级" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="考试名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 操作栏 -->
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>考试列表</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建考试
          </el-button>
        </div>
      </template>
      
      <!-- 考试列表 -->
      <div v-for="exam in examList" :key="exam.id" class="exam-item">
        <div class="exam-header">
          <div class="exam-info">
            <el-tag :type="getStatusType(exam.status)">
              {{ getStatusText(exam.status) }}
            </el-tag>
            <span class="exam-name">{{ exam.examName }}</span>
            <el-tag type="info" size="small">{{ exam.examType }}</el-tag>
            <el-tag type="warning" size="small">{{ exam.grade }}</el-tag>
            <span class="exam-time">{{ formatDate(exam.startTime) }} ~ {{ formatDate(exam.endTime) }}</span>
          </div>
          <div class="exam-actions">
            <el-button type="primary" link @click="handleDetail(exam.id)">详情</el-button>
            <el-button type="success" link @click="handleAnswerCard(exam.id)">配置答题卡</el-button>
            <el-button type="danger" link @click="handleDelete(exam.id)">删除</el-button>
          </div>
        </div>
        
        <!-- 学科操作 -->
        <div class="subject-list">
          <div
            v-for="subject in exam.subjects"
            :key="subject.subjectId"
            class="subject-item"
          >
            <div class="subject-info">
              <span class="subject-name">{{ subject.subjectName }}</span>
            </div>
            
            <div class="subject-links">
              <span class="action-link" @click="handleAnswerCardSubject(exam.id, subject.subjectId)">
                <span>答题卡设置</span>
                <el-icon v-if="isAnswerCardDone(subject)" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </span>
              <span class="action-divider">›</span>
              <span class="action-link" @click="handleMarkAssign(exam.id, subject.subjectId)">
                <span>阅卷分工</span>
                <el-icon v-if="isMarkAssignDone(subject)" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </span>
              <span class="action-divider">›</span>
              <span class="action-link" @click="handleScanUpload(exam.id, subject.subjectId)">
                <span>扫描答题卡 {{ subject.scannedCount || 0 }}/{{ exam.totalStudents || 0 }}</span>
                <el-icon v-if="isScanDone(subject, exam)" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </span>
              <span class="action-divider">›</span>
              <span class="action-link" @click="handleMarkMonitor(exam.id, subject.subjectId)">
                <span>阅卷监控</span>
                <el-icon v-if="isMarkMonitorDone(subject)" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </span>
              <span class="action-divider">›</span>
              <span class="action-link" @click="handleSubjectReport(exam.id, subject.subjectId)">
                <span>单科报告</span>
                <el-icon v-if="isReportDone(subject)" class="status-icon done"><CircleCheck /></el-icon>
                <el-icon v-else class="status-icon pending"><Warning /></el-icon>
              </span>
            </div>
            
            <div class="subject-actions">
              <el-button
                v-if="subject.status === 'finished'"
                type="primary"
                size="small"
                @click="handleResumeMark(exam.id, subject.subjectId)"
              >
                恢复批改
              </el-button>
              <el-button
                v-else-if="subject.status === 'marking'"
                type="success"
                size="small"
                @click="handleEndMark(exam.id, subject.subjectId)"
              >
                结束阅卷
              </el-button>
              <el-button
                v-else
                type="primary"
                size="small"
                @click="handleStartMark(exam.id, subject.subjectId)"
              >
                开启批阅
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExams, deleteExam, updateExamStatus } from '@/api/exam'

// 状态判断
const isAnswerCardDone = (subject) => subject.status && subject.status !== 'pending'
const isMarkAssignDone = (subject) => subject.status === 'marking' || subject.status === 'finished'
const isScanDone = (subject, exam) => {
  const total = exam.totalStudents || 0
  return total > 0 && (subject.scannedCount || 0) >= total
}
const isMarkMonitorDone = (subject) => subject.status === 'finished'
const isReportDone = (subject) => subject.status === 'finished'

const router = useRouter()

// 筛选表单
const filterForm = reactive({
  status: '',
  examType: '',
  grade: '',
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 考试列表
const examList = ref([])

// 获取列表
const fetchExamList = async () => {
  try {
    const res = await getExams({
      ...filterForm,
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    })
    examList.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('获取考试列表失败:', error)
  }
}

// 状态处理
const getStatusType = (status) => {
  const map = {
    draft: 'info',
    ongoing: 'primary',
    finished: 'success'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    draft: '草稿',
    ongoing: '进行中',
    finished: '已结束'
  }
  return map[status] || status
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

// 操作处理
const handleSearch = () => {
  pagination.page = 1
  fetchExamList()
}

const handleReset = () => {
  filterForm.status = ''
  filterForm.examType = ''
  filterForm.grade = ''
  filterForm.keyword = ''
  handleSearch()
}

const handleCreate = () => {
  router.push('/exam/create')
}

const handleDetail = (id) => {
  router.push(`/exam/${id}`)
}

const handleAnswerCard = (id) => {
  router.push(`/exam/${id}/answer-card`)
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除该考试吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await deleteExam(id)
    ElMessage.success('删除成功')
    fetchExamList()
  })
}

const handleStartMark = (examId, subjectId) => {
  router.push(`/mark?examId=${examId}&subjectId=${subjectId}`)
}

const handleEndMark = async (examId, subjectId) => {
  await updateExamStatus(examId, 'finished')
  ElMessage.success('阅卷已结束')
  fetchExamList()
}

const handleResumeMark = (examId, subjectId) => {
  router.push(`/mark?examId=${examId}&subjectId=${subjectId}`)
}

const handleAnswerCardSubject = (examId, subjectId) => {
  router.push(`/exam/${examId}/answer-card?subjectId=${subjectId}`)
}

const handleMarkAssign = (examId, subjectId) => {
  router.push(`/mark/assign?examId=${examId}&subjectId=${subjectId}`)
}

const handleScanUpload = (examId, subjectId) => {
  router.push(`/scan?examId=${examId}&subjectId=${subjectId}`)
}

const handleMarkMonitor = (examId, subjectId) => {
  router.push(`/mark?examId=${examId}&subjectId=${subjectId}`)
}

const handleSubjectReport = (examId, subjectId) => {
  router.push(`/report?examId=${examId}&subjectId=${subjectId}`)
}

const handleSizeChange = (size) => {
  pagination.size = size
  fetchExamList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchExamList()
}

onMounted(() => {
  fetchExamList()
})
</script>

<style scoped>
.exam-list-page {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exam-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 16px;
  padding: 16px;
  background: #fff;
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.exam-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.exam-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.exam-time {
  color: #909399;
  font-size: 14px;
}

.subject-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subject-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.subject-info {
  width: 80px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.subject-name {
  font-weight: 500;
}

.subject-links {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  transition: color 0.2s;
}

.action-link:hover {
  color: #409EFF;
}

.action-divider {
  color: #C0C4CC;
  font-size: 14px;
}

.status-icon {
  font-size: 14px;
}

.status-icon.done {
  color: #67C23A;
}

.status-icon.pending {
  color: #E6A23C;
}

.subject-actions {
  width: 100px;
  text-align: right;
  flex-shrink: 0;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
