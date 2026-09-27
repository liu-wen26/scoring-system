<template>
  <div class="question-mark-page">
    <el-page-header title="按题阅卷" @back="$router.back()" />

    <el-card class="filter-card">
      <template #header>
        <span>选择题目</span>
      </template>
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="考试">
          <el-select v-model="filterForm.examId" placeholder="选择考试" style="width: 200px" @change="onExamChange">
            <el-option v-for="exam in examList" :key="exam.id" :label="exam.examName" :value="exam.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="filterForm.subjectId" placeholder="选择科目" style="width: 150px" @change="onSubjectChange">
            <el-option v-for="subject in subjectList" :key="subject.id" :label="subject.subjectName" :value="subject.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题号">
          <el-select v-model="filterForm.questionNo" placeholder="选择题号" style="width: 120px" @change="loadTasks">
            <el-option v-for="no in questionOptions" :key="no" :label="`第 ${no} 题`" :value="no" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">加载任务</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="warning" :disabled="!filterForm.questionNo" @click="openAIMark">
            AI 辅助阅卷
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="currentTask" class="mark-card">
      <template #header>
        <div class="mark-header">
          <span>第 {{ currentTask.questionNo }} 题 - 学生 {{ currentTask.studentId || '未知' }}</span>
          <span class="score-info">满分: {{ currentTask.fullScore }} 分</span>
        </div>
      </template>

      <div class="mark-body">
        <div class="image-wrapper">
          <img v-if="currentTask.fileUrl" :src="currentTask.fileUrl" alt="题目区域" />
          <el-empty v-else description="暂无图片" />
        </div>

        <div class="score-panel">
          <div class="score-title">请输入得分</div>
          <el-input-number
            v-model="currentScore"
            :min="0"
            :max="currentTask.fullScore"
            :step="0.5"
            :precision="1"
            size="large"
            style="width: 160px"
          />
          <div class="score-actions">
            <el-button type="primary" size="large" @click="submitScore">提交并下一题</el-button>
            <el-button size="large" @click="skipTask">跳过</el-button>
          </div>
          <div class="task-progress">
            进度: {{ markedCount }} / {{ taskList.length }}
          </div>
        </div>
      </div>
    </el-card>

    <el-card v-else-if="taskList.length === 0 && filterForm.questionNo" class="empty-card">
      <el-empty description="该题目没有待阅卷任务" />
    </el-card>

    <AIMarkDialog
      v-model="aiDialogVisible"
      :exam-id="filterForm.examId"
      :subject-id="filterForm.subjectId"
      :question-no="filterForm.questionNo"
      :question-content="currentQuestionContent"
      @finished="onAIFinished"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExams, getExam, getExamQuestions } from '@/api/exam'
import { getQuestionMarkTasks, submitQuestionScore } from '@/api/mark'
import AIMarkDialog from './AIMarkDialog.vue'

const route = useRoute()
const router = useRouter()

const queryExamId = route.query.examId ? Number(route.query.examId) : null
const querySubjectId = route.query.subjectId ? Number(route.query.subjectId) : null
const queryQuestionNo = route.query.questionNo ? String(route.query.questionNo) : null

const filterForm = reactive({
  examId: queryExamId,
  subjectId: querySubjectId,
  questionNo: queryQuestionNo
})

const examList = ref([])
const subjectList = ref([])
const questionOptions = ref([])
const taskList = ref([])
const currentIndex = ref(0)
const currentScore = ref(0)
const aiDialogVisible = ref(false)
const currentQuestionContent = ref('')
const examQuestions = ref([])

const currentTask = computed(() => {
  if (taskList.value.length === 0) return null
  return taskList.value[currentIndex.value] || null
})

const markedCount = computed(() => {
  return taskList.value.filter(t => t.status === 'marked').length
})

onMounted(async () => {
  const res = await getExams()
  examList.value = res.items || []

  // 如果有 URL 参数，自动初始化并加载
  if (queryExamId) {
    await initFromQuery()
  }
})

const initFromQuery = async () => {
  if (!queryExamId) return
  try {
    // 加载考试详情及科目
    const examRes = await getExam(queryExamId)
    subjectList.value = (examRes.subjects || []).map(s => ({
      id: s.subjectId,
      subjectName: s.subjectName
    }))

    // 若未指定科目，尝试取第一个
    if (!filterForm.subjectId && subjectList.value.length > 0) {
      filterForm.subjectId = subjectList.value[0].id
    }

    // 加载题号选项：优先从答题卡配置读取主观题题号
    await loadQuestionOptions(examRes)

    // 加载题目信息
    await loadExamQuestions()

    // 若未指定题号，默认取第一个可选题号
    if (!filterForm.questionNo && questionOptions.value.length > 0) {
      filterForm.questionNo = questionOptions.value[0]
    }

    updateCurrentQuestionContent()

    if (filterForm.examId && filterForm.subjectId && filterForm.questionNo) {
      await loadTasks()
    }
  } catch (error) {
    console.error('自动加载失败:', error)
  }
}

const loadQuestionOptions = async (examRes = null) => {
  questionOptions.value = []
  if (!filterForm.examId || !filterForm.subjectId) return
  try {
    const res = examRes || await getExam(filterForm.examId)
    const subject = res.subjects?.find(s => s.subjectId === filterForm.subjectId)
    const answerCard = subject?.answerCard
    const regions = answerCard?.regions || []
    const subjectiveNos = regions
      .filter(r => r.type === 'subjective' || r.type === 'subjective_region')
      .map(r => String(r.questionNo || r.question_no || ''))
      .filter(n => n)
    if (subjectiveNos.length > 0) {
      questionOptions.value = [...new Set(subjectiveNos)].sort((a, b) => parseInt(a) - parseInt(b))
      return
    }

    // 无答题卡区域时，从 exam_questions 读取主观题题号
    const qRes = await getExamQuestions(filterForm.examId, filterForm.subjectId)
    const questionNos = (qRes.items || [])
      .filter(q => q.questionType === 'subjective')
      .map(q => String(q.questionNo))
      .filter(n => n)
    if (questionNos.length > 0) {
      questionOptions.value = [...new Set(questionNos)].sort((a, b) => parseInt(a) - parseInt(b))
      return
    }
  } catch (error) {
    console.error('读取答题卡题号失败:', error)
  }
  // 兜底：默认 1-30
  questionOptions.value = Array.from({ length: 30 }, (_, i) => String(i + 1))
}

const onExamChange = async (examId) => {
  filterForm.subjectId = null
  filterForm.questionNo = null
  subjectList.value = []
  questionOptions.value = []
  taskList.value = []
  if (!examId) return
  const res = await getExam(examId)
  subjectList.value = (res.subjects || []).map(s => ({
    id: s.subjectId,
    subjectName: s.subjectName
  }))
}

const onSubjectChange = async () => {
  filterForm.questionNo = null
  taskList.value = []
  examQuestions.value = []
  await loadQuestionOptions()
  await loadExamQuestions()
}

const loadExamQuestions = async () => {
  if (!filterForm.examId || !filterForm.subjectId) return
  try {
    const res = await getExamQuestions(filterForm.examId, filterForm.subjectId)
    examQuestions.value = res.items || []
  } catch (e) {
    console.error('加载题目失败:', e)
  }
}

const updateCurrentQuestionContent = () => {
  const q = examQuestions.value.find(q => String(q.questionNo) === String(filterForm.questionNo))
  currentQuestionContent.value = q?.questionContent || ''
}

const openAIMark = () => {
  updateCurrentQuestionContent()
  aiDialogVisible.value = true
}

const onAIFinished = () => {
  loadTasks()
}

const loadTasks = async () => {
  if (!filterForm.examId || !filterForm.subjectId || !filterForm.questionNo) {
    ElMessage.warning('请选择考试、科目和题号')
    return
  }
  try {
    const res = await getQuestionMarkTasks({
      examId: filterForm.examId,
      subjectId: filterForm.subjectId,
      questionNo: filterForm.questionNo,
      status: 'pending'
    })
    taskList.value = res.items || []
    currentIndex.value = 0
    currentScore.value = 0
  } catch (e) {
    ElMessage.error('加载任务失败')
  }
}

const submitScore = async () => {
  if (!currentTask.value) return
  try {
    await submitQuestionScore(currentTask.value.resultId, {
      questionNo: currentTask.value.questionNo,
      score: currentScore.value
    })
    currentTask.value.status = 'marked'
    currentTask.value.gotScore = currentScore.value
    ElMessage.success('提交成功')
    nextTask()
  } catch (e) {
    ElMessage.error('提交失败')
  }
}

const skipTask = () => {
  nextTask()
}

const nextTask = () => {
  if (currentIndex.value < taskList.value.length - 1) {
    currentIndex.value++
    currentScore.value = taskList.value[currentIndex.value].gotScore || 0
  } else {
    ElMessage.info('已经是最后一题')
  }
}
</script>

<style scoped>
.question-mark-page {
  padding: 20px;
}

.filter-card,
.mark-card,
.empty-card {
  margin-top: 20px;
}

.mark-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-info {
  color: #F56C6C;
  font-weight: bold;
}

.mark-body {
  display: flex;
  gap: 24px;
}

.image-wrapper {
  flex: 1;
  min-height: 400px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

.image-wrapper img {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
}

.score-panel {
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.score-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.score-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.task-progress {
  color: #909399;
  font-size: 14px;
}
</style>