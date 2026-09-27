<template>
  <el-dialog
    v-model="visible"
    title="AI 辅助阅卷"
    width="700px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    destroy-on-close
    @close="handleClose"
  >
    <!-- 配置与启动阶段 -->
    <div v-if="!taskId && !finished">
      <el-alert
        title="AI 辅助阅卷将自动调用阿里云百炼大模型对当前题目连续评分。未设置数量时，将一直批改到该题全部完成。"
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      />

      <el-form label-position="top" :model="form">
        <el-form-item label="阿里云百炼 API-Key">
          <el-input
            v-model="form.apiKey"
            type="password"
            show-password
            placeholder="请输入阿里云百炼 API-Key"
            clearable
          />
          <div v-if="configLoaded && config.hasConfig" class="config-tip">
            已保存过 Key，如需更新请直接填写新 Key。
          </div>
        </el-form-item>

        <el-form-item label="题目内容">
          <el-input
            v-model="form.questionContent"
            type="textarea"
            :rows="3"
            placeholder="请输入当前题目内容"
          />
        </el-form-item>

        <el-form-item label="标准答案">
          <el-input
            v-model="form.standardAnswer"
            type="textarea"
            :rows="3"
            placeholder="请输入标准答案或参考答案"
          />
        </el-form-item>

        <el-form-item label="评分标准">
          <el-input
            v-model="form.scoringCriteria"
            type="textarea"
            :rows="3"
            placeholder="请输入评分标准，例如：答对要点得 5 分，部分正确得 2-4 分..."
          />
        </el-form-item>

        <el-form-item label="批改数量（不填则批改完该题全部试卷）">
          <el-input-number
            v-model="form.totalLimit"
            :min="0"
            :max="9999"
            :step="1"
            :precision="0"
            placeholder="全部"
            style="width: 160px"
          />
          <span class="limit-hint">0 表示不限制</span>
        </el-form-item>
      </el-form>

      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="starting" @click="startAIMark">开始 AI 批阅</el-button>
      </div>
    </div>

    <!-- 批阅中阶段 -->
    <div v-else>
      <div class="ai-progress">
        <span>进度：{{ progress.processedCount }} / {{ progress.totalLimit > 0 ? progress.totalLimit : '全部' }}</span>
        <span>状态：<el-tag :type="statusType">{{ statusText }}</el-tag></span>
      </div>
      <div class="auto-mode-row">
        <el-switch v-model="autoMode" active-text="自动连续批改" />
        <span class="auto-mode-tip">开启后 AI 将自动完成当前试卷并立即进入下一份</span>
      </div>
      <el-progress
        v-if="progress.totalLimit > 0"
        :percentage="progressPercent"
        :status="progressStatus"
      />

      <div v-if="currentPaper" class="ai-paper">
        <div class="paper-header">
          <span>学生：{{ currentPaper.studentName || currentPaper.studentId }}</span>
          <span>题号：{{ currentPaper.questionNo }}</span>
          <span>满分：{{ currentPaper.fullScore }}</span>
        </div>
        <div class="paper-body">
          <div class="paper-label">学生答案</div>
          <div class="paper-answer">{{ currentPaper.studentAnswer }}</div>

          <div class="paper-label" style="margin-top: 16px">AI 评分</div>
          <div class="ai-score-row">
            <el-input-number
              v-model="currentScore"
              :min="0"
              :max="currentPaper.fullScore"
              :step="0.5"
              :precision="1"
              style="width: 140px"
            />
            <span class="score-unit">分</span>
          </div>

          <div class="paper-label" style="margin-top: 12px">评分理由</div>
          <el-input
            v-model="currentReason"
            type="textarea"
            :rows="2"
            placeholder="AI 评分理由"
          />
        </div>
      </div>

      <el-result
        v-else-if="finished"
        icon="success"
        title="AI 批阅完成"
        :sub-title="finishedMessage"
      />

      <div class="dialog-footer">
        <el-button v-if="!finished" type="danger" :loading="stopping" @click="stopAIMark">停止批阅</el-button>
        <el-button v-if="!finished" type="primary" :loading="scoring" @click="scoreNext">
          {{ autoMode ? '自动批改中...' : '批改并下一份' }}
        </el-button>
        <el-button v-if="finished" type="primary" @click="visible = false">完成</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getAIConfig,
  saveAIConfig,
  createAIMarkTask,
  scoreAIPaper,
  stopAIMarkTask
} from '@/api/mark'

const props = defineProps({
  modelValue: Boolean,
  examId: [Number, String],
  subjectId: [Number, String],
  questionNo: [Number, String],
  questionContent: String
})

const emit = defineEmits(['update:modelValue', 'finished'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = reactive({
  apiKey: '',
  questionContent: '',
  standardAnswer: '',
  scoringCriteria: '',
  totalLimit: 0
})

const configLoaded = ref(false)
const config = reactive({ hasConfig: false, model: 'qwen-turbo' })
const taskId = ref(null)
const starting = ref(false)
const scoring = ref(false)
const stopping = ref(false)
const finished = ref(false)
const finishedMessage = ref('')
const currentPaper = ref(null)
const currentScore = ref(0)
const currentReason = ref('')
const autoMode = ref(false)
const progress = reactive({ processedCount: 0, successCount: 0, totalLimit: 0 })

const statusText = computed(() => {
  if (finished.value) return '已完成'
  return scoring.value ? '批改中' : '运行中'
})
const statusType = computed(() => {
  if (finished.value) return 'success'
  return scoring.value ? 'warning' : 'primary'
})
const progressPercent = computed(() => {
  if (progress.totalLimit <= 0) return 0
  return Math.min(100, Math.round((progress.processedCount / progress.totalLimit) * 100))
})
const progressStatus = computed(() => {
  if (finished.value) return 'success'
  return ''
})

watch(() => props.modelValue, (val) => {
  if (val) {
    resetState()
    loadConfig()
    if (props.questionContent) {
      form.questionContent = props.questionContent
    }
  }
})

const resetState = () => {
  taskId.value = null
  finished.value = false
  finishedMessage.value = ''
  currentPaper.value = null
  currentScore.value = 0
  currentReason.value = ''
  autoMode.value = false
  progress.processedCount = 0
  progress.successCount = 0
  progress.totalLimit = 0
}

const loadConfig = async () => {
  try {
    const res = await getAIConfig()
    config.hasConfig = res.hasConfig || false
    config.model = res.model || 'qwen-turbo'
    configLoaded.value = true
  } catch (e) {
    console.error('读取 AI 配置失败:', e)
  }
}

const startAIMark = async () => {
  if (!form.apiKey && !config.hasConfig) {
    ElMessage.warning('请先输入阿里云百炼 API-Key')
    return
  }
  if (!form.questionContent || !form.standardAnswer || !form.scoringCriteria) {
    ElMessage.warning('请填写题目内容、标准答案和评分标准')
    return
  }

  starting.value = true
  try {
    // 保存 API-Key
    if (form.apiKey) {
      await saveAIConfig({ apiKey: form.apiKey })
    }

    // 创建任务
    const res = await createAIMarkTask({
      examId: props.examId,
      subjectId: props.subjectId,
      questionNo: String(props.questionNo),
      questionContent: form.questionContent,
      standardAnswer: form.standardAnswer,
      scoringCriteria: form.scoringCriteria,
      totalLimit: form.totalLimit
    })
    taskId.value = res.taskId
    progress.totalLimit = form.totalLimit
    ElMessage.success(res.message || '任务创建成功')

    // 自动开始第一份
    await scoreNext()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '启动失败')
  } finally {
    starting.value = false
  }
}

const scoreNext = async () => {
  if (!taskId.value || finished.value) return
  scoring.value = true
  try {
    const res = await scoreAIPaper(taskId.value)
    if (res.finished) {
      finished.value = true
      finishedMessage.value = res.message || '批阅完成'
      currentPaper.value = null
      emit('finished')
      return
    }

    currentPaper.value = res.current
    currentScore.value = res.current.aiScore
    currentReason.value = res.current.aiReason
    progress.processedCount = res.progress?.processedCount || 0
    progress.successCount = res.progress?.successCount || 0

    // 自动模式下延迟继续
    if (autoMode.value) {
      setTimeout(() => scoreNext(), 800)
    }
  } catch (e) {
    autoMode.value = false
    ElMessage.error(e?.response?.data?.detail || 'AI 评分失败')
  } finally {
    scoring.value = false
  }
}

const stopAIMark = async () => {
  if (!taskId.value) return
  stopping.value = true
  autoMode.value = false
  try {
    await stopAIMarkTask(taskId.value)
    finished.value = true
    finishedMessage.value = '已手动停止'
    currentPaper.value = null
  } catch (e) {
    ElMessage.error('停止失败')
  } finally {
    stopping.value = false
  }
}

const handleClose = () => {
  if (taskId.value && !finished.value) {
    stopAIMarkTask(taskId.value).catch(() => {})
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.config-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.limit-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}

.ai-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.auto-mode-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.auto-mode-tip {
  font-size: 12px;
  color: #909399;
}

.ai-paper {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.paper-header {
  display: flex;
  gap: 24px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 12px;
}

.paper-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.paper-answer {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  line-height: 1.6;
  color: #303133;
  min-height: 60px;
  white-space: pre-wrap;
}

.ai-score-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-unit {
  color: #606266;
}
</style>
