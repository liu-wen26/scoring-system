<template>
  <div class="report-list-page">
    <el-page-header title="成绩报告" @back="$router.back()" />

    <!-- 考试筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="考试">
          <el-select v-model="filterForm.examId" placeholder="选择考试" style="width: 250px" @change="onExamChange" clearable>
            <el-option v-for="exam in examList" :key="exam.id" :label="exam.examName" :value="exam.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="filterForm.subjectId" placeholder="全部科目" style="width: 150px" @change="loadData" clearable>
            <el-option v-for="s in subjectList" :key="s.subjectId" :label="s.subjectName" :value="s.subjectId" />
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

    <template v-if="filterForm.examId && reportData">
      <el-card class="report-card">
        <template #header>
          <div class="report-header">
            <span>成绩分析报告 - {{ reportData.examName || '' }}</span>
            <el-button type="primary" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
          </div>
        </template>

        <!-- 成绩统计 -->
        <el-row :gutter="20" class="stat-row">
          <el-col :span="6">
            <el-statistic title="考试人数" :value="reportData.statistics?.totalStudents || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均分" :value="reportData.statistics?.averageScore || 0" :precision="1" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最高分" :value="reportData.statistics?.maxScore || 0" :precision="1" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最低分" :value="reportData.statistics?.minScore || 0" :precision="1" />
          </el-col>
        </el-row>
        <el-row :gutter="20" class="stat-row">
          <el-col :span="6">
            <el-statistic title="及格率" :value="reportData.statistics?.passRate || 0" suffix="%" :precision="1" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="优秀率" :value="reportData.statistics?.excellentRate || 0" suffix="%" :precision="1" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="中位数" :value="reportData.statistics?.medianScore || 0" :precision="1" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="标准差" :value="reportData.standardDeviation || 0" :precision="1" />
          </el-col>
        </el-row>

        <!-- 分数段分布 -->
        <h3 class="section-title">分数段分布</h3>
        <el-table :data="scoreDistribution" border>
          <el-table-column prop="range" label="分数段" />
          <el-table-column prop="count" label="人数" />
          <el-table-column prop="percentage" label="占比">
            <template #default="scope">
              <el-progress :percentage="scope.row.percentage" />
            </template>
          </el-table-column>
        </el-table>

        <!-- 学生排名 -->
        <h3 class="section-title">学生排名</h3>
        <el-table :data="studentRanks" border v-loading="rankingLoading">
          <el-table-column type="index" label="排名" width="80" :index="(idx) => (rankingPage - 1) * rankingPageSize + idx + 1" />
          <el-table-column prop="studentId" label="学生ID" width="120">
            <template #default="{ row }">
              {{ row.studentId || '未知' }}
            </template>
          </el-table-column>
          <el-table-column prop="studentName" label="姓名" width="120">
            <template #default="{ row }">
              {{ row.studentName || '未知' }}
            </template>
          </el-table-column>
          <el-table-column prop="choiceScore" label="选择题">
            <template #default="{ row }">
              <el-tag type="warning" size="small">{{ row.choiceScore }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="subjectiveScore" label="主观题">
            <template #default="{ row }">
              <el-tag type="primary" size="small">{{ row.subjectiveScore }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="totalScore" label="总分" sortable>
            <template #default="{ row }">
              <span :style="{ color: row.totalScore >= 60 ? '#67C23A' : '#F56C6C', fontWeight: 'bold' }">
                {{ row.totalScore }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'marked' ? 'success' : 'info'" size="small">
                {{ row.status === 'marked' ? '已阅卷' : '待阅卷' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="rankingTotal > 0"
          v-model:current-page="rankingPage"
          :page-size="rankingPageSize"
          :total="rankingTotal"
          layout="total, prev, pager, next"
          @current-change="loadRanking"
          style="margin-top: 20px; justify-content: flex-end;"
        />
      </el-card>
    </template>

    <el-card v-else class="empty-card">
      <el-empty description="请选择考试查看成绩报告" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExams } from '@/api/exam'
import { reportApi } from '@/api/report'

const route = useRoute()

const filterForm = reactive({
  examId: route.query.examId ? Number(route.query.examId) : null,
  subjectId: route.query.subjectId ? Number(route.query.subjectId) : null
})

const examList = ref([])
const subjectList = ref([])
const reportData = ref(null)
const rankingLoading = ref(false)

const rankingPage = ref(1)
const rankingPageSize = 50
const rankingTotal = ref(0)

const studentRanks = ref([])

const scoreDistribution = computed(() => {
  const segments = reportData.value?.scoreSegments || {}
  const total = reportData.value?.statistics?.totalStudents || 1
  const order = ['0-59', '60-69', '70-79', '80-89', '90-100']
  return order.map(range => ({
    range,
    count: segments[range] || 0,
    percentage: Math.round((segments[range] || 0) / total * 1000) / 10
  }))
})

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
  studentRanks.value = []
  rankingTotal.value = 0
  reportData.value = null
  if (examId) {
    const exam = examList.value.find(e => e.id === examId)
    subjectList.value = (exam?.subjects || []).map(s => ({
      subjectId: s.subjectId,
      subjectName: s.subjectName
    }))
  } else {
    subjectList.value = []
  }
}

const loadData = async () => {
  if (!filterForm.examId) return
  await Promise.all([loadReport(), loadRanking()])
}

const loadReport = async () => {
  try {
    const params = {}
    if (filterForm.subjectId) params.subject_id = filterForm.subjectId
    const res = await reportApi.getExamReport(filterForm.examId, params)
    reportData.value = res
  } catch (error) {
    console.error('获取报告失败:', error)
    ElMessage.error('获取报告失败')
  }
}

const loadRanking = async () => {
  rankingLoading.value = true
  try {
    const params = {
      page: rankingPage.value,
      page_size: rankingPageSize
    }
    if (filterForm.subjectId) params.subject_id = filterForm.subjectId
    const res = await reportApi.getRanking(filterForm.examId, params)
    studentRanks.value = res.items || []
    rankingTotal.value = res.total || 0
  } catch (error) {
    console.error('获取排名失败:', error)
  } finally {
    rankingLoading.value = false
  }
}

const refreshData = () => {
  rankingPage.value = 1
  loadData()
}

const handleExport = async () => {
  try {
    await reportApi.exportReport(filterForm.examId, {
      report_type: 'full',
      format: 'excel'
    })
    ElMessage.success('导出任务已创建')
  } catch (error) {
    ElMessage.error('导出失败')
  }
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
.report-list-page {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.report-card {
  margin-top: 0;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-row {
  margin-bottom: 10px;
}

.section-title {
  margin: 20px 0 12px;
  font-size: 16px;
  font-weight: bold;
}

.empty-card {
  margin-top: 20px;
}
</style>