<template>
  <div class="answer-card-page">
    <div class="page-header">
      <h2 class="page-title">答题卡制作</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建答题卡
        </el-button>
        <el-button type="info" plain @click="$router.push('/answer-card/third-party')">第三方制卡</el-button>
        <el-button type="info" plain>题库制卡</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="filter.gradeId" placeholder="全部年级" clearable @change="loadTemplates">
        <el-option label="全部年级" :value="null" />
        <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
      </el-select>
      <el-select v-model="filter.subjectId" placeholder="全部学科" clearable @change="loadTemplates">
        <el-option label="全部学科" :value="null" />
        <el-option v-for="s in subjectList" :key="s.id" :label="s.subjectName" :value="s.id" />
      </el-select>
    </div>

    <el-table :data="templates" v-loading="loading" stripe border>
      <el-table-column prop="templateName" label="模板名称" />
      <el-table-column prop="gradeName" label="年级" width="120" />
      <el-table-column prop="subjectName" label="学科" width="120" />
      <el-table-column prop="createdAt" label="创建时间" width="180" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="success" link @click="handleDownload(row)">下载</el-button>
          <el-dropdown trigger="click" @command="(cmd) => handleMore(cmd, row)">
            <el-button type="primary" link>
              更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="preview">预览</el-dropdown-item>
                <el-dropdown-item command="copy">复制</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createVisible" title="创建答题卡" width="420px" :close-on-click-modal="false">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="90px">
        <el-form-item label="所属年级" prop="gradeId">
          <el-select v-model="createForm.gradeId" placeholder="请选择年级" style="width: 100%">
            <el-option label="请选择年级" :value="null" disabled />
            <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属科目" prop="subjectId">
          <el-select v-model="createForm.subjectId" placeholder="请选择科目" style="width: 100%">
            <el-option label="请选择科目" :value="null" disabled />
            <el-option v-for="s in subjectList" :key="s.id" :label="s.subjectName" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>

    <AnswerCardPreviewDialog v-model="previewVisible" :template-id="previewTemplateId" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAnswerCardTemplates,
  getAnswerCardTemplate,
  createAnswerCardTemplate,
  deleteAnswerCardTemplate
} from '@/api/answerCard'
import { getGrades, getSubjects } from '@/api/exam'
import AnswerCardPreviewDialog from './components/AnswerCardPreviewDialog.vue'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const templates = ref([])
const gradeList = ref([])
const subjectList = ref([])
const filter = reactive({
  gradeId: null,
  subjectId: null
})

const createVisible = ref(false)
const createFormRef = ref(null)
const createForm = reactive({
  gradeId: null,
  subjectId: null
})
const createRules = {
  gradeId: [{ required: true, message: '请选择年级', trigger: 'change' }],
  subjectId: [{ required: true, message: '请选择科目', trigger: 'change' }]
}

const previewVisible = ref(false)
const previewTemplateId = ref(null)

const loadGrades = async () => {
  try {
    gradeList.value = await getGrades()
  } catch (e) {
    console.error(e)
  }
}

const loadSubjects = async () => {
  try {
    subjectList.value = await getSubjects()
  } catch (e) {
    console.error(e)
  }
}

const loadTemplates = async () => {
  loading.value = true
  try {
    const res = await getAnswerCardTemplates({ templateType: 'custom' })
    let list = res.items || []
    if (filter.gradeId) {
      list = list.filter(t => t.gradeId === filter.gradeId)
    }
    if (filter.subjectId) {
      list = list.filter(t => t.subjectId === filter.subjectId)
    }
    templates.value = list
  } catch (e) {
    ElMessage.error('加载答题卡模板失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  createForm.gradeId = null
  createForm.subjectId = null
  createVisible.value = true
}

const submitCreate = async () => {
  try {
    await createFormRef.value.validate()
    creating.value = true
    const res = await createAnswerCardTemplate({
      gradeId: createForm.gradeId,
      subjectId: createForm.subjectId
    })
    createVisible.value = false
    ElMessage.success('创建成功')
    router.push(`/answer-card/editor/${res.id}`)
  } catch (e) {
    if (e?.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  } finally {
    creating.value = false
  }
}

const handleEdit = (row) => {
  router.push(`/answer-card/editor/${row.id}`)
}

const openPreview = (row) => {
  previewTemplateId.value = row.id
  previewVisible.value = true
}

const handleDownload = (row) => {
  openPreview(row)
}

const handleCopy = async (row) => {
  try {
    const tpl = await getAnswerCardTemplate(row.id)
    await createAnswerCardTemplate({
      templateName: `${tpl.templateName || '答题卡'} 副本`,
      gradeId: tpl.gradeId,
      subjectId: tpl.subjectId,
      width: tpl.width,
      height: tpl.height,
      config: tpl.config
    })
    ElMessage.success('复制成功')
    loadTemplates()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '复制失败')
  }
}

const handleMore = (cmd, row) => {
  if (cmd === 'preview') {
    openPreview(row)
  } else if (cmd === 'copy') {
    handleCopy(row)
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定删除该答题卡吗？', '提示', { type: 'warning' })
      .then(async () => {
        await deleteAnswerCardTemplate(row.id)
        ElMessage.success('删除成功')
        loadTemplates()
      })
      .catch(() => {})
  }
}

onMounted(() => {
  loadGrades()
  loadSubjects()
  loadTemplates()
})
</script>

<style scoped>
.answer-card-page {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
