<template>
  <div class="archive-page">
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane label="学生档案" name="student" />
      <el-tab-pane label="教师档案" name="teacher" />
    </el-tabs>

    <div class="toolbar">
      <span class="label">筛选：</span>
      <el-select v-model="filter.gradeId" placeholder="全部年级" clearable @change="onGradeChange">
        <el-option label="全部年级" :value="null" />
        <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
      </el-select>
      <el-select v-model="filter.classId" placeholder="全部班级" clearable :disabled="!filter.gradeId">
        <el-option label="全部班级" :value="null" />
        <el-option v-for="c in classList" :key="c.id" :label="c.className" :value="c.id" />
      </el-select>
      <el-input v-model="filter.keyword" placeholder="学生姓名/学号" clearable style="width: 200px" />
      <el-button type="primary" @click="loadStudents">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
      <el-button type="success" @click="openDialog()">新增学生</el-button>
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        accept=".xlsx,.csv"
        :on-change="handleBatchFile"
      >
        <el-button type="warning" icon="Upload">批量导入</el-button>
      </el-upload>
      <el-button link type="primary" @click="downloadTemplate">下载模板</el-button>
    </div>

    <el-table :data="studentList" v-loading="loading" stripe border>
      <el-table-column prop="studentNo" label="学号" />
      <el-table-column prop="realName" label="姓名" />
      <el-table-column prop="gender" label="性别" width="80" />
      <el-table-column prop="gradeName" label="年级" />
      <el-table-column prop="className" label="班级" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="primary" @click="viewDetail(row)">查看档案</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="loadStudents"
    />

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑学生' : '新增学生'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="学号" prop="studentNo">
          <el-input v-model="form.studentNo" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="年级" prop="gradeId">
          <el-select v-model="form.gradeId" placeholder="请选择年级" @change="onFormGradeChange">
            <el-option v-for="g in gradeList" :key="g.id" :label="g.gradeName" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级" prop="classId">
          <el-select v-model="form.classId" placeholder="请选择班级">
            <el-option v-for="c in formClassList" :key="c.id" :label="c.className" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="学生档案" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="学号">{{ detail.studentNo }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ detail.realName }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ detail.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="年级">{{ detail.gradeName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ detail.className || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detail.status === 1 ? '启用' : '禁用' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="batchVisible" title="批量导入学生" width="800px">
      <div class="batch-tip">
        共解析 {{ batchList.length }} 条，有效 {{ batchValidCount }} 条，无效 {{ batchList.length - batchValidCount }} 条。
      </div>
      <el-table :data="batchList" height="400" stripe border>
        <el-table-column prop="index" label="行号" width="70" />
        <el-table-column prop="studentNo" label="学号" />
        <el-table-column prop="realName" label="姓名" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="gradeName" label="年级" />
        <el-table-column prop="className" label="班级" />
        <el-table-column label="状态" width="180">
          <template #default="{ row }">
            <el-tag :type="row.valid ? 'success' : 'danger'">{{ row.valid ? '有效' : row.error }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="submitBatch">导入有效数据</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStudents, createStudent, updateStudent, deleteStudent, batchCreateStudents } from '@/api/user'
import { getGrades, getClasses } from '@/api/exam'
import * as XLSX from 'xlsx'

const activeTab = ref('student')
watch(activeTab, (val) => {
  if (val === 'teacher') {
    window.location.href = '/archive/teacher'
  }
})

const loading = ref(false)
const gradeList = ref([])
const classList = ref([])
const formClassList = ref([])
const allClassList = ref([])
const studentList = ref([])
const filter = reactive({
  gradeId: null,
  classId: null,
  keyword: ''
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = reactive({
  id: null,
  studentNo: '',
  realName: '',
  gender: '男',
  gradeId: null,
  classId: null,
  status: 1
})
const rules = {
  studentNo: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gradeId: [{ required: true, message: '请选择年级', trigger: 'change' }],
  classId: [{ required: true, message: '请选择班级', trigger: 'change' }]
}
const detail = reactive({})

const batchVisible = ref(false)
const batchList = ref([])
const batchSubmitting = ref(false)
const batchValidCount = computed(() => batchList.value.filter(r => r.valid).length)

const loadGrades = async () => {
  try {
    const res = await getGrades()
    gradeList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const loadAllClasses = async () => {
  try {
    const res = await getClasses()
    allClassList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const loadClasses = async (gradeId, target = 'filter') => {
  if (!gradeId) {
    if (target === 'filter') classList.value = []
    else formClassList.value = []
    return
  }
  try {
    const res = await getClasses(gradeId)
    if (target === 'filter') classList.value = res || []
    else formClassList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const onGradeChange = () => {
  filter.classId = null
  loadClasses(filter.gradeId, 'filter')
}

const onFormGradeChange = () => {
  form.classId = null
  loadClasses(form.gradeId, 'form')
}

const resetFilter = () => {
  filter.gradeId = null
  filter.classId = null
  filter.keyword = ''
  pagination.page = 1
  loadStudents()
}

const buildQueryParams = () => {
  const params = {
    skip: (pagination.page - 1) * pagination.pageSize,
    limit: pagination.pageSize
  }
  if (filter.gradeId) params.gradeId = filter.gradeId
  if (filter.classId) params.classId = filter.classId
  if (filter.keyword) params.keyword = filter.keyword
  return params
}

const loadStudents = async () => {
  loading.value = true
  try {
    const res = await getStudents(buildQueryParams())
    studentList.value = res.items || []
    pagination.total = res.total || 0
  } catch (e) {
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  form.id = row?.id || null
  form.studentNo = row?.studentNo || ''
  form.realName = row?.realName || ''
  form.gender = row?.gender || '男'
  form.gradeId = row?.gradeId || null
  form.classId = row?.classId || null
  form.status = row?.status ?? 1
  if (form.gradeId) loadClasses(form.gradeId, 'form')
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    const payload = {
      studentNo: form.studentNo,
      realName: form.realName,
      gender: form.gender,
      gradeId: form.gradeId,
      classId: form.classId,
      status: form.status
    }
    if (isEdit.value) {
      await updateStudent(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createStudent(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadStudents()
  } catch (e) {
    if (e?.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  }
}

const viewDetail = async (row) => {
  Object.assign(detail, row)
  detailVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除学生 ${row.realName} 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await deleteStudent(row.id)
      ElMessage.success('删除成功')
      loadStudents()
    })
    .catch(() => {})
}

// 批量导入
const parseCsv = (text) => {
  const rows = []
  let row = []
  let cell = ''
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    const next = text[i + 1]
    if (inQuotes) {
      if (ch === '"') {
        if (next === '"') {
          cell += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        cell += ch
      }
    } else {
      if (ch === '"') {
        inQuotes = true
      } else if (ch === ',') {
        row.push(cell)
        cell = ''
      } else if (ch === '\n' || ch === '\r') {
        if (ch === '\r' && next === '\n') i++
        row.push(cell)
        rows.push(row)
        row = []
        cell = ''
      } else {
        cell += ch
      }
    }
  }
  row.push(cell)
  if (row.length > 1 || cell) rows.push(row)
  return rows
}

const parseFile = (raw) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const name = raw.name.toLowerCase()
        let rows = []
        if (name.endsWith('.csv')) {
          rows = parseCsv(e.target.result)
        } else {
          const data = e.target.result
          const workbook = XLSX.read(data, { type: 'binary' })
          const sheet = workbook.Sheets[workbook.SheetNames[0]]
          rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
        }
        resolve(rows)
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = reject
    if (raw.name.toLowerCase().endsWith('.csv')) {
      reader.readAsText(raw)
    } else {
      reader.readAsBinaryString(raw)
    }
  })
}

const buildBatchStudents = (rows) => {
  if (!rows || rows.length < 2) return []
  const headers = rows[0].map(h => String(h).trim())
  const idx = (name) => headers.indexOf(name)
  const gradeMap = new Map(gradeList.value.map(g => [String(g.gradeName).trim(), g.id]))
  const classMap = new Map(allClassList.value.map(c => [`${c.gradeId}-${String(c.className).trim()}`, c.id]))

  return rows.slice(1).map((cells, i) => {
    const get = (col) => (col >= 0 ? String(cells[col] ?? '').trim() : '')
    const studentNo = get(idx('学号'))
    const realName = get(idx('姓名'))
    const gender = get(idx('性别')) || '男'
    const gradeName = get(idx('年级'))
    const className = get(idx('班级'))
    const gradeId = gradeMap.get(gradeName) || null
    let classId = null
    if (gradeId && className) {
      classId = classMap.get(`${gradeId}-${className}`) || null
    }
    let error = ''
    if (!studentNo) error = '学号为空'
    else if (!realName) error = '姓名为空'
    else if (!gradeId) error = `年级未找到：${gradeName}`
    else if (!classId) error = `班级未找到：${className}`
    return {
      index: i + 2,
      studentNo,
      realName,
      gender,
      gradeId,
      classId,
      gradeName,
      className,
      valid: !error,
      error
    }
  })
}

const handleBatchFile = async (file) => {
  try {
    const rows = await parseFile(file.raw)
    batchList.value = buildBatchStudents(rows)
    batchVisible.value = true
  } catch (e) {
    ElMessage.error('文件解析失败，请检查文件格式')
    console.error(e)
  }
}

const submitBatch = async () => {
  const validRows = batchList.value.filter(r => r.valid)
  if (!validRows.length) {
    ElMessage.warning('没有有效的数据可导入')
    return
  }
  batchSubmitting.value = true
  try {
    const payload = validRows.map(r => ({
      studentNo: r.studentNo,
      realName: r.realName,
      gender: r.gender,
      gradeId: r.gradeId,
      classId: r.classId,
      status: 1
    }))
    const res = await batchCreateStudents(payload)
    ElMessage.success(`导入完成：成功 ${res.successCount} 条，失败 ${res.failedCount} 条`)
    batchVisible.value = false
    loadStudents()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '批量导入失败')
  } finally {
    batchSubmitting.value = false
  }
}

const downloadTemplate = () => {
  const headers = ['学号', '姓名', '性别', '年级', '班级']
  const sample = [
    headers,
    ['2024001', '张三', '男', '一年级', '1班'],
    ['2024002', '李四', '女', '一年级', '2班']
  ]
  const csv = sample.map(row => row.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = '学生导入模板.csv'
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(() => {
  loadGrades()
  loadAllClasses()
  loadStudents()
})
</script>

<style scoped>
.archive-page {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.label {
  color: #606266;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
.batch-tip {
  margin-bottom: 12px;
  color: #606266;
}
</style>
