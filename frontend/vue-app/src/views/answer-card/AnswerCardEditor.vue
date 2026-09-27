<template>
  <div class="answer-card-editor">
    <div class="editor-header">
      <div class="header-left">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <span class="school-name">{{ schoolName }}</span>
      </div>
      <div class="header-actions">
        <el-button @click="handlePreview">预览</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>

    <div class="editor-body">
      <div class="preview-area">
        <AnswerCardPaper v-model:config="config" ref="paperRef" @edit-student-info="openStudentInfoDialog" />
      </div>

      <div class="settings-panel">
        <div class="panel-title">基本设置</div>
        <div class="setting-row full">
          <span class="setting-label">学校名称：</span>
          <el-input v-model="config.schoolName" size="small" placeholder="请输入学校名称" style="flex: 1" />
        </div>
        <div class="setting-row">
          <span class="setting-label">应用场景：</span>
          <el-radio-group v-model="config.scenario" size="small">
            <el-radio-button label="exam">考试</el-radio-button>
            <el-radio-button label="practice">练习</el-radio-button>
          </el-radio-group>
        </div>
        <div class="setting-row">
          <span class="setting-label">阅卷方式：</span>
          <el-radio-group v-model="config.markMode" size="small">
            <el-radio-button label="online">网络阅卷</el-radio-button>
            <el-radio-button label="offline">有痕阅卷</el-radio-button>
          </el-radio-group>
        </div>
        <div class="setting-row vertical">
          <span class="setting-label">考号识别：</span>
          <el-checkbox-group v-model="config.studentNumberTypes" size="small">
            <el-checkbox label="bubble">考号填涂</el-checkbox>
            <el-checkbox label="qrcode">二维码</el-checkbox>
            <el-checkbox label="barcode">条形码</el-checkbox>
            <el-checkbox label="handwrite">手写考号</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="setting-row switches">
          <span class="setting-label">注意事项：</span>
          <el-switch v-model="config.showNotes" />
          <span class="setting-label ml">缺考标记：</span>
          <el-switch v-model="config.showAbsentMark" />
        </div>

        <div class="panel-title">布局设置</div>
        <div class="setting-row">
          <span class="setting-label">答题卡布局：</span>
          <el-radio-group v-model="config.layout" size="small">
            <el-radio-button label="one">一栏</el-radio-button>
          </el-radio-group>
        </div>
        <div class="setting-row">
          <span class="setting-label">答题卡颜色：</span>
          <el-radio-group v-model="config.color" size="small">
            <el-radio-button label="black">黑色</el-radio-button>
            <el-radio-button label="red">红色</el-radio-button>
          </el-radio-group>
        </div>
        <div class="setting-row switches">
          <span class="setting-label">密封线：</span>
          <el-switch v-model="config.sealLine" />
          <span class="setting-label ml">答题卡分区：</span>
          <el-switch v-model="config.partition" />
        </div>

        <div class="panel-title">
          <span>详细设置</span>
        </div>
        <div class="section-btns">
          <el-button size="small" @click="openSectionDialog('choice')">+ 客观题</el-button>
          <el-button size="small" @click="openSectionDialog('fill')">+ 填空题</el-button>
          <el-button size="small" @click="openSectionDialog('subjective')">+ 解答题</el-button>
          <el-button size="small" @click="openSectionDialog('composition_en')">+ 作文(英)</el-button>
          <el-button size="small" @click="openSectionDialog('composition_cn')">+ 作文(语)</el-button>
          <el-button size="small" @click="openSectionDialog('blank')">+ 非作答区</el-button>
        </div>

        <div class="section-list">
          <div v-for="(section, idx) in config.sections" :key="section.id || idx" class="section-item">
            <span>
              <el-tag size="small" :type="section.type === 'choice' ? 'primary' : section.type === 'subjective' ? 'success' : section.type === 'fill' ? 'warning' : ''" style="margin-right: 6px">{{ sectionTypeTitle(section.type) }}</el-tag>
              {{ section.groupNo ? section.groupNo + '、' : '' }}{{ section.title }}（{{ section.count }}题/{{ section.score }}分）
            </span>
            <div class="section-actions">
              <el-button type="primary" link size="small" @click="editSection(idx)">编辑</el-button>
              <el-button type="danger" link size="small" @click="removeSection(idx)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AnswerCardPreviewDialog v-model="previewVisible" :config="config" :template-name="templateName.value || config.title" />

    <el-dialog v-model="sectionDialogVisible" :title="sectionDialogTitle" width="640px" :close-on-click-modal="false">
      <el-form :model="sectionForm" :rules="sectionRules" ref="sectionFormRef" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="大题题号" prop="groupNo">
              <el-select v-model="sectionForm.groupNo" style="width: 100%">
                <el-option
                  v-for="no in groupNoOptions"
                  :key="no"
                  :label="no"
                  :value="no"
                  :disabled="usedGroupNos.includes(no)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题目名称" prop="title">
              <el-input v-model="sectionForm.title" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 客观题详细设置 -->
        <template v-if="sectionForm.type === 'choice'">
          <el-form-item label="选项方向">
            <el-radio-group v-model="sectionForm.optionDirection">
              <el-radio label="horizontal">横向</el-radio>
              <el-radio label="vertical">竖向</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="排列方式">
            <el-radio-group v-model="sectionForm.arrangement">
              <el-radio label="horizontal">横排</el-radio>
              <el-radio label="vertical">竖排</el-radio>
              <el-radio label="mixed">混合排</el-radio>
            </el-radio-group>
          </el-form-item>

          <div class="quick-add-bar simple">
            <el-select v-model="quickAdd.subType" style="width: 100px">
              <el-option label="单选题" value="single" />
              <el-option label="多选题" value="multiple" />
              <el-option label="判断题" value="judge" />
            </el-select>
            <el-input v-model="quickAdd.count" type="number" min="2" max="10" class="num-input" />
            <span class="quick-text">个选项 从</span>
            <el-input v-model="quickAdd.startNo" type="number" min="1" max="999" class="num-input" />
            <span class="quick-text">到</span>
            <el-input v-model="quickAdd.endNo" type="number" min="1" max="999" class="num-input" />
            <span class="quick-text">题</span>
            <el-input v-model="quickAdd.score" type="number" min="0" max="100" step="0.5" class="num-input" />
            <span class="quick-text">分/题</span>
            <el-button type="primary" @click="addChoiceSubQuestions">添加</el-button>
          </div>

          <el-table :data="sectionForm.subQuestions" border size="small" style="margin-top: 12px">
            <el-table-column prop="questionNo" label="题号" width="90">
              <template #default="{ row }">
                <el-input v-model="row.questionNo" type="number" size="small" class="table-num-input" />
              </template>
            </el-table-column>
            <el-table-column prop="score" label="满分" width="100">
              <template #default="{ row }">
                <el-input v-model="row.score" type="number" min="0" max="100" step="0.5" size="small" class="table-num-input" />
              </template>
            </el-table-column>
            <el-table-column prop="subType" label="小题题型" width="120">
              <template #default="{ row }">
                <el-select v-model="row.subType" size="small" style="width: 90px" @change="onSubTypeChange(row)">
                  <el-option label="单选题" value="single" />
                  <el-option label="多选题" value="multiple" />
                  <el-option label="判断题" value="judge" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="optionCount" label="选项个数" width="110">
              <template #default="{ row }">
                <el-input v-if="row.subType !== 'judge'" v-model="row.optionCount" type="number" min="2" max="10" size="small" class="table-num-input" />
                <span v-else>—</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeSubQuestion($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="sectionForm.subQuestions.length === 0" class="empty-table-tip">暂无数据</div>
        </template>

        <!-- 解答题详细设置 -->
        <template v-if="sectionForm.type === 'subjective'">
          <el-form-item label="题目内容">
            <RichTextEditor v-model="sectionForm.content" />
            <div class="form-tip">可在此编辑解答题的题干、答题要求等内容</div>
          </el-form-item>
          <div class="sub-header-row">
            <el-button type="primary" link @click="addSubjectiveSubQuestion">+ 添加小题</el-button>
          </div>
          <el-table :data="sectionForm.subQuestions" border size="small">
            <el-table-column prop="questionNo" label="题号" width="100">
              <template #default="{ row }">
                <el-input v-model="row.questionNo" type="number" size="small" class="table-num-input" />
              </template>
            </el-table-column>
            <el-table-column prop="score" label="满分" width="100">
              <template #default="{ row }">
                <el-input v-model="row.score" type="number" min="0" max="100" step="0.5" size="small" class="table-num-input" />
              </template>
            </el-table-column>
            <el-table-column label="答题线" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.hasAnswerLine" active-text="有" inactive-text="无" inline-prompt />
              </template>
            </el-table-column>
            <el-table-column prop="lineCount" label="答题线行数" width="130">
              <template #default="{ row }">
                <el-input v-if="row.hasAnswerLine" v-model="row.lineCount" type="number" min="1" max="100" size="small" class="table-num-input" />
                <span v-else>—</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeSubQuestion($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="sectionForm.subQuestions.length === 0" class="empty-table-tip">暂无数据</div>
        </template>

        <!-- 填空题/作文/非作答区保持原简单配置 -->
        <template v-if="['fill','composition_en','composition_cn','blank'].includes(sectionForm.type)">
          <el-form-item label="题数">
            <el-input-number v-model="sectionForm.count" :min="1" :max="200" style="width: 100%" />
          </el-form-item>
          <el-form-item label="分值">
            <el-input-number v-model="sectionForm.score" :min="0" :max="100" style="width: 100%" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="closeSectionDialog">取消</el-button>
        <el-button type="primary" @click="submitSection">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="studentInfoDialogVisible" title="编辑考生信息" width="480px" :close-on-click-modal="false">
      <el-form label-width="90px">
        <el-form-item label="考号位数">
          <el-input-number v-model="studentInfoForm.digits" :min="1" :max="20" style="width: 100%" />
        </el-form-item>
        <div class="info-fields-label">信息点：</div>
        <div v-for="(field, idx) in studentInfoForm.fields" :key="field.id || idx" class="info-field-row">
          <el-input v-model="field.label" placeholder="标签，如：姓名" size="small" style="width: 100px" />
          <el-input v-model="field.placeholder" placeholder="占位符，如：________" size="small" style="flex: 1" />
          <el-button type="danger" link size="small" @click="removeInfoField(idx)">删除</el-button>
        </div>
        <el-button type="primary" link size="small" @click="addInfoField">+ 添加信息点</el-button>
      </el-form>
      <template #footer>
        <el-button @click="studentInfoDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitStudentInfo">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAnswerCardTemplate, updateAnswerCardTemplate } from '@/api/answerCard'
import AnswerCardPaper from './components/AnswerCardPaper.vue'
import AnswerCardPreviewDialog from './components/AnswerCardPreviewDialog.vue'
import RichTextEditor from './components/RichTextEditor.vue'

const route = useRoute()
const router = useRouter()
const templateId = Number(route.params.id)

const loading = ref(false)
const saving = ref(false)
const schoolName = ref('学校名称')
const paperRef = ref(null)
const previewVisible = ref(false)

const defaultStudentInfo = () => ({
  fields: [
    { id: 'name', label: '姓名', placeholder: '________' },
    { id: 'class', label: '班级', placeholder: '________' }
  ]
})

const defaultConfig = () => ({
  title: '',
  schoolName: '佛山市南海区狮山镇官窑初级中学',
  scenario: 'exam',
  markMode: 'online',
  studentNumberTypes: ['bubble'],
  showNotes: true,
  showAbsentMark: true,
  layout: 'one',
  color: 'black',
  sealLine: false,
  partition: false,
  digits: 8,
  studentInfo: defaultStudentInfo(),
  sections: []
})

const config = reactive(defaultConfig())
const templateName = ref('')

watch(() => config.layout, (val) => {
  if (val !== 'one') {
    config.layout = 'one'
  }
})

const removeSection = (idx) => {
  config.sections.splice(idx, 1)
}

const sectionDialogVisible = ref(false)
const sectionDialogTitle = ref('添加试题')
const editingSectionIndex = ref(-1)
const sectionForm = reactive({
  type: 'choice',
  groupNo: '一',
  title: '',
  count: 10,
  score: 3,
  columns: 1,
  rows: 0,
  optionDirection: 'horizontal',
  arrangement: 'vertical',
  subQuestions: [],
  content: ''
})
const sectionRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  groupNo: [{ required: true, message: '请选择大题题号', trigger: 'change' }]
}
const sectionFormRef = ref(null)

const groupNoOptions = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

const usedGroupNos = computed(() => {
  const currentIdx = editingSectionIndex.value
  return config.sections
    .filter((s, idx) => idx !== currentIdx)
    .map(s => s.groupNo)
    .filter(Boolean)
})

// 自动获取下一个可用的大题题号
const getNextGroupNo = () => {
  const used = config.sections.map(s => s.groupNo).filter(Boolean)
  for (const no of groupNoOptions) {
    if (!used.includes(no)) return no
  }
  return groupNoOptions[groupNoOptions.length - 1]
}

const subTypeMap = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题'
}

const quickAdd = reactive({
  subType: 'single',
  count: 4,
  startNo: 1,
  endNo: 4,
  score: 3
})

const typeOptions = [
  { value: 'choice', label: '客观题' },
  { value: 'fill', label: '填空题' },
  { value: 'subjective', label: '解答题' },
  { value: 'composition_en', label: '作文（英）' },
  { value: 'composition_cn', label: '作文（语）' },
  { value: 'blank', label: '非作答区' }
]

const sectionTypeTitle = (type) => {
  const item = typeOptions.find(o => o.value === type)
  return item ? item.label : '未知'
}

const resetSectionForm = (type) => {
  sectionForm.type = type
  sectionForm.groupNo = getNextGroupNo()
  sectionForm.title = sectionTypeTitle(type)
  sectionForm.count = type === 'blank' ? 1 : (type.startsWith('composition') ? 1 : 10)
  sectionForm.score = type === 'choice' ? 3 : type === 'fill' ? 3 : type === 'subjective' ? 10 : type === 'composition_en' ? 15 : type === 'composition_cn' ? 30 : 0
  sectionForm.columns = 1
  sectionForm.rows = type === 'subjective' ? 8 : 0
  sectionForm.optionDirection = 'horizontal'
  sectionForm.arrangement = 'vertical'
  sectionForm.subQuestions = []
  sectionForm.content = ''
}

const openSectionDialog = (type) => {
  editingSectionIndex.value = -1
  sectionDialogTitle.value = `添加${sectionTypeTitle(type)}`
  resetSectionForm(type)
  sectionDialogVisible.value = true
}

const editSection = (idx) => {
  editingSectionIndex.value = idx
  const s = config.sections[idx]
  sectionDialogTitle.value = '编辑试题'
  sectionForm.type = s.type
  sectionForm.groupNo = s.groupNo || '一'
  sectionForm.title = s.title
  sectionForm.count = s.count
  sectionForm.score = s.score
  sectionForm.columns = s.columns || 1
  sectionForm.rows = s.rows || 0
  sectionForm.optionDirection = s.optionDirection || 'horizontal'
  sectionForm.arrangement = s.arrangement || 'vertical'
  sectionForm.subQuestions = (s.subQuestions || []).map(q => ({ ...q }))
  sectionForm.content = s.content || ''
  sectionDialogVisible.value = true
}

const onSubTypeChange = (row) => {
  row.subTypeLabel = subTypeMap[row.subType]
  if (row.subType === 'judge') {
    row.optionCount = 2
  } else if (!row.optionCount || row.optionCount < 2) {
    row.optionCount = 4
  }
}

const addChoiceSubQuestions = () => {
  const start = Number(quickAdd.startNo) || 0
  const end = Number(quickAdd.endNo) || 0
  const score = Number(quickAdd.score) || 0
  const subType = quickAdd.subType
  const optionCount = subType === 'judge' ? 2 : (Number(quickAdd.count) || 4)
  if (start <= 0 || end < start) return
  for (let no = start; no <= end; no++) {
    sectionForm.subQuestions.push({
      questionNo: no,
      score,
      subType,
      subTypeLabel: subTypeMap[subType],
      optionCount
    })
  }
}

const addSubjectiveSubQuestion = () => {
  const nextNo = sectionForm.subQuestions.length + 1
  sectionForm.subQuestions.push({
    questionNo: String(nextNo),
    score: sectionForm.score || 10,
    hasAnswerLine: true,
    lineCount: sectionForm.rows || 8
  })
}

const removeSubQuestion = (idx) => {
  sectionForm.subQuestions.splice(idx, 1)
}

const submitSection = async () => {
  try {
    await sectionFormRef.value.validate()

    let count = Number(sectionForm.count)
    let score = Number(sectionForm.score)
    let rows = Number(sectionForm.rows)

    if (sectionForm.type === 'choice') {
      count = sectionForm.subQuestions.length
      score = sectionForm.subQuestions.reduce((sum, q) => sum + Number(q.score || 0), 0)
    }
    if (sectionForm.type === 'subjective') {
      count = sectionForm.subQuestions.length
      score = sectionForm.subQuestions.reduce((sum, q) => sum + Number(q.score || 0), 0)
      rows = sectionForm.subQuestions.reduce((sum, q) => sum + (q.hasAnswerLine ? Number(q.lineCount || 0) : 0), 0)
    }

    const payload = {
      id: editingSectionIndex.value >= 0 ? config.sections[editingSectionIndex.value].id : Date.now(),
      type: sectionForm.type,
      groupNo: sectionForm.groupNo,
      title: sectionForm.title,
      count,
      score,
      columns: sectionForm.type === 'choice' ? Number(sectionForm.columns || 1) : 1,
      rows,
      optionDirection: sectionForm.optionDirection,
      arrangement: sectionForm.arrangement,
      subQuestions: sectionForm.subQuestions.map(q => ({ ...q })),
      content: sectionForm.content
    }
    if (editingSectionIndex.value >= 0) {
      config.sections[editingSectionIndex.value] = payload
    } else {
      config.sections.push(payload)
    }
    sectionDialogVisible.value = false
  } catch (e) {
    // validation error
  }
}

const closeSectionDialog = () => {
  sectionDialogVisible.value = false
}

const studentInfoDialogVisible = ref(false)
const studentInfoForm = reactive({
  digits: 8,
  fields: []
})

const normalizeStudentInfo = (info) => {
  if (info && Array.isArray(info.fields) && info.fields.length > 0) {
    return { fields: info.fields.map(f => ({ ...f })) }
  }
  // 兼容旧数据
  return {
    fields: [
      { id: 'name', label: info?.nameLabel || '姓名', placeholder: '________' },
      { id: 'class', label: info?.classLabel || '班级', placeholder: '________' }
    ]
  }
}

const openStudentInfoDialog = () => {
  const normalized = normalizeStudentInfo(config.studentInfo)
  studentInfoForm.fields = normalized.fields
  studentInfoForm.digits = config.digits || 8
  studentInfoDialogVisible.value = true
}

const addInfoField = () => {
  studentInfoForm.fields.push({
    id: `field_${Date.now()}`,
    label: '',
    placeholder: '________'
  })
}

const removeInfoField = (idx) => {
  studentInfoForm.fields.splice(idx, 1)
}

const submitStudentInfo = () => {
  config.studentInfo = {
    fields: studentInfoForm.fields
      .filter(f => f.label || f.placeholder)
      .map(f => ({ ...f }))
  }
  config.digits = Number(studentInfoForm.digits) || 8
  studentInfoDialogVisible.value = false
}

const loadTemplate = async () => {
  loading.value = true
  try {
    const res = await getAnswerCardTemplate(templateId)
    templateName.value = res.templateName
    Object.assign(config, defaultConfig(), res.config || {})
    config.layout = 'one'
  } catch (e) {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await updateAnswerCardTemplate(templateId, {
      templateName: config.title || templateName.value,
      width: 210,
      height: 297,
      config: { ...config }
    })
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handlePreview = () => {
  previewVisible.value = true
}

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped>
.answer-card-editor {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background: #f0f2f5;
}
.editor-header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.school-name {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.preview-area {
  flex: 1;
  overflow: auto;
  padding: 24px;
  display: flex;
  justify-content: center;
}
.paper {
  width: 794px;
  min-height: 1123px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 40px;
  position: relative;
  box-sizing: border-box;
}
.paper.color-red {
  color: #c03639;
}
.paper-header {
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px dashed #c0c4cc;
  padding: 16px;
  margin-bottom: 20px;
}
.qr-placeholder {
  width: 80px;
  height: 80px;
  border: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}
.title-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.title-input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 22px;
  font-weight: bold;
  text-align: center;
  color: inherit;
  background: transparent;
}
.title-input::placeholder {
  color: #c0c4cc;
}
.student-info {
  display: flex;
  border: 1px solid #303133;
  margin-bottom: 20px;
}
.student-left {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  border-right: 1px solid #303133;
}
.info-line {
  font-size: 16px;
}
.student-right {
  width: 320px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.exam-no-label {
  font-size: 14px;
  margin-bottom: 6px;
}
.bubble-grid {
  border: 1px solid #303133;
}
.bubble-row {
  display: flex;
  border-bottom: 1px solid #303133;
}
.bubble-row:last-child {
  border-bottom: none;
}
.bubble-cell {
  width: 32px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #303133;
  font-size: 12px;
}
.bubble-cell:last-child {
  border-right: none;
}
.header-row .bubble-cell {
  height: 28px;
  padding: 2px;
}
.digit-input {
  width: 100%;
  height: 100%;
  border: none;
  text-align: center;
  outline: none;
  font-size: 12px;
}
.barcode-placeholder {
  width: 200px;
  height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 6px 0;
}
.barcode-line {
  height: 2px;
  background: #303133;
}
.qrcode-placeholder {
  width: 80px;
  height: 80px;
  border: 1px solid #303133;
  display: flex;
  align-items: center;
  justify-content: center;
}
.handwrite-no {
  font-size: 16px;
  padding: 20px;
}
.notes-box {
  border: 1px solid #303133;
  padding: 16px;
  margin-bottom: 20px;
  position: relative;
}
.notes-title {
  font-weight: bold;
  margin-bottom: 8px;
}
.notes-box p {
  margin: 0 0 6px;
  font-size: 14px;
}
.notes-marks {
  display: flex;
  gap: 30px;
  margin-top: 12px;
}
.mark-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.mark-box {
  width: 20px;
  height: 20px;
  border: 1px solid #303133;
}
.mark-box.filled {
  background: #303133;
}
.sections-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.layout-two .sections-wrap,
.layout-three .sections-wrap {
  display: block;
}
.section-card {
  break-inside: avoid;
  border: 1px solid #303133;
  padding: 16px;
  margin-bottom: 16px;
}
.section-title {
  font-weight: bold;
  margin-bottom: 12px;
  font-size: 15px;
}
.choice-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
.choice-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.choice-no {
  width: 18px;
}
.choice-opt {
  width: 16px;
  height: 16px;
  border: 1px solid #303133;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}
.fill-lines {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.fill-line {
  border-bottom: 1px solid #303133;
  height: 24px;
}
.subjective-box {
  min-height: 120px;
}
.answer-lines {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.answer-line {
  border-bottom: 1px dashed #909399;
  height: 22px;
}
.composition-grid {
  display: grid;
  grid-template-columns: repeat(20, 1fr);
  gap: 1px;
  border: 1px solid #303133;
}
.composition-cell {
  aspect-ratio: 1;
  border: 1px solid #dcdfe6;
}
.blank-area {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  border: 1px dashed #c0c4cc;
}
.seal-line {
  position: absolute;
  top: 80px;
  bottom: 80px;
  width: 0;
  border-left: 1px dashed #909399;
}
.seal-left {
  left: 20px;
}
.seal-right {
  right: 20px;
}

.settings-panel {
  width: 340px;
  background: #fff;
  border-left: 1px solid #ebeef5;
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}
.panel-title {
  font-size: 15px;
  font-weight: bold;
  margin: 16px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}
.panel-title:first-child {
  margin-top: 0;
}
.setting-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
}
.setting-row.vertical {
  flex-direction: column;
  align-items: flex-start;
}
.setting-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}
.setting-row.switches {
  gap: 8px;
}
.ml {
  margin-left: 12px;
}
.section-btns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}
.section-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.section-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
}
.section-actions {
  display: flex;
  gap: 4px;
}

.quick-add-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}
.quick-add-bar.simple .num-input {
  width: 70px;
}
.quick-add-bar.simple .num-input :deep(.el-input__inner) {
  padding: 0 8px;
  text-align: center;
}
.quick-text {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

.table-num-input {
  width: 100%;
}
.table-num-input :deep(.el-input__inner) {
  padding: 0 8px;
  text-align: center;
}

/* 隐藏原生数字输入框的上下箭头 */
.num-input :deep(input[type="number"]::-webkit-outer-spin-button),
.num-input :deep(input[type="number"]::-webkit-inner-spin-button),
.table-num-input :deep(input[type="number"]::-webkit-outer-spin-button),
.table-num-input :deep(input[type="number"]::-webkit-inner-spin-button) {
  -webkit-appearance: none;
  margin: 0;
}
.num-input :deep(input[type="number"]),
.table-num-input :deep(input[type="number"]) {
  -moz-appearance: textfield;
}

.sub-header-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.empty-table-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 24px 0;
  border: 1px solid #ebeef5;
  border-top: none;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.info-fields-label {
  font-size: 13px;
  color: #606266;
  margin: 12px 0 8px;
}
.info-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
