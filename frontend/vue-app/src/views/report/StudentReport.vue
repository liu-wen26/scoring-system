<template>
  <div class="student-report">
    <div class="report-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
      </div>
      <div class="header-center">
        <div class="exam-title">{{ reportData.exam.name || '' }}（{{ reportData.subject.name || '' }}）</div>
        <div class="student-info">{{ reportData.grade.name || '' }} {{ reportData.class.name || '' }} {{ reportData.student.name || '' }}</div>
      </div>
      <div class="header-right">
        <el-button type="primary" plain size="small">预览试卷</el-button>
      </div>
    </div>

    <div class="report-body">
      <div class="left-menu">
        <div class="menu-item" :class="{ active: activeMenu === 'report' }" @click="activeMenu = 'report'">个人成绩单报告</div>
        <div class="menu-item" :class="{ active: activeMenu === 'wrong' }" @click="activeMenu = 'wrong'">错题集</div>
      </div>

      <div v-if="activeMenu === 'report'" class="main-content">
        <!-- 总体水平 -->
        <div class="content-card">
          <div class="card-title">{{ reportData.student.name || '' }}本场考试总体水平</div>
          <div class="level-circles">
            <div class="circle-item orange">
              <div class="circle-value">{{ formatNumber(reportData.summary.totalScore) }}</div>
              <div class="circle-label">我的总分</div>
            </div>
            <div class="circle-item gray">
              <div class="circle-value">{{ formatPercent(reportData.summary.beatRate) }}</div>
              <div class="circle-label">击败班级人数比例</div>
            </div>
            <div class="circle-item green">
              <div class="circle-value">{{ formatNumber(reportData.summary.classAvg) }}</div>
              <div class="circle-label">班级平均分</div>
            </div>
            <div class="circle-item blue">
              <div class="circle-value">{{ formatNumber(reportData.summary.classMax) }}</div>
              <div class="circle-label">班级最高分</div>
            </div>
            <div class="circle-item red">
              <div class="circle-value">{{ reportData.summary.classRank || '-' }}</div>
              <div class="circle-label">班级排名</div>
            </div>
            <div class="circle-item yellow">
              <div class="circle-value">{{ reportData.summary.rankChange || 0 }}</div>
              <div class="circle-label">名次波动数</div>
            </div>
          </div>

          <div class="advanced-row">
            <div class="advanced-card">
              <div class="adv-value">{{ formatNumber(reportData.advanced.zScore) }}</div>
              <div class="adv-label"><span class="dot green"></span>Z分数<el-icon class="tip"><QuestionFilled /></el-icon></div>
            </div>
            <div class="advanced-card">
              <div class="adv-value">{{ formatNumber(reportData.advanced.tScore) }}</div>
              <div class="adv-label"><span class="dot orange"></span>T分数<el-icon class="tip"><QuestionFilled /></el-icon></div>
            </div>
            <div class="advanced-card">
              <div class="adv-value">{{ formatNumber(reportData.advanced.meanDeviation) }}</div>
              <div class="adv-label"><span class="dot blue"></span>离均差<el-icon class="tip"><QuestionFilled /></el-icon></div>
            </div>
            <div class="advanced-card">
              <div class="adv-value">{{ formatPercent(reportData.advanced.exceedMeanRate) }}</div>
              <div class="adv-label"><span class="dot red"></span>超均率<el-icon class="tip"><QuestionFilled /></el-icon></div>
            </div>
          </div>
        </div>

        <!-- 难易题得分详情 -->
        <div class="content-card">
          <div class="card-title">{{ reportData.student.name || '' }}本次考试难易题得分详情</div>
          <div class="difficulty-chart">
            <div v-for="item in difficultyList" :key="item.key" class="difficulty-row">
              <div class="diff-label">{{ item.label }}</div>
              <div class="diff-bar-wrapper">
                <div class="diff-bar-bg"></div>
                <div class="diff-bar my-bar" :style="{ width: item.myRate + '%' }"></div>
                <div class="diff-marker class-marker" :style="{ left: item.classRate + '%' }">
                  <div class="marker-tag">班</div>
                </div>
              </div>
              <div class="diff-value">{{ formatPercent(item.myRate) }}</div>
            </div>
          </div>
          <div class="diff-legend">
            <div class="legend-item"><span class="legend-bar my-legend"></span>我的得分率</div>
            <div class="legend-item"><span class="legend-tag">班</span>班级得分率</div>
          </div>
        </div>

        <!-- 历次考试情况 -->
        <div class="content-card">
          <div class="card-title">{{ reportData.student.name || '' }}历次{{ reportData.subject.name || '' }}考试情况</div>
          <div v-if="reportData.history.length > 0" class="history-chart">
            <div class="history-line">
              <div class="history-point"
                v-for="(h, idx) in reportData.history"
                :key="idx"
                :style="{ left: historyPointPosition(idx) + '%', bottom: (h.gradePercentile || 0) + '%' }"
              >
                <div class="point-dot"></div>
                <div class="point-label">{{ formatPercent(h.gradePercentile) }}</div>
              </div>
              <svg class="history-svg">
                <polyline
                  fill="none"
                  stroke="#409eff"
                  stroke-width="2"
                  :points="historyLinePoints"
                />
              </svg>
            </div>
            <div class="history-axis">
              <div class="axis-start">{{ formatDate(reportData.history[0].examTime) }}</div>
              <div class="axis-end">{{ formatDate(reportData.history[reportData.history.length - 1].examTime) }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无历史数据" />
        </div>

        <!-- 薄弱知识点 -->
        <div class="content-card">
          <div class="card-title">{{ reportData.student.name || '' }}本次考试薄弱知识点（得分率低于70%）</div>
          <el-table
            v-if="reportData.weakKnowledge.length > 0"
            :data="reportData.weakKnowledge"
            border
            size="small"
            :header-cell-style="{ background: '#f5f7fa' }"
          >
            <el-table-column prop="name" label="知识点" align="center" />
            <el-table-column prop="myRate" label="我的得分率" align="center" />
            <el-table-column prop="classRate" label="班级得分率" align="center" />
            <el-table-column prop="schoolRate" label="校级得分率" align="center" />
            <el-table-column prop="mastery" label="班级知识点掌握情况" align="center" />
          </el-table>
          <el-empty v-else description="暂无数据" />
        </div>

        <!-- 薄弱题型 + 薄弱能力 -->
        <div class="two-columns">
          <div class="content-card">
            <div class="card-title">{{ reportData.student.name || '' }}本次考试薄弱题型分析</div>
            <div v-if="reportData.weakTypes.length === 0" class="empty-box">
              <el-empty description="暂无数据" :image-size="80" />
              <div class="weak-tag">薄弱题型：<span class="tag-text">无薄弱题型</span></div>
            </div>
            <div v-else>
              <div v-for="t in reportData.weakTypes" :key="t">{{ t }}</div>
            </div>
          </div>
          <div class="content-card">
            <div class="card-title">{{ reportData.student.name || '' }}本次考试薄弱能力分析</div>
            <div v-if="reportData.weakAbilities.length === 0" class="empty-box">
              <el-empty description="暂无数据" :image-size="80" />
              <div class="weak-tag">薄弱能力：<span class="tag-text">无薄弱能力</span></div>
            </div>
            <div v-else>
              <div v-for="a in reportData.weakAbilities" :key="a">{{ a }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错题集 -->
      <div v-else class="main-content wrong-questions-content">
        <div class="content-card">
          <div class="wrong-header">
            <div class="card-title">{{ wrongData.student.name || '' }}本次考试错题集</div>
            <el-button type="primary" size="small" @click="exportWrongQuestions">导出错题集</el-button>
          </div>

          <div v-if="wrongData.wrongQuestions.length > 0" class="wrong-list">
            <div v-for="(item, idx) in wrongData.wrongQuestions" :key="item.questionId" class="wrong-card">
              <div class="wrong-top">
                <div class="question-no">{{ item.questionNo }}</div>
                <div class="question-meta">
                  <span class="meta-item">分值：{{ formatNumber(item.fullScore) }}分</span>
                  <span class="meta-item">该生得分：<span class="score-value">{{ formatNumber(item.studentScore) }}分</span></span>
                  <span class="meta-item">班级得分率：<span class="rate-value">{{ formatPercent(item.classRate) }}</span></span>
                  <span class="meta-item">与年级均值的距离：<span class="distance-value">{{ formatPercent(item.gradeDistance) }}</span></span>
                </div>
              </div>
              <div class="wrong-info">
                <div class="info-line">
                  <span class="info-label">知识点：</span>
                  <span class="info-value">{{ item.knowledgePoint || '暂无' }}</span>
                </div>
                <div class="info-line">
                  <span class="info-label">能力：</span>
                  <span class="info-value">{{ item.ability || '暂无' }}</span>
                </div>
              </div>
              <div class="question-body">
                <div class="question-title">{{ item.questionTitle }}</div>
                <pre class="question-content">{{ item.questionContent || '暂无试题' }}</pre>
              </div>
              <div class="wrong-actions">
                <el-button type="primary" plain size="small" @click="showBestAnswer(item)">查看优解</el-button>
                <el-button type="primary" size="small" @click="showStudentAnswer(item)">查看该生作答</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无错题数据" />
        </div>
      </div>
    </div>
  </div>

  <!-- 查看优解 / 该生作答弹窗 -->
  <el-dialog v-model="answerDialogVisible" :title="answerDialogTitle" width="600px" align-center>
    <div class="answer-dialog-body">
      <pre>{{ answerDialogContent }}</pre>
    </div>
    <template #footer>
      <el-button @click="answerDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, QuestionFilled } from '@element-plus/icons-vue'
import { reportApi } from '@/api/report'

const route = useRoute()
const router = useRouter()

const studentId = Number(route.params.studentId)
const examId = Number(route.query.examId)
const subjectId = Number(route.query.subjectId)

const activeMenu = ref('report')
const loading = ref(false)
const wrongLoading = ref(false)
const reportData = reactive({
  student: {},
  exam: {},
  class: {},
  grade: {},
  subject: {},
  summary: {
    totalScore: 0,
    classAvg: 0,
    classMax: 0,
    classRank: 0,
    gradeRank: 0,
    schoolRank: 0,
    beatRate: 0,
    rankChange: 0
  },
  advanced: {
    zScore: 0,
    tScore: 0,
    meanDeviation: 0,
    exceedMeanRate: 0
  },
  difficulty_analysis: {},
  history: [],
  weakKnowledge: [],
  weakTypes: [],
  weakAbilities: []
})

const wrongData = reactive({
  student: {},
  exam: {},
  class: {},
  grade: {},
  subject: {},
  wrongQuestions: [],
  totalCount: 0
})

const answerDialogVisible = ref(false)
const answerDialogTitle = ref('')
const answerDialogContent = ref('')

const difficultyList = computed(() => {
  const order = ['simple', 'medium', 'hard', 'veryHard']
  return order.map(key => {
    const item = reportData.difficulty_analysis[key] || { label: '-', myRate: 0, classRate: 0 }
    return { ...item, key }
  })
})

const historyLinePoints = computed(() => {
  const list = reportData.history
  if (list.length < 2) return ''
  const width = 100
  const height = 100
  const stepX = width / (list.length - 1)
  return list.map((h, idx) => {
    const x = idx * stepX
    const y = height - (h.gradePercentile || 0)
    return `${x},${y}`
  }).join(' ')
})

const historyPointPosition = (idx) => {
  const list = reportData.history
  if (list.length <= 1) return 0
  return (idx / (list.length - 1)) * 100
}

const formatNumber = (val) => {
  if (val === undefined || val === null) return '-'
  return Number(val).toFixed(2).replace(/\.00$/, '')
}

const formatPercent = (val) => {
  if (val === undefined || val === null) return '-'
  return Number(val).toFixed(2).replace(/\.00$/, '') + '%'
}

const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const loadReport = async () => {
  if (!studentId || !examId) return
  loading.value = true
  try {
    const res = await reportApi.getStudentReport(studentId, examId, subjectId || undefined)
    Object.assign(reportData, {
      student: res.student || {},
      exam: res.exam || {},
      class: res.class || {},
      grade: res.grade || {},
      subject: res.subject || {},
      summary: res.summary || {},
      advanced: res.advanced || {},
      difficulty_analysis: res.difficultyAnalysis || {},
      history: res.history || [],
      weakKnowledge: res.weakKnowledge || [],
      weakTypes: res.weakTypes || [],
      weakAbilities: res.weakAbilities || []
    })
  } catch (e) {
    ElMessage.error('加载学生报告失败')
  } finally {
    loading.value = false
  }
}

const loadWrongQuestions = async () => {
  if (!studentId || !examId) return
  wrongLoading.value = true
  try {
    const res = await reportApi.getStudentWrongQuestions(studentId, examId, subjectId || undefined)
    Object.assign(wrongData, {
      student: res.student || {},
      exam: res.exam || {},
      class: res.class || {},
      grade: res.grade || {},
      subject: res.subject || {},
      wrongQuestions: res.wrongQuestions || [],
      totalCount: res.totalCount || 0
    })
  } catch (e) {
    ElMessage.error('加载错题集失败')
  } finally {
    wrongLoading.value = false
  }
}

const exportWrongQuestions = () => {
  ElMessage.success('错题集导出任务已创建')
}

const showBestAnswer = (item) => {
  answerDialogTitle.value = `${item.questionNo} 优解`
  answerDialogContent.value = item.bestAnswer || '暂无优解'
  answerDialogVisible.value = true
}

const showStudentAnswer = (item) => {
  answerDialogTitle.value = `${item.questionNo} 该生作答`
  answerDialogContent.value = item.studentAnswer || '暂无该生作答记录'
  answerDialogVisible.value = true
}

onMounted(() => {
  loadReport()
  loadWrongQuestions()
})
</script>

<style scoped>
.student-report {
  min-height: 100vh;
  background: #f0f2f5;
}
.report-header {
  height: 64px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-left {
  width: 120px;
}
.header-center {
  text-align: center;
  flex: 1;
}
.exam-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
.student-info {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.header-right {
  width: 120px;
  text-align: right;
}

.report-body {
  display: flex;
  padding: 20px;
  gap: 20px;
}
.left-menu {
  width: 160px;
  background: #fff;
  border-radius: 8px;
  padding: 12px 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  height: fit-content;
}
.menu-item {
  padding: 12px 20px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
}
.menu-item:hover {
  color: #409eff;
  background: #f5f7fa;
}
.menu-item.active {
  background: #409eff;
  color: #fff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.content-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  padding-left: 10px;
  border-left: 4px solid #409eff;
  margin-bottom: 24px;
}

.level-circles {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 32px;
}
.circle-item {
  flex: 1;
  aspect-ratio: 1;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  max-width: 140px;
}
.circle-value {
  font-size: 28px;
  font-weight: bold;
}
.circle-label {
  font-size: 12px;
  margin-top: 4px;
}
.circle-item.orange { background: #f5a623; }
.circle-item.gray { background: #a8a8a8; }
.circle-item.green { background: #67c23a; }
.circle-item.blue { background: #409eff; }
.circle-item.red { background: #f56c6c; }
.circle-item.yellow { background: #e6a23c; }

.advanced-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.advanced-card {
  text-align: center;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}
.adv-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}
.adv-label {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.green { background: #67c23a; }
.dot.orange { background: #f5a623; }
.dot.blue { background: #409eff; }
.dot.red { background: #f56c6c; }
.tip {
  color: #c0c4cc;
  font-size: 12px;
}

.difficulty-chart {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 16px 0;
}
.difficulty-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.diff-label {
  width: 80px;
  text-align: right;
  font-size: 14px;
  color: #606266;
}
.diff-bar-wrapper {
  flex: 1;
  height: 24px;
  position: relative;
}
.diff-bar-bg {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 12px;
  background: #e4e7ed;
  border-radius: 6px;
}
.diff-bar {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 12px;
  border-radius: 6px;
  transition: width 0.5s ease;
}
.diff-bar.my-bar {
  background: #409eff;
}
.diff-marker {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}
.marker-tag {
  background: #e6a23c;
  color: #fff;
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 2px;
}
.diff-value {
  width: 60px;
  font-size: 13px;
  color: #409eff;
  font-weight: bold;
}
.diff-legend {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 16px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}
.legend-bar {
  width: 24px;
  height: 8px;
  border-radius: 4px;
}
.legend-bar.my-legend {
  background: #409eff;
}
.legend-tag {
  background: #e6a23c;
  color: #fff;
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 2px;
}

.history-chart {
  position: relative;
  height: 220px;
  padding: 20px 0 40px;
}
.history-line {
  position: relative;
  height: 160px;
  border-left: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
}
.history-svg {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.history-point {
  position: absolute;
  transform: translate(-50%, 50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.point-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.point-label {
  font-size: 12px;
  color: #409eff;
  margin-bottom: 4px;
}
.history-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}

.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.empty-box {
  text-align: center;
  padding: 20px 0;
}
.weak-tag {
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
}
.tag-text {
  color: #f56c6c;
  background: #fde2e2;
  padding: 2px 8px;
  border-radius: 4px;
}

.wrong-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.wrong-header .card-title {
  margin-bottom: 0;
}

.wrong-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wrong-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.wrong-top {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  padding: 12px 16px;
  gap: 16px;
}

.question-no {
  background: #409eff;
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  min-width: 60px;
  text-align: center;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #606266;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.score-value {
  color: #f5a623;
  font-weight: bold;
}

.rate-value {
  color: #67c23a;
  font-weight: bold;
}

.distance-value {
  color: #67c23a;
  font-weight: bold;
}

.wrong-info {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
}

.info-line {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  color: #909399;
}

.info-value {
  color: #303133;
}

.question-body {
  padding: 16px;
  min-height: 80px;
}

.question-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.question-content {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

.wrong-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
}

.answer-dialog-body {
  max-height: 400px;
  overflow: auto;
}

.answer-dialog-body pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
  color: #303133;
}
</style>
