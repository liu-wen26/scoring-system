<template>
  <div class="mark-monitor-page">
    <el-page-header title="阅卷监控" @back="$router.back()" />

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="考试">
          <el-select v-model="filterForm.examId" placeholder="选择考试" style="width: 250px" @change="onExamChange" clearable>
            <el-option v-for="exam in examList" :key="exam.id" :label="exam.examName" :value="exam.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="filterForm.subjectId" placeholder="选择科目" style="width: 150px" @change="loadData" clearable>
            <el-option v-for="subject in subjectList" :key="subject.id" :label="subject.subjectName" :value="subject.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData" :disabled="!filterForm.examId">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="refreshData" :disabled="!filterForm.examId">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="filterForm.examId" class="monitor-card">
      <template #header>
        <span>阅卷进度监控</span>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-statistic title="总试卷数" :value="stats.total" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已扫描" :value="stats.scanned" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已阅卷" :value="stats.marked" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="完成率" :value="stats.progress" suffix="%" :precision="1" />
        </el-col>
      </el-row>

      <el-divider />

      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-statistic title="平均分" :value="stats.averageScore" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="最高分" :value="stats.maxScore" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="最低分" :value="stats.minScore" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="选择题平均" :value="stats.avgChoiceScore" :precision="1" />
        </el-col>
      </el-row>

      <!-- 学生得分列表 -->
      <el-table :data="markList" border class="mark-table" v-loading="loading">
        <el-table-column prop="studentId" label="学生ID" width="100" />
        <el-table-column label="扫描状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.scanned ? 'success' : 'info'">
              {{ scope.row.scanned ? '已扫描' : '未扫描' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="阅卷状态" width="100">
          <template #default="scope">
            <el-tag :type="getMarkStatusType(scope.row.status)">
              {{ getMarkStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="choiceScore" label="选择题得分" width="120" />
        <el-table-column prop="subjectiveScore" label="主观题得分" width="120" />
        <el-table-column prop="totalScore" label="总分" width="100">
          <template #default="scope">
            <span :style="{ color: scope.row.totalScore >= 60 ? '#67C23A' : '#F56C6C', fontWeight: 'bold' }">
              {{ scope.row.totalScore }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="scope">
            <el-button type="primary" link @click="showDetail(scope.row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && markList.length === 0" description="暂无阅卷数据" />

      <!-- 分页 -->
      <el-pagination
        v-if="pagination.total > 0"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <el-card v-else class="empty-card">
      <el-empty description="请选择考试查看阅卷数据" />
    </el-card>

    <!-- 得分详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="学生得分详情" width="600px" destroy-on-close>
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生ID">{{ detailData.studentId || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="试卷ID">{{ detailData.scanPageId }}</el-descriptions-item>
          <el-descriptions-item label="选择题得分">
            <el-tag type="warning">{{ detailData.choiceScore }} 分</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="主观题得分">
            <el-tag type="primary">{{ detailData.subjectiveScore }} 分</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总分">
            <el-tag type="danger">{{ detailData.totalScore }} 分</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="阅卷状态">
            <el-tag :type="getMarkStatusType(detailData.status)">
              {{ getMarkStatusText(detailData.status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 客观题详情 -->
        <div v-if="detailData.choiceResult" class="detail-section">
          <h4>客观题答题详情</h4>
          <el-table :data="choiceDetails" size="small" border>
            <el-table-column prop="questionNo" label="题号" width="70" />
            <el-table-column prop="selected" label="学生答案" width="120" />
            <el-table-column prop="standardAnswer" label="标准答案" width="120" />
            <el-table-column label="结果" width="80">
              <template #default="{ row }">
                <el-tag :type="row.isCorrect ? 'success' : 'danger'" size="small">
                  {{ row.isCorrect ? '正确' : '错误' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="70" />
          </el-table>
        </div>

        <div v-if="detailData.subjectiveResult" class="detail-section">
          <h4>主观题切割情况</h4>
          <el-table :data="subjectiveDetails" size="small" border>
            <el-table-column prop="questionNo" label="题号" width="80" />
            <el-table-column prop="fullScore" label="满分" width="80" />
            <el-table-column prop="gotScore" label="得分" width="80" />
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExams } from '@/api/exam'
import { markApi } from '@/api/mark'

const route = useRoute()

const filterForm = reactive({
  examId: route.query.examId ? Number(route.query.examId) : null,
  subjectId: route.query.subjectId ? Number(route.query.subjectId) : null
})

const examList = ref([])
const subjectList = ref([])
const loading = ref(false)

const stats = reactive({
  total: 0,
  scanned: 0,
  marked: 0,
  progress: 0,
  averageScore: 0,
  maxScore: 0,
  minScore: 0,
  avgChoiceScore: 0
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const markList = ref([])

const showDetailDialog = ref(false)
const detailData = ref(null)
const detailLoading = ref(false)

const choiceDetails = computed(() => {
  if (!detailData.value?.choiceResult?.results) return []
  return detailData.value.choiceResult.results
})

const subjectiveDetails = computed(() => {
  if (!detailData.value?.subjectiveResult?.cuts) return []
  const scores = detailData.value.subjectiveResult.scores || {}
  return detailData.value.subjectiveResult.cuts.map(cut => ({
    questionNo: cut.questionNo || cut.question_no,
    fullScore: cut.fullScore || cut.full_score || 0,
    gotScore: scores[String(cut.questionNo || cut.question_no)] || '-'
  }))
})

const getMarkStatusType = (status) => {
  const map = { pending: 'info', marking: 'warning', marked: 'success', processed: 'success' }
  return map[status] || 'info'
}

const getMarkStatusText = (status) => {
  const map = { pending: '待阅卷', marking: '阅卷中', marked: '已完成', processed: '已处理' }
  return map[status] || status
}

const fetchExams = async () => {
  try {
    const res = await getExams({ limit: 100 })
    examList.value = res.items || []
    if (filterForm.examId) {
      const exam = examList.value.find(e => e.id === filterForm.examId)
      if (exam) {
        onExamChange(filterForm.examId, false)
      }
    }
  } catch (error) {
    console.error('获取考试列表失败:', error)
  }
}

const onExamChange = (examId, resetSubject = true) => {
  if (resetSubject) {
    filterForm.subjectId = null
  }
  markList.value = []
  pagination.total = 0
  if (examId) {
    const exam = examList.value.find(e => e.id === examId)
    subjectList.value = (exam?.subjects || []).map(s => ({
      id: s.subjectId,
      subjectName: s.subjectName
    }))
  } else {
    subjectList.value = []
  }
}

const loadData = async () => {
  if (!filterForm.examId) return

  loading.value = true
  try {
    // 获取阅卷进度
    const progressParams = {}
    if (filterForm.subjectId) progressParams.subject_id = filterForm.subjectId
    const progress = await markApi.getProgress(filterForm.examId, filterForm.subjectId || undefined)
    if (progress) {
      stats.total = progress.totalPapers || 0
      stats.marked = progress.markedPapers || 0
      stats.scanned = progress.totalPapers || 0
      stats.progress = progress.progress || 0
      stats.averageScore = progress.statistics?.averageScore || 0
      stats.maxScore = progress.statistics?.maxScore || 0
      stats.minScore = progress.statistics?.minScore || 0
    }

    // 获取阅卷结果列表
    const resultParams = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    }
    if (filterForm.subjectId) resultParams.subject_id = filterForm.subjectId
    const results = await markApi.getResults(filterForm.examId, resultParams)
    pagination.total = results.total || 0
    markList.value = (results.items || []).map(r => ({
      ...r,
      scanned: true,
      studentNo: r.studentId || '未知',
      studentName: r.studentId || '未知'
    }))

    // 计算选择题平均分
    if (markList.value.length > 0) {
      const totalChoice = markList.value.reduce((sum, r) => sum + (r.choiceScore || 0), 0)
      stats.avgChoiceScore = Math.round(totalChoice / markList.value.length * 10) / 10
    }
  } catch (error) {
    console.error('获取阅卷数据失败:', error)
    ElMessage.error('获取阅卷数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  pagination.page = 1
  loadData()
}

const showDetail = async (row) => {
  showDetailDialog.value = true
  detailData.value = row
  detailLoading.value = true
  try {
    const paperDetail = await markApi.getPaperDetail(row.scanPageId)
    if (paperDetail) {
      detailData.value = {
        ...row,
        ...paperDetail,
        choiceResult: (paperDetail.choiceResult && paperDetail.choiceResult.results)
          ? paperDetail.choiceResult
          : (paperDetail.ocrResult?.choice ? { results: paperDetail.ocrResult.choice } : null),
        subjectiveResult: (paperDetail.subjectiveResult && paperDetail.subjectiveResult.cuts)
          ? paperDetail.subjectiveResult
          : (paperDetail.ocrResult ? { cuts: paperDetail.ocrResult.subjectiveCuts || [] } : null)
      }
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.warning('试卷扫描详情不存在，仅展示阅卷结果')
  } finally {
    detailLoading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

onMounted(() => {
  fetchExams().then(() => {
    if (filterForm.examId && filterForm.subjectId) {
      loadData()
    }
  })
})
</script>

<style scoped>
.mark-monitor-page {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.monitor-card {
  margin-top: 0;
}

.stat-row {
  margin-bottom: 10px;
}

.mark-table {
  margin-top: 20px;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #303133;
}

.empty-card {
  margin-top: 20px;
}
</style>