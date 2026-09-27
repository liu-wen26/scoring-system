<template>
  <div class="third-party-page">
    <div class="breadcrumb-bar">
      <el-button link @click="$router.push('/answer-card')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <span class="breadcrumb-text">答题卡模板 > 第三方答题卡</span>
    </div>

    <div class="filter-bar">
      <div class="filter-item">
        <span class="filter-label">年级：</span>
        <el-select v-model="filter.gradeId" placeholder="全部" clearable @change="loadTemplates">
          <el-option label="全部" :value="null" />
          <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">学科：</span>
        <el-select v-model="filter.subjectId" placeholder="全部" clearable @change="loadTemplates">
          <el-option label="全部" :value="null" />
          <el-option v-for="s in subjectList" :key="s.id" :label="s.subjectName" :value="s.id" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">上传时间：</span>
        <el-select v-model="filter.timeRange" placeholder="全部" clearable @change="loadTemplates">
          <el-option label="全部" :value="null" />
          <el-option label="最近一周" value="week" />
          <el-option label="最近一月" value="month" />
          <el-option label="最近三月" value="quarter" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">阅卷方式：</span>
        <el-select v-model="filter.markMode" placeholder="全部" clearable @change="loadTemplates">
          <el-option label="全部" :value="null" />
          <el-option label="网络阅卷" value="online" />
          <el-option label="有痕阅卷" value="offline" />
        </el-select>
      </div>
      <div class="filter-item">
        <el-checkbox v-model="filter.myCreated" @change="loadTemplates">我创建的</el-checkbox>
      </div>
      <div class="filter-actions">
        <el-button type="primary" @click="openUploadDialog">上传答题卡</el-button>
      </div>
    </div>

    <el-table :data="templates" v-loading="loading" stripe border>
      <el-table-column prop="templateName" label="模板名称" />
      <el-table-column prop="gradeName" label="年级" width="120" />
      <el-table-column prop="subjectName" label="学科" width="120" />
      <el-table-column prop="markMode" label="阅卷方式" width="120">
        <template #default="{ row }">
          {{ row.markMode === 'online' ? '网络阅卷' : '有痕阅卷' }}
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="上传时间" width="180" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" link @click="openPreview(row)">预览</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="uploadVisible" title="上传第三方答题卡" width="520px" :close-on-click-modal="false">
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="90px">
        <el-form-item label="所属年级" prop="gradeId">
          <el-select v-model="uploadForm.gradeId" placeholder="请选择年级" style="width: 100%">
            <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属学科" prop="subjectId">
          <el-select v-model="uploadForm.subjectId" placeholder="请选择学科" style="width: 100%">
            <el-option v-for="s in subjectList" :key="s.id" :label="s.subjectName" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="阅卷方式" prop="markMode">
          <el-radio-group v-model="uploadForm.markMode">
            <el-radio label="online">网络阅卷</el-radio>
            <el-radio label="offline">有痕阅卷</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="答题卡" prop="file">
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :limit="1"
            accept="image/*"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button type="primary">选择图片</el-button>
            <template #tip>
              <div class="upload-tip">支持 jpg、png 等图片格式，大小不超过 10MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">确定</el-button>
      </template>
    </el-dialog>

    <AnswerCardPreviewDialog v-model="previewVisible" :template-id="previewTemplateId" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAnswerCardTemplates,
  deleteAnswerCardTemplate,
  uploadThirdPartyTemplate
} from '@/api/answerCard'
import { getGrades, getSubjects } from '@/api/exam'
import AnswerCardPreviewDialog from './components/AnswerCardPreviewDialog.vue'

const loading = ref(false)
const uploading = ref(false)
const uploadVisible = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const templates = ref([])
const gradeList = ref([])
const subjectList = ref([])

const filter = reactive({
  gradeId: null,
  subjectId: null,
  timeRange: null,
  markMode: null,
  myCreated: false
})

const uploadForm = reactive({
  gradeId: null,
  subjectId: null,
  markMode: 'online',
  file: null
})
const uploadRules = {
  gradeId: [{ required: true, message: '请选择年级', trigger: 'change' }],
  subjectId: [{ required: true, message: '请选择学科', trigger: 'change' }],
  file: [{ required: true, message: '请选择答题卡图片', trigger: 'change' }]
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

const withinTimeRange = (createdAt, range) => {
  if (!range || !createdAt) return true
  const now = new Date().getTime()
  const t = new Date(createdAt).getTime()
  const day = 24 * 60 * 60 * 1000
  const map = { week: 7, month: 30, quarter: 90 }
  return now - t <= map[range] * day
}

const loadTemplates = async () => {
  loading.value = true
  try {
    const params = {
      templateType: 'third_party',
      ...(filter.gradeId && { gradeId: filter.gradeId }),
      ...(filter.subjectId && { subjectId: filter.subjectId }),
      ...(filter.markMode && { markMode: filter.markMode }),
      ...(filter.myCreated && { myCreated: true })
    }
    const res = await getAnswerCardTemplates(params)
    let list = res.items || []
    list = list.filter(t => withinTimeRange(t.createdAt, filter.timeRange))
    templates.value = list
  } catch (e) {
    ElMessage.error('加载第三方答题卡失败')
  } finally {
    loading.value = false
  }
}

const openUploadDialog = () => {
  uploadForm.gradeId = null
  uploadForm.subjectId = null
  uploadForm.markMode = 'online'
  uploadForm.file = null
  uploadRef.value?.clearFiles?.()
  uploadVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const handleFileRemove = () => {
  uploadForm.file = null
}

const submitUpload = async () => {
  try {
    await uploadFormRef.value.validate()
    if (!uploadForm.file) {
      ElMessage.warning('请选择答题卡图片')
      return
    }
    uploading.value = true
    const data = new FormData()
    data.append('file', uploadForm.file)
    data.append('gradeId', uploadForm.gradeId)
    data.append('subjectId', uploadForm.subjectId)
    data.append('markMode', uploadForm.markMode)
    await uploadThirdPartyTemplate(data)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    loadTemplates()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const openPreview = (row) => {
  previewTemplateId.value = row.id
  previewVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定删除该第三方答题卡吗？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteAnswerCardTemplate(row.id)
      ElMessage.success('删除成功')
      loadTemplates()
    })
    .catch(() => {})
}

onMounted(() => {
  loadGrades()
  loadSubjects()
  loadTemplates()
})
</script>

<style scoped>
.third-party-page {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}
.breadcrumb-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.breadcrumb-text {
  font-size: 15px;
  color: #606266;
}
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.filter-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}
.filter-actions {
  margin-left: auto;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
</style>
