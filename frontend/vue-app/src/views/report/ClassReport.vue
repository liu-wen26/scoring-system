<template>
  <div class="class-report-page">
    <!-- 顶部 Tab 栏 -->
    <div class="report-topbar">
      <div class="topbar-left">
        <el-button link class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <div class="report-tabs">
          <div class="tab-item active">班级报告</div>
          <div class="tab-item" @click="switchToSchool">校级报告</div>
        </div>
      </div>
      <el-button type="primary" class="export-btn" @click="handleExportReport">
        <span>导出报表</span>
        <el-icon class="export-icon"><TopRight /></el-icon>
      </el-button>
    </div>

    <!-- 考试信息头 -->
    <div class="report-header-bar">
      <div class="exam-info">
        <span class="exam-name">{{ reportData.examName || '未选择考试' }}</span>
        <span class="info-item" v-if="reportData.startTime">
          <el-icon><Clock /></el-icon> {{ formatDateTime(reportData.startTime) }}
        </span>
        <span class="info-item" v-if="reportData.gradeName">
          <el-icon><OfficeBuilding /></el-icon> {{ reportData.gradeName }}
        </span>
        <span class="info-item" v-if="reportData.subjectName">
          <el-icon><Document /></el-icon> {{ reportData.subjectName }}
        </span>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedClassId" placeholder="选择班级" style="width: 140px" @change="onClassChange">
          <el-option v-for="c in classList" :key="c.id" :label="c.className" :value="c.id" />
        </el-select>
        <el-icon class="setting-icon"><Setting /></el-icon>
      </div>
    </div>

    <!-- 未选择考试时显示筛选 -->
    <div v-if="!hasParams" class="filter-section">
      <el-card>
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="考试">
            <el-select v-model="filterForm.examId" placeholder="选择考试" style="width: 250px" @change="onFilterExamChange">
              <el-option v-for="exam in examList" :key="exam.id" :label="exam.examName" :value="exam.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="filterForm.classId" placeholder="选择班级" style="width: 160px" :disabled="!filterForm.examId">
              <el-option v-for="c in filterClassList" :key="c.id" :label="c.className" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="科目">
            <el-select v-model="filterForm.subjectId" placeholder="全部科目" style="width: 140px">
              <el-option label="全部科目" :value="null" />
              <el-option v-for="s in subjectList" :key="s.subjectId" :label="s.subjectName" :value="s.subjectId" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="confirmFilter" :disabled="!filterForm.examId || !filterForm.classId">查询</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <template v-else>
      <!-- 左侧分析维度菜单 + 右侧内容 -->
      <div class="report-body">
        <div class="report-sidebar">
          <div
            v-for="item in menuItems"
            :key="item.key"
            class="menu-item"
            :class="{ active: activeMenu === item.key }"
            @click="activeMenu = item.key"
          >
            {{ item.label }}
          </div>
        </div>

        <div class="report-content">
          <!-- 班级基础成绩分析 -->
          <div v-if="activeMenu === 'basic_analysis'" class="content-panel">
            <div class="panel-title">{{ reportData.className || '' }}基础指标分析</div>
            <div class="panel-subtitle">
              共{{ reportData.summary.totalClasses }}个班级，{{ reportData.summary.totalParticipants }}人参与测验，本班{{ reportData.summary.classScoredStudents }}人实际参与测验，{{ reportData.summary.absentCount }}人缺考
            </div>

            <div class="metric-cards">
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(reportData.statistics.averageScore) }}</div>
                <div class="metric-label"><el-icon><TrendCharts /></el-icon> 平均分</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(reportData.statistics.maxScore) }}</div>
                <div class="metric-label"><el-icon><Trophy /></el-icon> 最高分</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatPercent(reportData.statistics.excellentRate) }}</div>
                <div class="metric-label"><el-icon><Histogram /></el-icon> 优秀率</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatPercent(reportData.statistics.goodRate) }}</div>
                <div class="metric-label"><el-icon><Clock /></el-icon> 良好率</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatPercent(reportData.statistics.passRate) }}</div>
                <div class="metric-label"><el-icon><CircleCheck /></el-icon> 合格率</div>
              </div>
            </div>

            <div class="advanced-metrics">
              <div class="advanced-item">
                <span class="adv-label">综合分</span>
                <span class="adv-value">{{ formatNumber(reportData.statistics.compositeScore) }}</span>
                <el-tooltip content="班级平均分占满分的百分比" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="advanced-item">
                <span class="adv-label">Z分数</span>
                <span class="adv-value">{{ formatNumber(reportData.statistics.zScore) }}</span>
                <el-tooltip content="(班级平均分 - 年级平均分) / 年级标准差" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="advanced-item">
                <span class="adv-label">T分数</span>
                <span class="adv-value">{{ formatNumber(reportData.statistics.tScore) }}</span>
                <el-tooltip content="50 + 10 × Z分数" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="advanced-item">
                <span class="adv-label">离均差</span>
                <span class="adv-value">{{ formatNumber(reportData.statistics.meanDeviation) }}</span>
                <el-tooltip content="班级平均分 - 年级平均分" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="advanced-item">
                <span class="adv-label">超均率</span>
                <span class="adv-value">{{ formatPercent(reportData.statistics.exceedMeanRate) }}</span>
                <el-tooltip content="(班级平均分 - 年级平均分) / 年级平均分 × 100%" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
              <div class="advanced-item">
                <span class="adv-label">差异系数</span>
                <span class="adv-value">{{ formatPercent(reportData.statistics.coefficientVariation) }}</span>
                <el-tooltip content="班级标准差 / 班级平均分 × 100%" placement="top"><el-icon class="adv-tip"><QuestionFilled /></el-icon></el-tooltip>
              </div>
            </div>

            <!-- 3-4-3 分布图 -->
            <div class="section-block">
              <div class="section-title">
                {{ reportData.className || '' }}学生年级3-4-3分布图
                <span class="section-tip">（可点击图形查看具体学生名单）</span>
              </div>
              <div class="distribution-layout">
                <div class="distribution-left">
                  <div class="insight-text">
                    <el-icon class="insight-icon"><WarnTriangleFilled /></el-icon>
                    本班级<span class="highlight">尖子生</span>较多
                  </div>
                  <div class="distribution-bar">
                    <div class="bar-segment top" :style="{ width: distributionPct.top + '%' }">
                      <span v-if="distributionPct.top >= 15" class="bar-label">{{ formatPercent(reportData.distribution.topRate) }}</span>
                    </div>
                    <div class="bar-segment middle" :style="{ width: distributionPct.middle + '%' }">
                      <span v-if="distributionPct.middle >= 15" class="bar-label">{{ formatPercent(reportData.distribution.middleRate) }}</span>
                    </div>
                    <div class="bar-segment bottom" :style="{ width: distributionPct.bottom + '%' }">
                      <span v-if="distributionPct.bottom >= 15" class="bar-label">{{ formatPercent(reportData.distribution.bottomRate) }}</span>
                    </div>
                  </div>
                  <div class="distribution-summary">
                    本班尖子生共有 <span class="highlight">{{ reportData.distribution.topCount }}人</span>，占班级总人数的 <span class="highlight">{{ formatPercent(reportData.distribution.topRate) }}</span>
                  </div>
                  <div class="distribution-legend">
                    <div class="legend-item"><span class="legend-dot top"></span>尖子生(年级前30%)</div>
                    <div class="legend-item"><span class="legend-dot middle"></span>中等生(年级中40%)</div>
                    <div class="legend-item"><span class="legend-dot bottom"></span>后进生(年级后30%)</div>
                  </div>
                </div>
                <div class="distribution-right">
                  <div class="sub-table-title">尖子生学生名单：</div>
                  <el-table :data="reportData.distribution.topStudents" border size="small" class="sub-table">
                    <el-table-column prop="studentName" label="学生" align="center" />
                    <el-table-column prop="score" label="得分" align="center" />
                    <el-table-column prop="classRank" label="班次" align="center" />
                    <el-table-column prop="schoolRank" label="校次" align="center" />
                  </el-table>
                </div>
              </div>
            </div>

            <!-- 波动生与临界生 -->
            <div class="two-columns">
              <div class="section-block">
                <div class="section-title">{{ reportData.className || '' }}波动生</div>
                <div class="small-tabs">
                  <div class="small-tab" :class="{ active: activeVolatilityTab === 'progress' }" @click="activeVolatilityTab = 'progress'">大幅进步</div>
                  <div class="small-tab" :class="{ active: activeVolatilityTab === 'regress' }" @click="activeVolatilityTab = 'regress'">大幅退步</div>
                </div>
                <el-table :data="volatilityStudents" border size="small" class="sub-table">
                  <el-table-column prop="studentName" label="学生" align="center" />
                  <el-table-column prop="rankChange" label="进步名次" align="center" v-if="activeVolatilityTab === 'progress'" />
                  <el-table-column prop="rankChange" label="退步名次" align="center" v-else />
                  <el-table-column label="试卷预览" align="center" width="90">
                    <template #default>
                      <el-icon class="preview-icon"><Document /></el-icon>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="volatilityStudents.length === 0" description="暂无数据" :image-size="60" />
              </div>

              <div class="section-block">
                <div class="section-title">{{ reportData.className || '' }}临界生</div>
                <div class="small-tabs">
                  <div class="small-tab" :class="{ active: activeBorderlineTab === 'excellent' }" @click="activeBorderlineTab = 'excellent'">优秀档临界生</div>
                  <div class="small-tab" :class="{ active: activeBorderlineTab === 'good' }" @click="activeBorderlineTab = 'good'">良好档临界生</div>
                  <div class="small-tab" :class="{ active: activeBorderlineTab === 'pass' }" @click="activeBorderlineTab = 'pass'">合格档临界生</div>
                </div>
                <el-table :data="borderlineStudents" border size="small" class="sub-table">
                  <el-table-column prop="studentName" label="学生" align="center" />
                  <el-table-column prop="score" label="得分" align="center" />
                  <el-table-column prop="diff" label="分差" align="center" />
                  <el-table-column prop="classRank" label="班次" align="center" />
                  <el-table-column prop="schoolRank" label="校次" align="center" />
                  <el-table-column label="试卷预览" align="center" width="90">
                    <template #default>
                      <el-icon class="preview-icon"><Document /></el-icon>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="borderlineStudents.length === 0" description="暂无数据" :image-size="60" />
              </div>
            </div>
          </div>

          <!-- 成绩单 -->
          <div v-else-if="activeMenu === 'score_sheet'" class="content-panel">
            <div class="panel-title">{{ reportData.className || '' }}成绩单</div>
            <div class="panel-actions">
              <el-button link type="primary" @click="handleExportOriginal">导出原卷</el-button>
              <el-button link type="primary" @click="handleExportWrong">导出班级错题</el-button>
            </div>

            <el-table
              :data="sortedStudents"
              v-loading="loading"
              border
              stripe
              class="score-table"
              :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 'bold' }"
            >
              <el-table-column prop="studentName" label="姓名" min-width="120" align="center" />
              <el-table-column prop="studentNo" label="学号" min-width="140" align="center" sortable />
              <el-table-column prop="score" label="得分" min-width="120" align="center" sortable>
                <template #default="{ row }">
                  <span :style="{ color: row.score !== null ? '#303133' : '#999' }">
                    {{ row.score !== null ? row.score : '未阅卷' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="classRank" label="班级排名" min-width="140" align="center" sortable>
                <template #default="{ row }">
                  <span v-if="row.classRank !== undefined && row.classRank !== null">{{ row.classRank }}</span>
                  <span v-else style="color: #999">-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="viewStudentReport(row)">查看报告</el-button>
                  <el-button link type="primary" @click="viewOriginalPaper(row)">查看原卷</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 试题分析 -->
          <div v-else-if="activeMenu === 'question_analysis'" class="content-panel">
            <div class="panel-title">班级内各学生小题分析</div>
            <div class="panel-actions">
              <el-select
                v-model="selectedQuestionIds"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选项"
                style="width: 200px"
                size="small"
              >
                <el-option
                  v-for="q in questionAnalysis.questions"
                  :key="q.questionId"
                  :label="q.questionNo"
                  :value="q.questionId"
                />
              </el-select>
              <el-button type="primary" size="small" @click="exportQuestionAnalysis">
                <el-icon><Download /></el-icon> 导出
              </el-button>
            </div>

            <el-table
              :data="questionTableStudents"
              v-loading="loading"
              border
              class="question-table"
              :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 'bold' }"
            >
              <el-table-column prop="studentName" label="姓名" min-width="100" align="center" fixed="left" />
              <el-table-column prop="studentNo" label="学号" min-width="100" align="center" sortable fixed="left" />
              <el-table-column prop="gradeRank" label="年级排名" min-width="110" align="center" sortable fixed="left" />
              <el-table-column prop="classRank" label="班级排名" min-width="110" align="center" sortable fixed="left" />

              <el-table-column
                v-for="q in selectedQuestions"
                :key="q.questionId"
                :label="q.questionNo"
                align="center"
                min-width="140"
              >
                <el-table-column :label="'得分率'" align="center" min-width="70">
                  <template #default="{ row }">
                    <span>{{ formatPercent(row.questionMap[q.questionId]?.rate) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="'得分'" align="center" min-width="70">
                  <template #default="{ row }">
                    <span>{{ row.questionMap[q.questionId]?.score !== undefined ? row.questionMap[q.questionId].score : '-' }}</span>
                  </template>
                </el-table-column>
              </el-table-column>
            </el-table>
          </div>

          <!-- 个人成绩分析 -->
          <div v-else-if="activeMenu === 'personal_analysis'" class="content-panel">
            <div class="panel-title">个人成绩分析</div>
            <div class="panel-subtitle">点击学生行"查看报告"按钮，查看该学生的个人成绩报告（含总体水平、难易题得分、历次考试、薄弱知识点、错题集等）</div>

            <div class="panel-actions" style="margin-bottom: 16px;">
              <el-input
                v-model="personalSearchKeyword"
                placeholder="搜索学生姓名或学号"
                clearable
                style="width: 280px"
                size="small"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>

            <el-table
              :data="filteredPersonalStudents"
              v-loading="loading"
              border
              stripe
              :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 'bold' }"
            >
              <el-table-column prop="studentName" label="姓名" min-width="120" align="center" />
              <el-table-column prop="studentNo" label="学号" min-width="140" align="center" />
              <el-table-column prop="score" label="得分" min-width="100" align="center" sortable>
                <template #default="{ row }">
                  <span :style="{ color: row.score !== null ? '#303133' : '#999' }">
                    {{ row.score !== null ? row.score : '未阅卷' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="classRank" label="班级排名" min-width="100" align="center" sortable>
                <template #default="{ row }">
                  <span v-if="row.classRank !== undefined && row.classRank !== null">{{ row.classRank }}</span>
                  <span v-else style="color: #999">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="gradeRank" label="年级排名" min-width="100" align="center" sortable>
                <template #default="{ row }">
                  <span v-if="row.gradeRank !== undefined && row.gradeRank !== null">{{ row.gradeRank }}</span>
                  <span v-else style="color: #999">-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="140" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click="viewStudentReport(row)">查看报告</el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="filteredPersonalStudents.length === 0 && !loading" description="暂无学生成绩数据" />
          </div>

          <!-- 其他维度：占位 -->
          <div v-else class="content-panel placeholder-panel">
            <div class="panel-title">{{ activeMenuLabel }}</div>
            <el-empty description="该分析维度正在开发中" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExams, getSubjectsByExam, getClasses } from '@/api/exam'
import { reportApi } from '@/api/report'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const activeMenu = ref('basic_analysis')
const selectedClassId = ref(null)
const activeVolatilityTab = ref('progress')
const activeBorderlineTab = ref('excellent')
const personalSearchKeyword = ref('')
const questionAnalysis = reactive({
  questions: [],
  students: []
})
const selectedQuestionIds = ref([])
const reportData = reactive({
  examId: null,
  examName: '',
  startTime: null,
  gradeName: '',
  subjectName: '',
  classId: null,
  className: '',
  fullScore: 100,
  summary: {
    totalClasses: 0,
    totalParticipants: 0,
    classTotalStudents: 0,
    classScoredStudents: 0,
    absentCount: 0
  },
  statistics: {
    averageScore: 0,
    maxScore: 0,
    minScore: 0,
    passRate: 0,
    goodRate: 0,
    excellentRate: 0,
    compositeScore: 0,
    zScore: 0,
    tScore: 0,
    meanDeviation: 0,
    exceedMeanRate: 0,
    coefficientVariation: 0
  },
  distribution: {
    topCount: 0,
    middleCount: 0,
    bottomCount: 0,
    topRate: 0,
    middleRate: 0,
    bottomRate: 0,
    topStudents: [],
    excellentLine: 90,
    goodLine: 80,
    passLine: 60
  },
  progressStudents: [],
  regressStudents: [],
  borderline: {
    excellent: [],
    good: [],
    pass: []
  },
  students: []
})

const menuItems = [
  { key: 'basic_analysis', label: '班级基础成绩分析' },
  { key: 'paper_review', label: '试卷讲评' },
  { key: 'knowledge_analysis', label: '知识能力分析' },
  { key: 'question_analysis', label: '试题分析' },
  { key: 'score_sheet', label: '成绩单' },
  { key: 'personal_analysis', label: '个人成绩分析' },
  { key: 'question_group', label: '题组模块' },
  { key: 'paper_analysis', label: '试卷分析' },
  { key: 'custom_analysis', label: '自定义分析' }
]

const activeMenuLabel = computed(() => {
  const item = menuItems.find(i => i.key === activeMenu.value)
  return item ? item.label : ''
})

// 查询参数
const queryExamId = computed(() => route.query.examId ? Number(route.query.examId) : null)
const queryClassId = computed(() => route.query.classId ? Number(route.query.classId) : null)
const querySubjectId = computed(() => route.query.subjectId ? Number(route.query.subjectId) : null)
const hasParams = computed(() => !!(queryExamId.value && queryClassId.value))

// 筛选表单
const examList = ref([])
const subjectList = ref([])
const filterClassList = ref([])
const classList = ref([])

const filterForm = reactive({
  examId: null,
  classId: null,
  subjectId: null
})

const sortedStudents = computed(() => {
  const list = (reportData.students || []).map(s => ({ ...s }))
  return list
})

const distributionPct = computed(() => {
  const d = reportData.distribution
  const total = d.topCount + d.middleCount + d.bottomCount || 1
  return {
    top: (d.topCount / total) * 100,
    middle: (d.middleCount / total) * 100,
    bottom: (d.bottomCount / total) * 100
  }
})

const volatilityStudents = computed(() => {
  if (activeVolatilityTab.value === 'progress') {
    return reportData.progressStudents || []
  }
  return reportData.regressStudents || []
})

const borderlineStudents = computed(() => {
  return reportData.borderline[activeBorderlineTab.value] || []
})

const filteredPersonalStudents = computed(() => {
  const keyword = personalSearchKeyword.value.trim().toLowerCase()
  const list = (reportData.students || []).map(s => ({ ...s }))
  if (!keyword) return list
  return list.filter(s =>
    (s.studentName || '').toLowerCase().includes(keyword) ||
    (s.studentNo || '').toLowerCase().includes(keyword)
  )
})

const selectedQuestions = computed(() => {
  return questionAnalysis.questions.filter(q => selectedQuestionIds.value.includes(q.questionId))
})

const questionTableStudents = computed(() => {
  return (questionAnalysis.students || []).map(s => {
    const questionMap = {}
    ;(s.questions || []).forEach(q => {
      questionMap[q.questionId] = q
    })
    return { ...s, questionMap }
  })
})

const formatDateTime = (str) => {
  if (!str) return ''
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const formatNumber = (val) => {
  if (val === undefined || val === null || isNaN(val)) return '0'
  return Number(val).toFixed(2).replace(/\.00$/, '')
}

const formatPercent = (val) => {
  if (val === undefined || val === null || isNaN(val)) return '0.00%'
  return Number(val).toFixed(2) + '%'
}

const loadExams = async () => {
  try {
    const res = await getExams({ limit: 100 })
    examList.value = res.items || []
  } catch (e) {
    console.error(e)
  }
}

const loadFilterClasses = async (gradeId) => {
  filterClassList.value = []
  if (!gradeId) return
  try {
    const res = await getClasses(gradeId)
    filterClassList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const onFilterExamChange = async (examId) => {
  filterForm.classId = null
  filterForm.subjectId = null
  subjectList.value = []
  if (!examId) return
  try {
    const exam = examList.value.find(e => e.id === examId)
    if (exam?.subjects) {
      subjectList.value = exam.subjects
    } else {
      const res = await getSubjectsByExam(examId)
      subjectList.value = res || []
    }
    const gradeId = exam?.gradeId || null
    if (gradeId) {
      await loadFilterClasses(gradeId)
    }
  } catch (e) {
    console.error(e)
  }
}

const confirmFilter = () => {
  router.replace({
    path: '/report',
    query: {
      examId: filterForm.examId,
      classId: filterForm.classId,
      subjectId: filterForm.subjectId || undefined
    }
  })
}

const loadClassOptions = async (gradeId) => {
  if (!gradeId) {
    classList.value = []
    return
  }
  try {
    const res = await getClasses(gradeId)
    classList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const exportQuestionAnalysis = () => {
  const headers = ['姓名', '学号', '年级排名', '班级排名']
  const questionNos = []
  selectedQuestions.value.forEach(q => {
    headers.push(`${q.questionNo}得分率`)
    headers.push(`${q.questionNo}得分`)
    questionNos.push(q.questionId)
  })
  const rows = questionTableStudents.value.map(s => {
    const row = [s.studentName, s.studentNo, s.gradeRank, s.classRank]
    questionNos.forEach(qid => {
      const q = s.questionMap[qid]
      row.push(q?.rate !== undefined ? `${q.rate}%` : '-')
      row.push(q?.score !== undefined ? q.score : '-')
    })
    return row
  })
  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `小题分析_${reportData.className || '班级'}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

const loadQuestionAnalysis = async () => {
  if (!queryClassId.value || !queryExamId.value) return
  try {
    const res = await reportApi.getQuestionAnalysis(queryClassId.value, queryExamId.value, querySubjectId.value)
    questionAnalysis.questions = res.questions || []
    questionAnalysis.students = res.students || []
    if (selectedQuestionIds.value.length === 0 && questionAnalysis.questions.length > 0) {
      selectedQuestionIds.value = questionAnalysis.questions.slice(0, 6).map(q => q.questionId)
    }
  } catch (e) {
    ElMessage.error('加载小题分析失败')
  }
}

const loadReport = async () => {
  if (!queryExamId.value || !queryClassId.value) return
  loading.value = true
  try {
    const res = await reportApi.getClassReport(queryClassId.value, queryExamId.value, querySubjectId.value)
    Object.assign(reportData, {
      examId: res.exam?.id || queryExamId.value,
      examName: res.exam?.name || '',
      startTime: res.exam?.startTime || null,
      gradeName: res.grade?.name || '',
      subjectName: res.subject?.name || '',
      classId: res.class?.id || queryClassId.value,
      className: res.class?.name || '',
      fullScore: res.fullScore || 100,
      summary: {
        totalClasses: res.summary?.totalClasses || 0,
        totalParticipants: res.summary?.totalParticipants || 0,
        classTotalStudents: res.summary?.classTotalStudents || 0,
        classScoredStudents: res.summary?.classScoredStudents || 0,
        absentCount: res.summary?.absentCount || 0
      },
      statistics: {
        averageScore: res.statistics?.averageScore || 0,
        maxScore: res.statistics?.maxScore || 0,
        minScore: res.statistics?.minScore || 0,
        passRate: res.statistics?.passRate || 0,
        goodRate: res.statistics?.goodRate || 0,
        excellentRate: res.statistics?.excellentRate || 0,
        compositeScore: res.statistics?.compositeScore || 0,
        zScore: res.statistics?.zScore || 0,
        tScore: res.statistics?.tScore || 0,
        meanDeviation: res.statistics?.meanDeviation || 0,
        exceedMeanRate: res.statistics?.exceedMeanRate || 0,
        coefficientVariation: res.statistics?.coefficientVariation || 0
      },
      distribution: {
        topCount: res.distribution?.topCount || 0,
        middleCount: res.distribution?.middleCount || 0,
        bottomCount: res.distribution?.bottomCount || 0,
        topRate: res.distribution?.topRate || 0,
        middleRate: res.distribution?.middleRate || 0,
        bottomRate: res.distribution?.bottomRate || 0,
        topStudents: res.distribution?.topStudents || [],
        excellentLine: res.distribution?.excellentLine || 90,
        goodLine: res.distribution?.goodLine || 80,
        passLine: res.distribution?.passLine || 60
      },
      progressStudents: res.progressStudents || [],
      regressStudents: res.regressStudents || [],
      borderline: {
        excellent: res.borderline?.excellent || [],
        good: res.borderline?.good || [],
        pass: res.borderline?.pass || []
      },
      students: res.students || []
    })
    selectedClassId.value = reportData.classId
    if (res.grade?.id) {
      await loadClassOptions(res.grade.id)
    }
  } catch (e) {
    ElMessage.error('加载班级报告失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const onClassChange = (classId) => {
  if (!classId || classId === queryClassId.value) return
  router.replace({
    path: '/report',
    query: {
      examId: queryExamId.value,
      classId: classId,
      subjectId: querySubjectId.value || undefined
    }
  })
}

const switchToSchool = () => {
  ElMessage.info('校级报告功能开发中')
}

const handleExportReport = async () => {
  if (!queryExamId.value) return
  try {
    await reportApi.exportReport(queryExamId.value, {
      report_type: 'class',
      format: 'excel',
      class_id: queryClassId.value,
      subject_id: querySubjectId.value
    })
    ElMessage.success('导出任务已创建')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const handleExportOriginal = () => {
  ElMessage.info('导出原卷功能开发中')
}

const handleExportWrong = () => {
  ElMessage.info('导出班级错题功能开发中')
}

const viewStudentReport = (row) => {
  router.push({
    name: 'StudentReport',
    params: { studentId: row.studentId },
    query: { examId: queryExamId.value, subjectId: querySubjectId.value }
  })
}

const viewOriginalPaper = (row) => {
  ElMessage.info('查看原卷功能开发中')
}

watch(() => activeMenu.value, (val) => {
  if (val === 'question_analysis') {
    loadQuestionAnalysis()
  }
})

watch(() => route.query, () => {
  if (hasParams.value) {
    loadReport()
  }
}, { immediate: false })

onMounted(async () => {
  await loadExams()
  if (queryExamId.value && !queryClassId.value) {
    await onFilterExamChange(queryExamId.value)
  }
  if (hasParams.value) {
    await loadReport()
  }
})
</script>

<style scoped>
.class-report-page {
  min-height: 100%;
  background: #f5f7fa;
}

/* 顶部 Tab 栏 */
.report-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: #606266;
}

.report-tabs {
  display: flex;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 4px;
  gap: 4px;
}

.tab-item {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item:hover {
  color: #409eff;
}

.tab-item.active {
  background: #409eff;
  color: #fff;
  font-weight: 500;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 20px;
  padding: 8px 18px;
}

.export-icon {
  transform: rotate(-45deg);
  font-size: 12px;
}

/* 考试信息头 */
.report-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
}

.exam-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.exam-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.info-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.info-item .el-icon {
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-icon {
  font-size: 20px;
  color: #909399;
  cursor: pointer;
}

.setting-icon:hover {
  color: #409eff;
}

/* 筛选区 */
.filter-section {
  padding: 20px;
}

/* 报告主体 */
.report-body {
  display: flex;
  min-height: calc(100vh - 140px);
}

.report-sidebar {
  width: 170px;
  background: #f5f7fa;
  padding: 16px 0;
  flex-shrink: 0;
}

.menu-item {
  padding: 12px 20px;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background: #e6f2ff;
  color: #409eff;
}

.menu-item.active {
  background: #409eff;
  color: #fff;
  border-left-color: #1064c8;
}

.report-content {
  flex: 1;
  padding: 20px;
  background: #fff;
  overflow: auto;
}

.content-panel {
  background: #fff;
  min-height: 400px;
}

.panel-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  padding-left: 12px;
  border-left: 4px solid #409eff;
  margin-bottom: 12px;
}

.panel-subtitle {
  font-size: 13px;
  color: #909399;
  margin-bottom: 24px;
}

.section-block {
  margin-top: 32px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  padding-left: 10px;
  border-left: 4px solid #409eff;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-tip {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

/* 3-4-3 分布 */
.distribution-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.distribution-left {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 24px;
}

.insight-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 15px;
  color: #606266;
  margin-bottom: 24px;
}

.insight-icon {
  color: #f5a623;
  font-size: 20px;
}

.highlight {
  color: #f5a623;
  font-weight: bold;
}

.distribution-bar {
  display: flex;
  height: 56px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.bar-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  min-width: 40px;
  transition: width 0.5s ease;
}

.bar-segment.top {
  background: #67c23a;
}

.bar-segment.middle {
  background: #409eff;
}

.bar-segment.bottom {
  background: #e6a23c;
}

.distribution-summary {
  text-align: center;
  color: #606266;
  font-size: 14px;
  margin-bottom: 16px;
}

.distribution-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-dot.top {
  background: #67c23a;
}

.legend-dot.middle {
  background: #409eff;
}

.legend-dot.bottom {
  background: #e6a23c;
}

.distribution-right {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
}

.sub-table-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.sub-table {
  width: 100%;
}

.preview-icon {
  color: #409eff;
  font-size: 18px;
  cursor: pointer;
}

.preview-icon:hover {
  color: #66b1ff;
}

/* 双栏布局 */
.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 24px;
}

.two-columns .section-block {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-top: 0;
}

/* 小标签页 */
.small-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.small-tab {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  cursor: pointer;
  transition: all 0.2s;
}

.small-tab:hover {
  color: #409eff;
}

.small-tab.active {
  background: #409eff;
  color: #fff;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}

/* 基础指标卡片 */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 24px 16px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}

.metric-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}

.metric-label .el-icon {
  font-size: 16px;
  color: #909399;
}

/* 高阶指标 */
.advanced-metrics {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.advanced-item {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 14px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.adv-label {
  color: #606266;
}

.adv-value {
  color: #303133;
  font-weight: bold;
  font-size: 16px;
}

.adv-tip {
  color: #c0c4cc;
  cursor: help;
  font-size: 14px;
}

.score-table {
  width: 100%;
}

.question-table {
  width: 100%;
}

.question-table .el-table__header-wrapper th.el-table__cell {
  background: #f5f7fa;
}

.placeholder-panel {
  padding-top: 60px;
}

@media (max-width: 1200px) {
  .metric-cards {
    grid-template-columns: repeat(3, 1fr);
  }
  .advanced-metrics {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .metric-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .advanced-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
