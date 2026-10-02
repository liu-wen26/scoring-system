<template>
  <div class="scan-upload-page">
    <el-page-header title="扫描上传" @back="$router.back()" />
    
    <!-- 模式选择 -->
    <el-card class="mode-card">
      <template #header>
        <span>选择上传模式</span>
      </template>
      
      <el-radio-group v-model="uploadMode" size="large">
        <el-radio-button label="direct">
          <el-icon><Connection /></el-icon>
          扫描仪直连模式
        </el-radio-button>
        <el-radio-button label="pdf">
          <el-icon><Document /></el-icon>
          PDF 离线上传模式
        </el-radio-button>
      </el-radio-group>
      
      <div class="mode-description">
        <el-alert
          v-if="uploadMode === 'direct'"
          title="扫描仪直连模式"
          description="扫描仪连接阅卷系统，扫描后实时上传图片。适用于有网络环境的实时阅卷场景。"
          type="info"
          :closable="false"
          show-icon
        />
        <el-alert
          v-else
          title="PDF 离线上传模式"
          description="扫描仪单独工作，保存为 PDF 文件，事后批量上传到系统。适用于无网络环境的事后处理场景。"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
    </el-card>
    
    <!-- 考试选择 -->
    <el-card class="exam-card">
      <template #header>
        <span>考试信息</span>
      </template>
      
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择考试" required>
          <el-select v-model="form.examId" placeholder="请选择考试" style="width: 300px" @change="onExamChange">
            <el-option
              v-for="exam in examList"
              :key="exam.id"
              :label="exam.examName"
              :value="exam.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择科目" required>
          <el-select v-model="form.subjectId" placeholder="请选择科目" style="width: 300px" :disabled="!subjectList.length">
            <el-option
              v-for="subject in subjectList"
              :key="subject.id"
              :label="subject.subjectName"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 直连模式上传 -->
    <el-card v-if="uploadMode === 'direct'" class="upload-card">
      <template #header>
        <span>扫描上传</span>
      </template>

      <el-form :model="directForm" label-width="120px">
        <el-form-item label="关联模式">
          <el-radio-group v-model="directForm.bindingMode">
            <el-radio label="auto">自动识别考号匹配名册</el-radio>
            <el-radio label="sequential">按顺序关联</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <div class="direct-upload">
        <el-upload
          drag
          multiple
          accept="image/jpeg,image/jpg,image/png"
          action="/api/v1/scan/upload/image"
          :data="uploadData"
          :headers="uploadHeaders"
          :before-upload="beforeImageUpload"
          :on-success="handleImageSuccess"
          :on-error="handleUploadError"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽图片到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 JPG/PNG 格式，单个文件不超过 10MB
            </div>
          </template>
        </el-upload>
      </div>
    </el-card>
    
    <!-- PDF 模式上传 -->
    <el-card v-else class="upload-card">
      <template #header>
        <span>PDF 上传</span>
      </template>
      
      <el-form :model="pdfForm" label-width="120px">
        <el-form-item label="关联模式">
          <el-radio-group v-model="pdfForm.bindingMode">
            <el-radio label="auto">自动识别考号匹配名册</el-radio>
            <el-radio label="sequential">按顺序关联</el-radio>
            <el-radio label="manual">上传后自动关联</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="pdfForm.bindingMode === 'sequential'" label="学生顺序">
          <el-button type="primary" plain @click="showStudentDialog = true">
            选择学生 (已选 {{ selectedStudents.length }} 人)
          </el-button>
        </el-form-item>
      </el-form>
      
      <el-upload
        drag
        multiple
        accept=".pdf"
        action="/api/v1/scan/upload/pdf"
        :data="pdfUploadData"
        :headers="uploadHeaders"
        :before-upload="beforePDFUpload"
        :on-success="handlePDFSuccess"
        :on-error="handleUploadError"
      >
        <el-icon class="el-icon--upload"><Document /></el-icon>
        <div class="el-upload__text">
          拖拽 PDF 文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF 格式，单个文件不超过 100MB，最多 50 页
          </div>
        </template>
      </el-upload>
    </el-card>
    
    <!-- 上传结果 -->
    <el-card v-if="uploadResults.length > 0" class="result-card">
      <template #header>
        <span>上传结果</span>
      </template>
      
      <el-table :data="uploadResults">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.success ? 'success' : 'danger'">
              {{ scope.row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="信息" />
      </el-table>
    </el-card>
    
    <!-- 学生选择对话框 -->
    <el-dialog v-model="showStudentDialog" title="选择学生" width="600px">
      <el-transfer
        v-model="selectedStudents"
        :data="studentOptions"
        :titles="['未选择', '已选择']"
        filterable
      />
      <template #footer>
        <el-button @click="showStudentDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmStudents">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getExams } from '@/api/exam'
import { getStudents } from '@/api/user'

const route = useRoute()
const userStore = useUserStore()

const queryExamId = route.query.examId ? Number(route.query.examId) : null
const querySubjectId = route.query.subjectId ? Number(route.query.subjectId) : null

// 上传模式
const uploadMode = ref('pdf')

// 表单数据
const form = reactive({
  examId: null,
  subjectId: null
})

const pdfForm = reactive({
  bindingMode: 'auto'
})

const directForm = reactive({
  bindingMode: 'auto'
})

// 列表数据
const examList = ref([])
const subjectList = ref([])

// 上传相关
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

const uploadData = computed(() => ({
  exam_id: form.examId,
  subject_id: form.subjectId,
  scan_mode: 'direct',
  binding_mode: directForm.bindingMode
}))

const pdfUploadData = computed(() => {
  const data = {
    exam_id: form.examId,
    subject_id: form.subjectId,
    binding_mode: pdfForm.bindingMode
  }
  if (pdfForm.bindingMode === 'sequential') {
    data.student_list = JSON.stringify(
      selectedStudents.value
        .map(id => studentOptions.value.find(s => s.key === id))
        .filter(Boolean)
        .map(s => ({ id: s.key, name: s.label }))
    )
  }
  return data
})

const uploadResults = ref([])

// 学生选择
const showStudentDialog = ref(false)
const selectedStudents = ref([])
const studentOptions = ref([])

// 上传前校验
const beforeImageUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/jpg'
  const isPNG = file.type === 'image/png'
  const isLt10M = file.size / 1024 / 1024 < 10
  
  if (!isJPG && !isPNG) {
    ElMessage.error('只支持 JPG/PNG 格式图片')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  
  if (!form.examId || !form.subjectId) {
    ElMessage.error('请先选择考试和科目')
    return false
  }
  
  return true
}

const beforePDFUpload = (file) => {
  const isPDF = file.name.endsWith('.pdf')
  const isLt100M = file.size / 1024 / 1024 < 100
  
  if (!isPDF) {
    ElMessage.error('只支持 PDF 格式文件')
    return false
  }
  if (!isLt100M) {
    ElMessage.error('PDF 文件大小不能超过 100MB')
    return false
  }
  
  if (!form.examId || !form.subjectId) {
    ElMessage.error('请先选择考试和科目')
    return false
  }
  
  return true
}

// 上传回调
const handleImageSuccess = (response, file) => {
  uploadResults.value.push({
    filename: file.name,
    success: true,
    message: '上传成功'
  })
  ElMessage.success('图片上传成功')
}

const handlePDFSuccess = (response, file) => {
  uploadResults.value.push({
    filename: file.name,
    success: true,
    message: `上传成功，共 ${response.total_pages} 页`
  })
  ElMessage.success('PDF 上传成功')
}

const handleUploadError = (error, file) => {
  uploadResults.value.push({
    filename: file.name,
    success: false,
    message: error.message || '上传失败'
  })
  ElMessage.error('上传失败')
}

const confirmStudents = () => {
  showStudentDialog.value = false
  ElMessage.success(`已选择 ${selectedStudents.value.length} 名学生`)
}

// 考试切换：按所选考试加载其科目
const onExamChange = (examId) => {
  form.subjectId = null
  subjectList.value = []
  const exam = examList.value.find(e => e.id === examId)
  subjectList.value = (exam?.subjects || []).map(s => ({
    id: s.subjectId,
    subjectName: s.subjectName
  }))
  if (subjectList.value.length === 1) {
    form.subjectId = subjectList.value[0].id
  }
}

// 获取考试列表
const fetchExams = async () => {
  try {
    const res = await getExams({ limit: 100 })
    examList.value = res.items || []
    if (queryExamId) {
      const target = examList.value.find(e => e.id === queryExamId)
      if (target) {
        form.examId = queryExamId
        onExamChange(queryExamId)
        if (querySubjectId && subjectList.value.some(s => s.id === querySubjectId)) {
          form.subjectId = querySubjectId
        }
      }
    }
  } catch (error) {
    console.error('获取考试列表失败:', error)
  }
}

// 获取学生列表（用于按顺序关联）
const fetchStudents = async () => {
  try {
    const res = await getStudents({ limit: 1000 })
    studentOptions.value = (res.items || []).map(s => ({
      key: s.id,
      label: `${s.realName}${s.studentNo ? ' (' + s.studentNo + ')' : ''}`
    }))
  } catch (error) {
    console.error('获取学生列表失败:', error)
  }
}

onMounted(() => {
  fetchExams()
  fetchStudents()
})
</script>

<style scoped>
.scan-upload-page {
  padding: 0;
}

.mode-card,
.exam-card,
.upload-card,
.result-card {
  margin-top: 20px;
}

.mode-description {
  margin-top: 20px;
}

.direct-upload {
  padding: 20px;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
