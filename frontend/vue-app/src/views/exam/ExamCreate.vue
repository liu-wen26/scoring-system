<template>
  <div class="exam-create-page">
    <el-page-header title="新建考试" @back="$router.back()" />
    
    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="exam-form"
      >
        <el-form-item label="考试名称" prop="examName">
          <el-input v-model="form.examName" placeholder="请输入考试名称" />
        </el-form-item>
        
        <el-form-item label="考试类型" prop="examType">
          <el-select v-model="form.examType" placeholder="请选择考试类型">
            <el-option label="月考" value="monthly" />
            <el-option label="期中" value="midterm" />
            <el-option label="期末" value="final" />
            <el-option label="模拟" value="simulation" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="考试级别" prop="examLevel">
          <el-select v-model="form.examLevel" placeholder="请选择考试级别">
            <el-option label="校级" value="school" />
            <el-option label="区级" value="district" />
            <el-option label="市级" value="city" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="参考年级" prop="grade">
          <el-select v-model="form.gradeId" placeholder="请选择年级" @change="onGradeChange">
            <el-option
              v-for="g in gradeList"
              :key="g.id"
              :label="g.gradeName"
              :value="g.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="考试时间" prop="timeRange">
          <el-date-picker
            v-model="form.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="参考科目" prop="subjectIds">
          <el-checkbox-group v-model="form.subjectIds">
            <el-checkbox
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.id"
            >
              {{ subject.subjectName }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item v-if="form.subjectIds.length > 0" label="各科总分">
          <div class="subject-scores">
            <div
              v-for="sid in form.subjectIds"
              :key="sid"
              class="subject-score-item"
            >
              <span class="subject-name">{{ getSubjectName(sid) }}</span>
              <el-input-number
                v-model="subjectScoreMap[sid]"
                :min="1"
                :max="1000"
                size="small"
                style="width: 120px"
              />
              <span class="score-unit">分</span>
            </div>
            <div v-if="form.subjectIds.length > 1" class="total-score-line">
              总分合计：<strong>{{ computedTotalScore }}</strong> 分
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="参考人数" prop="totalStudents">
          <div class="student-count-wrapper">
            <el-input-number v-model="form.totalStudents" :min="0" :max="10000" />
            <span v-if="archiveStudentCount > 0" class="archive-hint">
              （{{ form.grade }}学生档案共 <strong>{{ archiveStudentCount }}</strong> 人，已自动关联）
            </span>
            <span v-else-if="form.gradeId" class="archive-hint empty">
              （{{ form.grade || gradeList.find(g => g.id === form.gradeId)?.gradeName }}学生档案共 0 人）
            </span>
          </div>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit">创建</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createExam, getSubjects, getGrades, getStudentCount } from '@/api/exam'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const formRef = ref()
const subjects = ref([])
const gradeList = ref([])
const archiveStudentCount = ref(0)

const form = reactive({
  examName: '',
  examType: '',
  examLevel: '',
  grade: '',
  gradeId: null,
  timeRange: [],
  subjectIds: [],
  totalStudents: 0,
  description: ''
})

// 每个科目的分数字典 { subjectId: score }
const subjectScoreMap = reactive({})

// 监听科目选择变化，自动初始化/清理分数
watch(() => form.subjectIds, (newIds, oldIds) => {
  // 为新选中的科目设置默认分100
  newIds.forEach(id => {
    if (!(id in subjectScoreMap)) {
      subjectScoreMap[id] = 100
    }
  })
  // 清理取消选中的科目
  const removed = oldIds?.filter(id => !newIds.includes(id)) || []
  removed.forEach(id => {
    delete subjectScoreMap[id]
  })
}, { deep: true })

const computedTotalScore = computed(() => {
  return form.subjectIds.reduce((sum, id) => sum + (subjectScoreMap[id] || 0), 0)
})

const getSubjectName = (id) => {
  const s = subjects.value.find(s => s.id === id)
  return s ? s.subjectName : ''
}

// 年级变化时，从学生档案获取该年级学生人数，并加载对应科目
const onGradeChange = async () => {
  archiveStudentCount.value = 0
  form.grade = ''
  // 清空已选科目和分数
  form.subjectIds = []
  for (const key in subjectScoreMap) {
    delete subjectScoreMap[key]
  }
  if (!form.gradeId) return
  const g = gradeList.value.find(item => item.id === form.gradeId)
  form.grade = g ? g.gradeName : ''
  try {
    const [countRes, subjectsData] = await Promise.all([
      getStudentCount({ gradeId: form.gradeId }),
      getSubjects({ gradeId: form.gradeId })
    ])
    archiveStudentCount.value = countRes.count || 0
    subjects.value = subjectsData || []
    // 自动填充学生人数
    form.totalStudents = archiveStudentCount.value
  } catch (e) {
    console.error('获取年级关联数据失败', e)
    ElMessage.error('获取年级关联数据失败')
  }
}

const rules = {
  examName: [
    { required: true, message: '请输入考试名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  examType: [
    { required: true, message: '请选择考试类型', trigger: 'change' }
  ],
  examLevel: [
    { required: true, message: '请选择考试级别', trigger: 'change' }
  ],
  grade: [
    { required: true, message: '请选择年级', trigger: 'change' }
  ],
  timeRange: [
    { required: true, message: '请选择考试时间', trigger: 'change' }
  ],
  subjectIds: [
    { required: true, message: '请选择参考科目', trigger: 'change', type: 'array' }
  ]
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 构建每科目分数列表
  const subjectScores = form.subjectIds.map(id => ({
    subjectId: id,
    subjectName: getSubjectName(id),
    totalScore: subjectScoreMap[id] || 100
  }))
  
  try {
    const res = await createExam({
      examName: form.examName,
      examType: form.examType,
      examLevel: form.examLevel,
      grade: form.grade,
      startTime: form.timeRange[0],
      endTime: form.timeRange[1],
      subjectIds: form.subjectIds,
      subjectScores: subjectScores,
      totalScore: computedTotalScore.value,
      totalStudents: form.totalStudents,
      description: form.description
    })

    const examId = res.id
    ElMessage.success('考试创建成功')

    try {
      await ElMessageBox.confirm('是否立即配置答题卡？', '考试创建成功', {
        confirmButtonText: '去配置',
        cancelButtonText: '稍后',
        type: 'success'
      })
      router.push(`/exam/${examId}/answer-card`)
    } catch {
      router.push('/exam')
    }
  } catch (error) {
    const detail = error.response?.data?.detail
    let msg = '创建失败'
    if (Array.isArray(detail)) {
      msg = detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ')
    } else if (typeof detail === 'string') {
      msg = detail
    } else if (detail?.message) {
      msg = detail.message
    }
    ElMessage.error(msg)
  }
}

onMounted(async () => {
  try {
    const gradesData = await getGrades()
    gradeList.value = gradesData || []
  } catch (e) {
    ElMessage.error('加载基础数据失败')
  }
})
</script>

<style scoped>
.exam-create-page {
  padding: 0;
}

.form-card {
  margin-top: 20px;
  max-width: 800px;
}

.exam-form {
  padding: 20px;
}

.subject-scores {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.subject-score-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 6px;
}

.subject-name {
  font-weight: 500;
  min-width: 80px;
  color: #303133;
}

.score-unit {
  color: #909399;
  font-size: 13px;
}

.total-score-line {
  width: 100%;
  padding-top: 8px;
  border-top: 1px dashed #dcdfe6;
  color: #606266;
  font-size: 14px;
}

.total-score-line strong {
  color: #409eff;
  font-size: 16px;
}

.student-count-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.archive-hint {
  color: #67c23a;
  font-size: 13px;
}

.archive-hint strong {
  color: #409eff;
}

.archive-hint.empty {
  color: #e6a23c;
}
</style>
