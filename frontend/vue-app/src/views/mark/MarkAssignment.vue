<template>
  <div class="mark-assignment-page">
    <!-- 顶部考试信息 -->
    <div class="exam-header-bar">
      <el-page-header title="阅卷分工" @back="$router.back()" />
      <div class="exam-meta">
        <el-tag v-if="examStatus" :type="getStatusType(examStatus)">{{ getStatusText(examStatus) }}</el-tag>
        <span class="meta-item">{{ examGrade }}</span>
        <span class="meta-item">{{ subjectName }}</span>
      </div>
    </div>

    <div class="assignment-layout">
      <!-- 左侧：选题 -->
      <el-card class="question-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span class="panel-title">批阅任务</span>
          </div>
        </template>
        <div class="panel-desc">请选择题号/题组并新建批阅任务（可多选）</div>

        <div class="question-grid">
          <div
            v-for="q in questionList"
            :key="q.questionNo"
            class="question-card"
            :class="{ selected: selectedQuestions.includes(q.questionNo) }"
            @click="toggleQuestion(q.questionNo)"
          >
            <div class="question-thumb">
              <img v-if="q.previewUrl" :src="q.previewUrl" />
              <div v-else class="thumb-placeholder">题号<br>{{ q.questionNo }}</div>
            </div>
            <div class="question-label">{{ q.displayNo }}</div>
          </div>
        </div>

        <div v-if="selectedQuestions.length > 0" class="create-form">
          <el-divider />
          <div class="form-title">新建批阅任务（已选 {{ selectedQuestions.length }} 题）</div>
          <el-form :model="createForm" label-width="90px">
            <el-form-item label="批阅教师">
              <el-select
                v-model="createForm.userIds"
                multiple
                placeholder="选择阅卷教师"
                style="width: 100%"
              >
                <el-option
                  v-for="user in userList"
                  :key="user.id"
                  :label="user.username"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="批阅方式">
              <el-select v-model="createForm.markMode" placeholder="批阅方式" style="width: 100%">
                <el-option label="单批" value="single" />
                <el-option label="双批" value="double" />
                <el-option label="多批" value="multiple" />
              </el-select>
            </el-form-item>
            <el-form-item label="分配方式">
              <el-select v-model="createForm.allocationMode" placeholder="分配方式" style="width: 100%">
                <el-option label="效率优先" value="efficiency" />
                <el-option label="平均分配" value="balance" />
                <el-option label="随机分配" value="random" />
              </el-select>
            </el-form-item>
            <el-form-item label="分配份数">
              <div class="auto-papers-tip">
                系统将根据实际扫描答题卡数量自动分配
                <span v-if="examTotalStudents">（当前考试参考人数：{{ examTotalStudents }}）</span>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleCreate">创建批阅任务</el-button>
              <el-button @click="selectedQuestions = []">取消选择</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 右侧：任务列表 -->
      <el-card class="task-panel" shadow="never">
        <template #header>
          <div class="panel-header">
            <span class="panel-title">批阅任务列表</span>
            <div class="toolbar">
              <el-button type="danger" text :disabled="!selectedTaskIds.length" @click="handleDeleteTasks">
                <el-icon><Delete /></el-icon>删除批阅任务
              </el-button>
              <el-button text :disabled="!taskList.length" @click="handleClearRecords">
                <el-icon><DeleteFilled /></el-icon>清空批阅记录
              </el-button>
              <el-button text :disabled="!selectedTaskIds.length" @click="handleEditTeachers">
                <el-icon><Edit /></el-icon>修改批阅教师
              </el-button>
              <el-button text :disabled="!selectedTaskIds.length" @click="handleEditAllocationMode">
                <el-icon><Setting /></el-icon>修改阅卷分配方式
              </el-button>
              <el-button text @click="handleSetArbitration">
                <el-icon><Aim /></el-icon>设置仲裁
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="taskList"
          v-loading="loading"
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="45" />
          <el-table-column prop="questionNoText" label="题号" min-width="120" />
          <el-table-column prop="markModeText" label="批阅方式" width="100" />
          <el-table-column label="批阅教师" min-width="200">
            <template #default="{ row }">
              <div class="teacher-list">
                <span class="teacher-count">{{ row.userNames.length }}人</span>
                <span class="teacher-names">{{ row.userNames.join(' ') }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="allocationModeText" label="阅卷分配方式" width="130">
            <template #default="{ row }">
              <span class="allocation-tag">
                <el-icon><Connection /></el-icon>
                {{ row.allocationModeText }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="140">
            <template #default="{ row }">
              <el-progress :percentage="row.progress" :status="row.progress >= 100 ? 'success' : ''" />
            </template>
          </el-table-column>
          <el-table-column prop="statusText" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="getTaskStatusType(row.status)">{{ row.statusText }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleReuse(row)">复用</el-button>
              <el-button link type="warning" size="small" @click="handlePause(row)">暂停</el-button>
              <el-dropdown size="small" trigger="click">
                <el-button link type="info" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="handleEditRow(row)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="handleDeleteRow(row)">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 修改教师弹窗 -->
    <el-dialog v-model="editTeachersVisible" title="修改批阅教师" width="400px">
      <el-select v-model="editForm.userIds" multiple placeholder="选择教师" style="width: 100%">
        <el-option v-for="user in userList" :key="user.id" :label="user.username" :value="user.id" />
      </el-select>
      <template #footer>
        <el-button @click="editTeachersVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditTeachers">确定</el-button>
      </template>
    </el-dialog>

    <!-- 修改分配方式弹窗 -->
    <el-dialog v-model="editModeVisible" title="修改阅卷分配方式" width="400px">
      <el-select v-model="editForm.allocationMode" placeholder="分配方式" style="width: 100%">
        <el-option label="效率优先" value="efficiency" />
        <el-option label="平均分配" value="balance" />
        <el-option label="随机分配" value="random" />
      </el-select>
      <template #footer>
        <el-button @click="editModeVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEditMode">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExam } from '@/api/exam'
import { getAnswerCardConfig } from '@/api/answerCard'
import { markApi } from '@/api/mark'
import { getUsers } from '@/api/user'

const route = useRoute()
const router = useRouter()

const examId = Number(route.query.examId)
const subjectId = Number(route.query.subjectId)

const examStatus = ref('')
const examGrade = ref('')
const subjectName = ref('')
const examTotalStudents = ref(0)
const userList = ref([])
const taskList = ref([])
const questionList = ref([])
const selectedQuestions = ref([])
const selectedTaskIds = ref([])
const loading = ref(false)

const createForm = reactive({
  userIds: [],
  markMode: 'single',
  allocationMode: 'efficiency',
  totalPapers: 0
})

const editForm = reactive({
  userIds: [],
  allocationMode: 'efficiency'
})
const editTeachersVisible = ref(false)
const editModeVisible = ref(false)

const userMap = computed(() => {
  const map = {}
  userList.value.forEach(u => { map[u.id] = u.username })
  return map
})

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

const fetchExamInfo = async () => {
  try {
    const res = await getExam(examId)
    examStatus.value = res.status
    examGrade.value = res.grade
    examTotalStudents.value = res.totalStudents || 0
    const subject = res.subjects?.find(s => s.subjectId === subjectId)
    subjectName.value = subject?.subjectName || ''
  } catch (error) {
    ElMessage.error('加载考试信息失败')
  }
}

const fetchUsers = async () => {
  try {
    const res = await getUsers({ limit: 1000 })
    userList.value = res || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const fetchAnswerCardConfig = async () => {
  try {
    const res = await getAnswerCardConfig(examId, subjectId)
    const regions = res.regions || []
    const subjectiveRegions = regions.filter(r => r.type === 'subjective' || r.type === 'subjective_region')
    const pagePreviews = res.pagePreviews || (res.templateImage ? [res.templateImage] : [])

    // 按 questionNo 去重并生成列表
    const seen = new Set()
    questionList.value = subjectiveRegions
      .filter(r => {
        const no = String(r.questionNo || r.question_no || '')
        if (!no || seen.has(no)) return false
        seen.add(no)
        return true
      })
      .map((r, idx) => {
        const no = String(r.questionNo || r.question_no || '')
        const groupPrefix = r.page ? '' : ''
        return {
          questionNo: no,
          displayNo: groupPrefix + no,
          score: r.score || 0,
          page: r.page || 1,
          previewUrl: pagePreviews[(r.page || 1) - 1] || pagePreviews[0] || null
        }
      })
      .sort((a, b) => {
        const na = parseInt(a.questionNo) || 0
        const nb = parseInt(b.questionNo) || 0
        return na - nb
      })
  } catch (error) {
    console.error('加载答题卡配置失败:', error)
  }
}

const fetchAllocations = async () => {
  loading.value = true
  try {
    const res = await markApi.getAllocations({ examId, subjectId })
    taskList.value = (res.items || [])
      .filter(item => {
        const nos = item.questionNos || []
        return Array.isArray(nos) && nos.length > 0 && nos.every(n => n != null && String(n) !== '')
      })
      .map(item => {
        const uids = item.userIds || (item.userId ? [item.userId] : [])
        const names = uids.map(id => userMap.value[id] || `用户${id}`)
        const nos = item.questionNos || []
        return {
          ...item,
          questionNoText: nos.join('、'),
          markModeText: markModeMap[item.markMode] || '单批',
          userNames: names,
          allocationModeText: allocationModeMap[item.allocationMode] || '效率优先',
          statusText: statusMap[item.status]?.text || item.status,
          progress: item.progress || 0
        }
      })
  } catch (error) {
    ElMessage.error('加载分工列表失败')
  } finally {
    loading.value = false
  }
}

const toggleQuestion = (questionNo) => {
  const idx = selectedQuestions.value.indexOf(questionNo)
  if (idx > -1) {
    selectedQuestions.value.splice(idx, 1)
  } else {
    selectedQuestions.value.push(questionNo)
  }
}

const handleCreate = async () => {
  if (selectedQuestions.value.length === 0) {
    ElMessage.warning('请至少选择一道题')
    return
  }
  if (createForm.userIds.length === 0) {
    ElMessage.warning('请选择批阅教师')
    return
  }
  try {
    await markApi.createAllocation({
      examId,
      subjectId,
      questionType: 'subjective',
      questionNos: [...selectedQuestions.value],
      userIds: [...createForm.userIds],
      markMode: createForm.markMode,
      allocationMode: createForm.allocationMode,
      totalPapers: 0
    })
    ElMessage.success('批阅任务创建成功')
    selectedQuestions.value = []
    createForm.userIds = []
    createForm.totalPapers = 0
    await fetchAllocations()
  } catch (error) {
    ElMessage.error('创建批阅任务失败')
  }
}

const handleSelectionChange = (selection) => {
  selectedTaskIds.value = selection.map(row => row.id)
}

const handleDeleteTasks = async () => {
  if (selectedTaskIds.value.length === 0) return
  try {
    await ElMessageBox.confirm('确定删除选中的批阅任务吗？', '提示', { type: 'warning' })
    await markApi.batchDeleteAllocations(selectedTaskIds.value)
    ElMessage.success('删除成功')
    selectedTaskIds.value = []
    await fetchAllocations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleClearRecords = () => {
  ElMessageBox.confirm('确定清空所有批阅记录吗？', '提示', { type: 'warning' }).then(() => {
    ElMessage.success('已清空')
  })
}

const handleEditTeachers = () => {
  editForm.userIds = []
  editTeachersVisible.value = true
}
const confirmEditTeachers = () => {
  ElMessage.success('批阅教师已修改')
  editTeachersVisible.value = false
}

const handleEditAllocationMode = () => {
  editForm.allocationMode = 'efficiency'
  editModeVisible.value = true
}
const confirmEditMode = () => {
  ElMessage.success('分配方式已修改')
  editModeVisible.value = false
}

const handleSetArbitration = () => {
  ElMessage.info('仲裁设置功能待完善')
}

const handleReuse = (row) => {
  ElMessage.success(`已复用任务：${row.questionNoText}`)
}

const handlePause = (row) => {
  row.status = row.status === 'paused' ? 'pending' : 'paused'
  row.statusText = statusMap[row.status]?.text || row.status
  ElMessage.success('状态已更新')
}

const handleEditRow = (row) => {
  ElMessage.info('编辑单行功能待完善')
}

const handleDeleteRow = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该任务吗？', '提示', { type: 'warning' })
    await markApi.deleteAllocation(row.id)
    ElMessage.success('删除成功')
    await fetchAllocations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
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

const getTaskStatusType = (status) => {
  return statusMap[status]?.type || 'info'
}

onMounted(async () => {
  if (!examId || !subjectId) {
    ElMessage.warning('缺少考试或学科参数')
    router.back()
    return
  }
  await fetchExamInfo()
  await fetchUsers()
  await fetchAnswerCardConfig()
  await fetchAllocations()
})
</script>

<style scoped>
.mark-assignment-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.exam-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.exam-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-item {
  font-size: 14px;
  color: #606266;
}

.assignment-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.question-panel {
  width: 360px;
  flex-shrink: 0;
}

.task-panel {
  flex: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-weight: 500;
  font-size: 16px;
}

.panel-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.toolbar {
  display: flex;
  gap: 8px;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.question-card {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  background: #fff;
}

.question-card:hover {
  border-color: #409eff;
}

.question-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.question-thumb {
  width: 100%;
  height: 80px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.question-thumb img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.thumb-placeholder {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.question-label {
  margin-top: 8px;
  font-size: 13px;
  color: #303133;
}

.create-form {
  margin-top: 16px;
}

.form-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}

.teacher-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.teacher-count {
  color: #409eff;
  font-size: 13px;
}

.teacher-names {
  font-size: 13px;
  color: #606266;
}

.allocation-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  font-size: 13px;
}

.auto-papers-tip {
  font-size: 13px;
  color: #606266;
  line-height: 32px;
}
</style>
