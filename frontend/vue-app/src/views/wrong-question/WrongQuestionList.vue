<template>
  <div class="wrong-question-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="考试">
          <el-select v-model="filterForm.examId" placeholder="选择考试" clearable @change="handleFilterChange">
            <el-option
              v-for="exam in examOptions"
              :key="exam.id"
              :label="exam.name"
              :value="exam.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学生">
          <el-select v-model="filterForm.studentId" placeholder="选择学生" clearable @change="handleFilterChange">
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="filterForm.subject" placeholder="选择学科" clearable @change="handleFilterChange">
            <el-option label="语文" value="语文" />
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
            <el-option label="物理" value="物理" />
            <el-option label="化学" value="化学" />
            <el-option label="生物学" value="生物学" />
            <el-option label="道德与法治" value="道德与法治" />
            <el-option label="历史" value="历史" />
            <el-option label="地理" value="地理" />
            <el-option label="信息科技" value="信息科技" />
            <el-option label="音乐" value="音乐" />
            <el-option label="美术" value="美术" />
            <el-option label="体育与健康" value="体育与健康" />
            <el-option label="综合实践活动" value="综合实践活动" />
          </el-select>
        </el-form-item>
        <el-form-item label="错误类型">
          <el-select v-model="filterForm.errorType" placeholder="错误类型" clearable @change="handleFilterChange">
            <el-option label="概念理解错误" value="concept" />
            <el-option label="计算错误" value="calculation" />
            <el-option label="审题错误" value="misreading" />
            <el-option label="粗心大意" value="careless" />
            <el-option label="知识点缺失" value="knowledge_gap" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.totalCount }}</div>
          <div class="stat-label">总错题数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.conceptErrors }}</div>
          <div class="stat-label">概念错误</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.calculationErrors }}</div>
          <div class="stat-label">计算错误</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.carelessErrors }}</div>
          <div class="stat-label">粗心错误</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>错题列表</span>
          <div>
            <el-button type="success" @click="handleExport">导出错题本</el-button>
            <el-button type="primary" @click="handleBatchTag">批量标注</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="wrongQuestions"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="studentName" label="学生姓名" width="120" />
        <el-table-column prop="examName" label="考试名称" min-width="150" />
        <el-table-column prop="subject" label="学科" width="100" />
        <el-table-column prop="questionNumber" label="题号" width="80" />
        <el-table-column prop="questionContent" label="题目内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="studentAnswer" label="学生答案" width="120" show-overflow-tooltip />
        <el-table-column prop="correctAnswer" label="正确答案" width="120" show-overflow-tooltip />
        <el-table-column prop="score" label="分值" width="80">
          <template #default="scope">
            <span :class="{ 'text-danger': scope.row.score === 0 }">{{ scope.row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="errorType" label="错误类型" width="120">
          <template #default="scope">
            <el-tag :type="getErrorTypeType(scope.row.errorType)">
              {{ getErrorTypeLabel(scope.row.errorType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="录入时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="handleViewDetail(scope.row)">查看</el-button>
            <el-button type="primary" link @click="handleTag(scope.row)">标注</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </el-card>

    <!-- 错题详情弹窗 -->
    <el-dialog v-model="detailDialog.visible" title="错题详情" width="700px">
      <div v-if="detailDialog.data" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生">{{ detailDialog.data.studentName }}</el-descriptions-item>
          <el-descriptions-item label="考试">{{ detailDialog.data.examName }}</el-descriptions-item>
          <el-descriptions-item label="学科">{{ detailDialog.data.subject }}</el-descriptions-item>
          <el-descriptions-item label="题号">第 {{ detailDialog.data.questionNumber }} 题</el-descriptions-item>
          <el-descriptions-item label="分值">{{ detailDialog.data.fullScore }} 分</el-descriptions-item>
          <el-descriptions-item label="得分">
            <span :class="{ 'text-danger': detailDialog.data.score === 0 }">{{ detailDialog.data.score }} 分</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4>题目内容</h4>
          <div class="content-box">{{ detailDialog.data.questionContent }}</div>
        </div>

        <div class="detail-section">
          <h4>学生答案</h4>
          <div class="content-box student-answer">{{ detailDialog.data.studentAnswer }}</div>
        </div>

        <div class="detail-section">
          <h4>正确答案</h4>
          <div class="content-box correct-answer">{{ detailDialog.data.correctAnswer }}</div>
        </div>

        <div class="detail-section">
          <h4>错误分析</h4>
          <el-tag :type="getErrorTypeType(detailDialog.data.errorType)">
            {{ getErrorTypeLabel(detailDialog.data.errorType) }}
          </el-tag>
          <p class="analysis-text">{{ detailDialog.data.analysis || '暂无分析' }}</p>
        </div>

        <div class="detail-section" v-if="detailDialog.data.imageUrl">
          <h4>答题图片</h4>
          <el-image :src="detailDialog.data.imageUrl" fit="contain" style="max-width: 100%; max-height: 300px;" />
        </div>
      </div>
    </el-dialog>

    <!-- 标注弹窗 -->
    <el-dialog v-model="tagDialog.visible" title="错题标注" width="500px">
      <el-form :model="tagForm" label-width="100px">
        <el-form-item label="错误类型">
          <el-select v-model="tagForm.errorType" placeholder="选择错误类型">
            <el-option label="概念理解错误" value="concept" />
            <el-option label="计算错误" value="calculation" />
            <el-option label="审题错误" value="misreading" />
            <el-option label="粗心大意" value="careless" />
            <el-option label="知识点缺失" value="knowledge_gap" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="错误分析">
          <el-input
            v-model="tagForm.analysis"
            type="textarea"
            :rows="4"
            placeholder="请输入错误分析..."
          />
        </el-form-item>
        <el-form-item label="相关知识点">
          <el-select-v2
            v-model="tagForm.knowledgePoints"
            :options="knowledgeOptions"
            placeholder="选择相关知识点"
            multiple
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleTagSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 筛选表单
const filterForm = reactive({
  examId: '',
  studentId: '',
  subject: '',
  errorType: ''
})

// 统计数据
const stats = reactive({
  totalCount: 156,
  conceptErrors: 42,
  calculationErrors: 38,
  carelessErrors: 35
})

// 表格数据
const loading = ref(false)
const wrongQuestions = ref([])
const selectedRows = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 选项数据
const examOptions = ref([
  { id: 1, name: '2024年春季期中考试' },
  { id: 2, name: '2024年3月月考' },
  { id: 3, name: '2024年上学期期末考试' }
])

const studentOptions = ref([
  { id: 1, name: '张三' },
  { id: 2, name: '李四' },
  { id: 3, name: '王五' }
])

const knowledgeOptions = ref([
  { value: 'algebra', label: '代数' },
  { value: 'geometry', label: '几何' },
  { value: 'function', label: '函数' },
  { value: 'probability', label: '概率统计' }
])

// 弹窗
const detailDialog = reactive({
  visible: false,
  data: null
})

const tagDialog = reactive({
  visible: false,
  currentId: null
})

const tagForm = reactive({
  errorType: '',
  analysis: '',
  knowledgePoints: []
})

// 获取错误类型标签
const getErrorTypeLabel = (type) => {
  const map = {
    concept: '概念理解错误',
    calculation: '计算错误',
    misreading: '审题错误',
    careless: '粗心大意',
    knowledge_gap: '知识点缺失',
    other: '其他'
  }
  return map[type] || type
}

const getErrorTypeType = (type) => {
  const map = {
    concept: 'danger',
    calculation: 'warning',
    misreading: 'info',
    careless: '',
    knowledge_gap: 'danger',
    other: 'info'
  }
  return map[type] || ''
}

// 加载数据
const loadData = () => {
  loading.value = true
  // 模拟数据
  setTimeout(() => {
    wrongQuestions.value = Array.from({ length: 20 }, (_, i) => ({
      id: i + 1,
      studentName: ['张三', '李四', '王五', '赵六'][i % 4],
      examName: '2024年春季期中考试',
      subject: ['数学', '语文', '英语'][i % 3],
      questionNumber: i + 1,
      questionContent: `这是第${i + 1}题的题目内容，涉及相关知识点...`,
      studentAnswer: ['A', 'B', 'C', 'D', '计算错误', '未作答'][i % 6],
      correctAnswer: ['B', 'C', 'A', 'D'][i % 4],
      score: i % 3 === 0 ? 0 : [2, 3, 5][i % 3],
      fullScore: 5,
      errorType: ['concept', 'calculation', 'careless', 'misreading'][i % 4],
      analysis: '',
      imageUrl: '',
      createdAt: '2024-03-15 14:30:00'
    }))
    pagination.total = 156
    loading.value = false
  }, 500)
}

// 事件处理
const handleFilterChange = () => {
  pagination.page = 1
  loadData()
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  filterForm.examId = ''
  filterForm.studentId = ''
  filterForm.subject = ''
  filterForm.errorType = ''
  handleSearch()
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  loadData()
}

const handlePageChange = (val) => {
  pagination.page = val
  loadData()
}

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleViewDetail = (row) => {
  detailDialog.data = row
  detailDialog.visible = true
}

const handleTag = (row) => {
  tagDialog.currentId = row.id
  tagForm.errorType = row.errorType
  tagForm.analysis = row.analysis || ''
  tagForm.knowledgePoints = []
  tagDialog.visible = true
}

const handleTagSubmit = () => {
  ElMessage.success('标注成功')
  tagDialog.visible = false
  loadData()
}

const handleBatchTag = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要标注的错题')
    return
  }
  ElMessage.info(`批量标注 ${selectedRows.value.length} 条记录`)
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除这条错题记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
    loadData()
  })
}

const handleExport = () => {
  ElMessage.success('开始导出错题本...')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.wrong-question-page {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.text-danger {
  color: #F56C6C;
  font-weight: bold;
}

.detail-content {
  padding: 10px;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #333;
  font-size: 14px;
  font-weight: bold;
}

.content-box {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
}

.student-answer {
  background: #fdf6ec;
  color: #e6a23c;
}

.correct-answer {
  background: #f0f9eb;
  color: #67c23a;
}

.analysis-text {
  margin-top: 10px;
  color: #666;
  line-height: 1.6;
}
</style>
