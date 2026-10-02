<template>
  <div class="answer-card-config-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/exam' }">考试列表</el-breadcrumb-item>
        <el-breadcrumb-item>答题卡设置</el-breadcrumb-item>
      </el-breadcrumb>
      <h2 class="page-title">{{ examName }}</h2>
      <el-select
        v-if="subjects.length > 1"
        v-model="currentSubjectId"
        placeholder="选择科目"
        style="width: 140px; margin-left: 12px;"
        @change="loadSubjectConfig"
      >
        <el-option
          v-for="s in subjects"
          :key="s.subjectId"
          :label="s.subjectName"
          :value="s.subjectId"
        />
      </el-select>
      <div class="header-actions">
        <el-button @click="handleSplit">拆试卷</el-button>
        <el-button @click="handleClear">清空模板</el-button>
        <el-button type="primary" @click="handleReplace">更换模板</el-button>
        <input
          ref="fileInput"
          type="file"
          accept="image/*,.pdf"
          style="display:none"
          @change="onFileChange"
        />
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧画布区 -->
      <div class="canvas-area">
        <div class="canvas-toolbar">
          <div class="tool-group">
            <el-tooltip content="选择/移动">
              <el-button
                :type="activeTool === 'select' ? 'primary' : ''"
                @click="activeTool = 'select'"
              >
                <el-icon><Pointer /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="框选学生信息">
              <el-button
                :type="activeTool === 'student' ? 'success' : ''"
                @click="activeTool = 'student'"
              >
                <el-icon><User /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip :content="objectiveQuestionList.length ? '框选客观题' : '请先添加客观题组'">
              <el-button
                :type="activeTool === 'objective' ? 'danger' : ''"
                :disabled="!objectiveQuestionList.length"
                @click="activeTool = 'objective'"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip :content="subjectiveQuestionList.length ? '框选主观题' : '请先添加主观题组'">
              <el-button
                :type="activeTool === 'subjective' ? 'primary' : ''"
                :disabled="!subjectiveQuestionList.length"
                @click="activeTool = 'subjective'"
              >
                <el-icon><Document /></el-icon>
              </el-button>
            </el-tooltip>
            <el-divider direction="vertical" />
            <el-tooltip content="撤销">
              <el-button @click="handleUndo" :disabled="historyIndex <= 0">
                <el-icon><RefreshLeft /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="重做">
              <el-button @click="handleRedo" :disabled="historyIndex >= historyStack.length - 1">
                <el-icon><RefreshRight /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除选中">
              <el-button type="danger" @click="handleDelete" :disabled="!selectedRegion">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
          <div class="tool-group">
            <el-button size="small" @click="zoom = Math.max(50, zoom - 10)">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <span class="zoom-label">{{ zoom }}%</span>
            <el-button size="small" @click="zoom = Math.min(200, zoom + 10)">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="canvas-scroll" v-loading="loading">
          <div v-if="!templateImageUrl" class="empty-template">
            <el-empty description="请上传答题卡模板图片或 PDF">
              <el-button type="primary" @click="$refs.fileInput.click()">上传模板</el-button>
            </el-empty>
          </div>
          <AnswerCardCanvas
            v-else
            ref="canvasComp"
            v-model="allRegions"
            :template-image="templateImageUrl"
            :page-previews="templatePagePreviews"
            :page-count="pageCount"
            :active-tool="activeTool"
            :zoom="zoom"
            :student-fields="studentFields"
            :objective-questions="objectiveQuestionList"
            :subjective-questions="subjectiveQuestionList"
            :next-region-label="pendingRegionTarget"
            @region-selected="onRegionSelected"
            @region-created="onRegionCreated"
          />
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-label">客观题：</div>
            <div class="stat-value">
              <span class="stat-num">{{ objectiveCount }}</span>题
              <span class="stat-score">{{ objectiveScore }}</span>分
            </div>
          </div>
          <el-divider direction="vertical" />
          <div class="stat-item">
            <div class="stat-label">主观题：</div>
            <div class="stat-value">
              <span class="stat-num">{{ subjectiveCount }}</span>题
              <span class="stat-score">{{ subjectiveScore }}</span>分
            </div>
          </div>
          <el-divider direction="vertical" />
          <div class="stat-item">
            <div class="stat-label">总计：</div>
            <div class="stat-value">
              <span class="stat-num">{{ objectiveCount + subjectiveCount }}</span>题
              <span class="stat-score">{{ objectiveScore + subjectiveScore }}</span>分
            </div>
          </div>
        </div>

        <el-collapse v-model="activeCollapse" class="panel-collapse">
          <!-- 客观题 -->
          <el-collapse-item name="objective">
            <template #title>
              <div class="collapse-title">
                <el-icon :size="18" color="#67C23A"><Select /></el-icon>
                <span>客观题</span>
                <el-tag size="small" type="success" effect="dark" class="tag-right">
                  {{ objectiveCount }} 题
                </el-tag>
              </div>
            </template>
            
            <div class="question-group-form">
              <div class="form-row">
                <span class="form-label">从</span>
                <el-input v-model="objectiveForm.startNo" type="number" size="small" placeholder="序号" class="form-input" />
                <span class="form-label">到</span>
                <el-input v-model="objectiveForm.endNo" type="number" size="small" placeholder="题" class="form-input" />
                <el-input v-model="objectiveForm.groupLabel" size="small" placeholder="大题号名称" class="form-input" />
                <el-input v-model="objectiveForm.scorePerQuestion" type="number" size="small" placeholder="分/题" class="form-input" />
              </div>
              <div class="form-row">
                <el-select v-model="objectiveForm.questionType" size="small" placeholder="请选择" class="form-select">
                  <el-option label="单选题" value="single" />
                  <el-option label="多选题" value="multiple" />
                  <el-option label="判断题" value="judge" />
                </el-select>
                <el-button type="primary" size="small" @click="addObjectiveGroup">确定</el-button>
              </div>
            </div>

            <el-table :data="objectiveQuestionList" size="small" border stripe class="question-table">
              <el-table-column prop="no" label="序号" width="50" />
              <el-table-column prop="groupLabel" label="大题号" width="70" />
              <el-table-column prop="subNo" label="小题号" width="70" />
              <el-table-column prop="score" label="满分" width="60" />
              <el-table-column label="答案" width="70">
                <template #default="{ row }">
                  <el-input
                    v-model="form.standardAnswers[row.no]"
                    size="small"
                    maxlength="10"
                    placeholder="答案"
                    @change="updateAnswer(row.no, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="questionTypeLabel" label="题型类型" width="80" />
              <el-table-column label="操作" width="130" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    :type="getQuestionRegion(row.no) ? 'success' : 'primary'"
                    @click="selectRegionByNo(row.no)"
                  >
                    {{ getQuestionRegion(row.no) ? '已框选' : '框选' }}
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteQuestion(row.no, 'choice')"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="question-summary">
              <span>数量: {{ objectiveCount }}题</span>
              <span>分值: {{ objectiveScore }}分</span>
            </div>

            <div class="btn-group">
              <el-button type="primary" class="confirm-btn" @click="confirmObjectiveAnswers">确认客观题答案</el-button>
              <el-button type="danger" plain @click="clearQuestions('choice')">清空客观题</el-button>
            </div>
          </el-collapse-item>

          <!-- 主观题 -->
          <el-collapse-item name="subjective">
            <template #title>
              <div class="collapse-title">
                <el-icon :size="18" color="#409EFF"><Edit /></el-icon>
                <span>主观题</span>
                <el-tag size="small" type="primary" effect="dark" class="tag-right">
                  {{ subjectiveCount }} 题
                </el-tag>
              </div>
            </template>
            
            <div class="question-group-form">
              <div class="form-row">
                <span class="form-label">从</span>
                <el-input v-model="subjectiveForm.startNo" type="number" size="small" placeholder="序号" class="form-input" />
                <span class="form-label">到</span>
                <el-input v-model="subjectiveForm.endNo" type="number" size="small" placeholder="题" class="form-input" />
                <el-input v-model="subjectiveForm.groupLabel" size="small" placeholder="大题号名称" class="form-input" />
                <el-input v-model="subjectiveForm.scorePerQuestion" type="number" size="small" placeholder="分/题" class="form-input" />
              </div>
              <div class="form-row">
                <el-select v-model="subjectiveForm.questionType" size="small" placeholder="请选择" class="form-select">
                  <el-option label="解答题" value="solution" />
                  <el-option label="填空题" value="fill" />
                  <el-option label="计算题" value="calculation" />
                  <el-option label="作文题" value="composition" />
                </el-select>
                <el-button type="primary" size="small" @click="addSubjectiveGroup">确定</el-button>
              </div>
            </div>

            <el-table :data="subjectiveQuestionList" size="small" border stripe class="question-table">
              <el-table-column prop="no" label="序号" width="50" />
              <el-table-column prop="groupLabel" label="大题号" width="70" />
              <el-table-column prop="subNo" label="小题号" width="70" />
              <el-table-column label="满分" width="80">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.score"
                    :min="0"
                    :max="100"
                    :step="0.5"
                    :precision="1"
                    size="small"
                    style="width: 70px"
                    @change="updateSubjectiveScore(row.no, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="答案" width="100">
                <template #default="{ row }">
                  <el-input
                    v-model="form.standardAnswers[row.no]"
                    size="small"
                    placeholder="参考答案"
                    @change="updateAnswer(row.no, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="questionTypeLabel" label="题型" width="80" />
              <el-table-column label="操作" width="130" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    :type="getQuestionRegion(row.no) ? 'success' : 'primary'"
                    @click="selectRegionByNo(row.no)"
                  >
                    {{ getQuestionRegion(row.no) ? '已框选' : '框选' }}
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteQuestion(row.no, 'subjective')"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="question-summary">
              <span>数量: {{ subjectiveCount }}题</span>
              <span>分值: {{ subjectiveScore }}分</span>
            </div>

            <div class="btn-group">
              <el-button type="primary" class="confirm-btn" @click="confirmSubjectiveAnswers">确认主观题答案</el-button>
              <el-button type="danger" plain @click="clearQuestions('subjective')">清空主观题</el-button>
            </div>
          </el-collapse-item>

          <!-- 学生信息 -->
          <el-collapse-item name="student">
            <template #title>
              <div class="collapse-title">
                <el-icon :size="18" color="#E6A23C"><User /></el-icon>
                <span>框选学生信息</span>
                <el-tag v-if="studentInfoConfirmed" size="small" type="success" effect="dark" class="tag-right">
                  已确认
                </el-tag>
                <el-tag v-else-if="hasStudentRegions" size="small" type="success" effect="dark" class="tag-right">
                  已设置
                </el-tag>
                <el-tag v-else size="small" type="warning" effect="dark" class="tag-right">
                  未设置
                </el-tag>
              </div>
            </template>
            
            <div class="student-info-section">
              <div class="section-header">
                <span class="section-title">使用场景</span>
                <el-button type="primary" link size="small" @click="showStudentExample = true">
                  查看框选示例
                </el-button>
              </div>
              
              <div class="usage-scenario">
                <p>1. 学生信息是能识别出学生的相关信息，如学生在试卷上填涂的学校、班级、学号、姓名、考场、座次、考号等信息；</p>
                <p>2. 框选学生信息区域后，教师批阅试卷时，如果存在疑问卷或者作答内容超出区域，可查看原卷，试卷页面隐藏框选的学生信息。</p>
              </div>
              
              <div class="student-info-status">
                <div class="status-item">
                  <span class="status-label">框选状态：</span>
                  <span v-if="hasStudentRegions" class="status-value success">已框选 {{ framedStudentFieldCount }} 个区域</span>
                  <span v-else class="status-value warning">未框选</span>
                </div>
              </div>

              <div class="student-field-list">
                <div v-for="f in studentFields" :key="f.key" class="student-field-item">
                  <span class="field-label">{{ f.label }}</span>
                  <span class="status-value" :class="getStudentRegion(f.key) ? 'success' : 'warning'">
                    {{ getStudentRegion(f.key) ? '已框选' : '未框选' }}
                  </span>
                  <el-button type="primary" link size="small" @click="selectRegionByField(f.key)">
                    {{ getStudentRegion(f.key) ? '重新框选' : '框选' }}
                  </el-button>
                </div>
              </div>
              
              <el-button
                type="primary"
                size="small"
                @click="startSelectStudentInfo"
                :disabled="!templateImageUrl"
                style="width: 100%; margin-bottom: 12px;"
              >
                {{ studentRegion ? '重新框选学生信息区域' : '框选学生信息区域' }}
              </el-button>
              
              <el-button
                type="primary"
                class="confirm-btn"
                @click="confirmStudentInfo"
                :disabled="!hasStudentRegions"
              >
                确认学生信息
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="panel-footer">
          <el-button @click="resetCurrentSubject">重置</el-button>
          <el-button type="primary" @click="saveCurrentSubject">保存配置</el-button>
          <el-button type="warning" plain @click="reprocessScans">重新处理扫描</el-button>
        </div>
      </div>
    </div>

    <!-- 批量设置答案对话框 -->
    <el-dialog v-model="showBatchAnswer" title="批量设置客观题答案" width="500px">
      <div class="batch-answer-desc">请按题号顺序输入答案（如：ABCDAB...）</div>
      <el-input
        v-model="batchAnswerText"
        type="textarea"
        :rows="4"
        placeholder="ABCDABCD..."
      />
      <template #footer>
        <el-button @click="showBatchAnswer = false">取消</el-button>
        <el-button type="primary" @click="applyBatchAnswer">确定</el-button>
      </template>
    </el-dialog>

    <!-- 客观题区域自动拆分对话框 -->
    <el-dialog
      v-model="showSplitDialog"
      title="自动拆分客观题区域"
      width="420px"
      destroy-on-close
      @closed="pendingSplitRegion = null"
    >
      <div class="split-dialog-desc">
        你框选了一个较大的客观题区域，可以按题号顺序自动拆分为多个小题区域。
      </div>
      <el-form :model="splitForm" label-width="90px" class="split-form">
        <el-form-item label="起始题号">
          <el-input v-model.number="splitForm.startNo" type="number" min="1" placeholder="起始题号" />
        </el-form-item>
        <el-form-item label="结束题号">
          <el-input v-model.number="splitForm.endNo" type="number" min="1" placeholder="结束题号" />
        </el-form-item>
        <el-form-item label="列数">
          <el-input v-model.number="splitForm.cols" type="number" min="1" placeholder="每行列题数" />
        </el-form-item>
        <el-form-item label="排列方向">
          <el-radio-group v-model="splitForm.direction">
            <el-radio label="horizontal">横向（从左到右）</el-radio>
            <el-radio label="vertical">纵向（从上到下）</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div class="split-preview">
        将生成 <strong>{{ splitCount }}</strong> 个小题区域（{{ splitRows }} 行 × {{ splitForm.cols }} 列，{{ splitDirectionText }}）
      </div>
      <template #footer>
        <el-button @click="cancelSplit">取消</el-button>
        <el-button type="primary" @click="confirmSplit">确定拆分</el-button>
      </template>
    </el-dialog>

    <!-- 学生信息框选示例对话框 -->
    <el-dialog v-model="showStudentExample" title="提示" width="650px">
      <div class="example-content">
        <div class="operation-instruction">
          操作说明：左击拖拽鼠标画矩形，在试卷上框选能够识别到学生信息的区域，如：学生所在学校、班级、姓名、考场、座次、学号、考号等。
        </div>
        <div class="example-image">
          <div class="mock-answer-sheet">
            <!-- 试卷顶部信息 -->
            <div class="exam-header">
              <div class="exam-title">七年级 地理</div>
              <div class="exam-subtitle">全卷共4页，满分100分，考试时间60分钟</div>
            </div>
            
            <!-- 准考证区域 -->
            <div class="exam-code-row">
              <div class="exam-code-label">准考证粘贴处</div>
              <div class="exam-code-box">0000041</div>
            </div>
            
            <!-- 学生信息区域（带绿色框） -->
            <div class="student-info-area-with-frame">
              <div class="student-info-label">学生信息</div>
              <div class="student-info-content">
                <div class="info-row">
                  <span class="info-label">考号：</span>
                  <span class="info-barcode">20210307</span>
                  <span class="info-label">班级：</span>
                  <span class="info-text">七(3)班</span>
                  <span class="info-label">姓名：</span>
                  <span class="info-text">张三</span>
                </div>
                <div class="fill-area">
                  <div class="fill-grid">
                    <div class="fill-col" v-for="n in 9" :key="n">
                      <div class="fill-digit">{{ n - 1 }}</div>
                      <div class="fill-circles">
                        <div
                          v-for="d in 10"
                          :key="d"
                          class="fill-circle"
                          :class="{ filled: (n === 3 && d === 3) || (n === 4 && d === 2) || (n === 5 && d === 1) || (n === 6 && d === 4) || (n === 7 && d === 5) || (n === 8 && d === 9) }"
                        >
                          {{ d - 1 }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 客观题区域 -->
            <div class="objective-area-demo">
              <div class="objective-title">一、单项选择题（共30题，每题1分，共30分）</div>
              <div class="option-table">
                <div class="option-row" v-for="row in 4" :key="row">
                  <div class="option-cell" v-for="col in 8" :key="col">
                    <span class="option-no">{{ (row - 1) * 8 + col }}</span>
                    <span class="option-letters">
                      <span class="option-letter">A</span>
                      <span class="option-letter">B</span>
                      <span class="option-letter filled">C</span>
                      <span class="option-letter">D</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 绿色标注框 -->
          <div class="annotation-frame">
            <div class="annotation-label">学生信息</div>
          </div>
        </div>
        <div class="example-desc">
          <p><strong>说明：</strong></p>
          <p>1. 用鼠标在左侧答题卡画布上拖拽，画出一个矩形框</p>
          <p>2. 矩形框应完整包含学生信息区域（考号、班级、姓名、填涂区等）</p>
          <p>3. 框选完成后点击"确认学生信息"按钮保存</p>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showStudentExample = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExam } from '@/api/exam'
import {
  getAnswerCardConfig,
  saveAnswerCardConfig,
  uploadAnswerCardTemplate
} from '@/api/answerCard'
import { reprocessExamSubject } from '@/api/scan'
import AnswerCardCanvas from './AnswerCardCanvas.vue'

const route = useRoute()
const router = useRouter()
const examId = Number(route.params.id)
const querySubjectId = route.query.subjectId ? Number(route.query.subjectId) : null

const loading = ref(false)
const examName = ref('')
const subjects = ref([])
const currentSubjectId = ref(null)
const templateImageUrl = ref('')
const pageCount = ref(1)
const activeTool = ref('select')
const zoom = ref(100)
const activeCollapse = ref(['objective', 'subjective', 'student'])
const selectedRegion = ref(null)
const canvasComp = ref(null)
const fileInput = ref(null)
const showBatchAnswer = ref(false)
const batchAnswerText = ref('')
const pendingRegionTarget = ref(null)
const showStudentExample = ref(false)
const studentInfoConfirmed = ref(false)
const showSplitDialog = ref(false)
const pendingSplitRegion = ref(null)
const templatePagePreviews = ref([])
const splitForm = reactive({
  startNo: '',
  endNo: '',
  cols: 1,
  direction: 'horizontal'
})

const objectiveForm = reactive({
  startNo: '',
  endNo: '',
  groupLabel: '',
  scorePerQuestion: '',
  questionType: 'single'
})

const subjectiveForm = reactive({
  startNo: '',
  endNo: '',
  groupLabel: '',
  scorePerQuestion: '',
  questionType: 'solution'
})


const questionTypeMap = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题',
  solution: '解答题',
  fill: '填空题',
  calculation: '计算题',
  composition: '作文题'
}

const studentFields = [
  { key: 'school', label: '学校' },
  { key: 'class', label: '班级' },
  { key: 'name', label: '姓名' },
  { key: 'studentNo', label: '学号' },
  { key: 'examNo', label: '考号' },
  { key: 'seatNo', label: '座位号' }
]

const form = reactive({
  templateId: null,
  templateImage: '',
  questionsConfig: {
    studentNumber: {
      configType: 'handwrite',
      digits: 10,
      position: { x: 20, y: 20, w: 160, h: 30 }
    },
    questionGroups: []
  },
  standardAnswers: {},
  markPoints: [],
  regions: []
})

const allRegions = ref([])
const historyStack = ref([])
const historyIndex = ref(-1)

const pushHistory = () => {
  const snapshot = JSON.stringify(allRegions.value)
  // 如果当前不在栈顶，移除后面的
  if (historyIndex.value < historyStack.value.length - 1) {
    historyStack.value = historyStack.value.slice(0, historyIndex.value + 1)
  }
  historyStack.value.push(snapshot)
  if (historyStack.value.length > 50) {
    historyStack.value.shift()
  } else {
    historyIndex.value++
  }
}

const handleUndo = () => {
  if (historyIndex.value <= 0) return
  historyIndex.value--
  allRegions.value = JSON.parse(historyStack.value[historyIndex.value])
}

const handleRedo = () => {
  if (historyIndex.value >= historyStack.value.length - 1) return
  historyIndex.value++
  allRegions.value = JSON.parse(historyStack.value[historyIndex.value])
}

watch(allRegions, (newVal, oldVal) => {
  if (oldVal && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
    pushHistory()
  }
}, { deep: true })

watch(activeTool, (newTool) => {
  if (newTool === 'select' && pendingRegionTarget.value) {
    pendingRegionTarget.value = null
  }
})

const objectiveQuestionList = computed(() => {
  const list = []
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'choice') {
      for (let i = 0; i < group.count; i++) {
        const no = group.startNo + i
        list.push({
          no: String(no),
          groupLabel: group.groupLabel || '',
          subNo: String(no),
          score: group.scorePerQuestion,
          questionType: group.questionType || 'single',
          questionTypeLabel: questionTypeMap[group.questionType] || '选择题'
        })
      }
    }
  }
  return list
})

const subjectiveQuestionList = computed(() => {
  const list = []
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'subjective') {
      const individual = group.individualScores || {}
      for (let i = 0; i < group.count; i++) {
        const no = group.startNo + i
        list.push({
          no: String(no),
          groupLabel: group.groupLabel || '',
          subNo: String(no),
          score: individual[String(no)] ?? group.scorePerQuestion,
          questionType: group.questionType || 'solution',
          questionTypeLabel: questionTypeMap[group.questionType] || '解答题'
        })
      }
    }
  }
  return list
})

const objectiveCount = computed(() => {
  let count = 0
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'choice') {
      count += group.count
    }
  }
  return count
})

const objectiveScore = computed(() => {
  let score = 0
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'choice') {
      score += group.count * (group.scorePerQuestion || 0)
    }
  }
  return score
})

const subjectiveCount = computed(() => {
  let count = 0
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'subjective') {
      count += group.count
    }
  }
  return count
})

const subjectiveScore = computed(() => {
  let score = 0
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type === 'subjective') {
      const individual = group.individualScores || {}
      for (let i = 0; i < group.count; i++) {
        const no = String(group.startNo + i)
        score += individual[no] ?? (group.scorePerQuestion || 0)
      }
    }
  }
  return score
})

const objectiveRegions = computed(() => allRegions.value.filter(r => r.type === 'objective'))
const subjectiveRegions = computed(() => allRegions.value.filter(r => r.type === 'subjective'))
const studentRegions = computed(() => allRegions.value.filter(r => r.type === 'student'))
const studentRegion = computed(() => allRegions.value.find(r => r.type === 'student' && r.field === 'studentInfo'))
const hasStudentRegions = computed(() => studentRegions.value.length > 0)
const framedStudentFieldCount = computed(() =>
  studentFields.filter(f => allRegions.value.some(r => r.type === 'student' && r.field === f.key)).length
)

const splitCount = computed(() => {
  const start = parseInt(splitForm.startNo) || 0
  const end = parseInt(splitForm.endNo) || 0
  if (start <= 0 || end <= 0 || end < start) return 0
  return end - start + 1
})

const splitRows = computed(() => {
  if (!splitForm.cols || splitForm.cols < 1) return 0
  return Math.ceil(splitCount.value / splitForm.cols)
})

const splitDirectionText = computed(() => {
  return splitForm.direction === 'vertical' ? '先从上到下，再从左到右' : '先从左到右，再从上到下'
})

const getUnassignedObjectiveQuestions = () => {
  const assigned = new Set(allRegions.value.filter(r => r.type === 'objective').map(r => String(r.questionNo)))
  return objectiveQuestionList.value.filter(q => !assigned.has(String(q.no)))
}

const getRegionByNo = (no, type) => {
  return allRegions.value.find(r => r.type === type && String(r.questionNo) === String(no))
}

const getQuestionRegion = (no) => {
  const type = objectiveQuestionList.value.some(q => String(q.no) === String(no)) ? 'objective' : 'subjective'
  return getRegionByNo(no, type)
}

const getStudentRegion = (field) => {
  return allRegions.value.find(r => r.type === 'student' && r.field === field)
}

const selectRegionByNo = (no, type) => {
  const regionType = type || (objectiveQuestionList.value.some(q => String(q.no) === String(no)) ? 'objective' : 'subjective')
  const region = getRegionByNo(no, regionType)
  if (region) {
    selectedRegion.value = region
    canvasComp.value?.selectByKey(region.key)
    pendingRegionTarget.value = null
  } else {
    activeTool.value = regionType
    pendingRegionTarget.value = { type: regionType, questionNo: String(no) }
    ElMessage.info(`请在左侧画布框选第${no}题区域`)
  }
}

const selectRegionByField = (field) => {
  const region = getStudentRegion(field)
  if (region) {
    selectedRegion.value = region
    canvasComp.value?.selectByKey(region.key)
    pendingRegionTarget.value = null
  } else {
    activeTool.value = 'student'
    pendingRegionTarget.value = { type: 'student', field }
    const fieldLabel = studentFields.find(f => f.key === field)?.label || field
    ElMessage.info(`请在左侧画布框选${fieldLabel}区域`)
  }
}

const startSelectStudentInfo = () => {
  if (studentRegion.value) {
    allRegions.value = allRegions.value.filter(r => !(r.type === 'student' && r.field === 'studentInfo'))
  }
  activeTool.value = 'student'
  pendingRegionTarget.value = { type: 'student', field: 'studentInfo' }
  ElMessage.info('请在左侧画布框选学生信息区域')
}

const confirmStudentInfo = () => {
  if (!hasStudentRegions.value) {
    ElMessage.warning('请先框选学生信息区域')
    return
  }
  studentInfoConfirmed.value = true
  activeTool.value = 'select'
  ElMessage.success('学生信息已确认')
}

const addObjectiveGroup = () => {
  const startNo = parseInt(objectiveForm.startNo)
  const endNo = parseInt(objectiveForm.endNo)
  
  if (isNaN(startNo) || isNaN(endNo) || startNo > endNo) {
    ElMessage.warning('请输入有效的序号范围')
    return
  }
  
  const count = endNo - startNo + 1
  const newGroup = {
    type: 'choice',
    startNo,
    count,
    scorePerQuestion: parseInt(objectiveForm.scorePerQuestion) || 3,
    groupLabel: objectiveForm.groupLabel,
    questionType: objectiveForm.questionType,
    options: ['A', 'B', 'C', 'D']
  }
  
  form.questionsConfig.questionGroups.push(newGroup)
  objectiveForm.startNo = ''
  objectiveForm.endNo = ''
  objectiveForm.groupLabel = ''
  objectiveForm.scorePerQuestion = ''
  ElMessage.success('客观题组添加成功')
}

const addSubjectiveGroup = () => {
  const startNo = parseInt(subjectiveForm.startNo)
  const endNo = parseInt(subjectiveForm.endNo)
  
  if (isNaN(startNo) || isNaN(endNo) || startNo > endNo) {
    ElMessage.warning('请输入有效的序号范围')
    return
  }
  
  const count = endNo - startNo + 1
  const newGroup = {
    type: 'subjective',
    startNo,
    count,
    scorePerQuestion: parseInt(subjectiveForm.scorePerQuestion) || 10,
    groupLabel: subjectiveForm.groupLabel,
    questionType: subjectiveForm.questionType
  }
  
  form.questionsConfig.questionGroups.push(newGroup)
  subjectiveForm.startNo = ''
  subjectiveForm.endNo = ''
  subjectiveForm.groupLabel = ''
  subjectiveForm.scorePerQuestion = ''
  ElMessage.success('主观题组添加成功')
}

const deleteQuestion = (no, type) => {
  const noNum = parseInt(no)
  const groups = form.questionsConfig.questionGroups
  const idx = groups.findIndex(g => g.type === type && noNum >= g.startNo && noNum < g.startNo + g.count)
  if (idx === -1) return

  const group = groups[idx]
  const endNo = group.startNo + group.count - 1

  // 同步删除对应框选区域
  allRegions.value = allRegions.value.filter(r => !(r.type === type && String(r.questionNo) === String(no)))

  if (group.count === 1) {
    groups.splice(idx, 1)
  } else if (noNum === group.startNo) {
    group.startNo++
    group.count--
  } else if (noNum === endNo) {
    group.count--
  } else {
    // 中间删除，拆分为两个组
    const leftCount = noNum - group.startNo
    const rightStart = noNum + 1
    const rightCount = endNo - noNum
    const rightGroup = {
      ...group,
      startNo: rightStart,
      count: rightCount
    }
    group.count = leftCount
    groups.splice(idx + 1, 0, rightGroup)
  }

  // 清理该题的分数/答案记录
  if (group.individualScores) {
    delete group.individualScores[String(no)]
  }
  delete form.standardAnswers[String(no)]

  ElMessage.success(`已删除第 ${no} 题`)
}

const clearQuestions = (type) => {
  ElMessageBox.confirm(`确定清空所有${type === 'choice' ? '客观题' : '主观题'}吗？`, '提示', {
    type: 'warning'
  }).then(() => {
    const groups = form.questionsConfig.questionGroups
    // 删除该类型题组
    for (let i = groups.length - 1; i >= 0; i--) {
      if (groups[i].type === type) {
        groups.splice(i, 1)
      }
    }
    // 同步删除对应框选区域
    allRegions.value = allRegions.value.filter(r => r.type !== type)
    // 清理答案记录
    if (type === 'choice') {
      objectiveQuestionList.value.forEach(q => {
        delete form.standardAnswers[q.no]
      })
    } else {
      subjectiveQuestionList.value.forEach(q => {
        delete form.standardAnswers[q.no]
      })
    }
    ElMessage.success(`已清空${type === 'choice' ? '客观题' : '主观题'}`)
  }).catch(() => {})
}

const updateAnswer = (no, value) => {
  form.standardAnswers[no] = value
}

const updateSubjectiveScore = (no, score) => {
  const noStr = String(no)
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type !== 'subjective') continue
    if (no >= group.startNo && no < group.startNo + group.count) {
      if (!group.individualScores) {
        group.individualScores = {}
      }
      group.individualScores[noStr] = Number(score)
      // 同步更新已框选区域的分值
      const region = getRegionByNo(noStr, 'subjective')
      if (region) {
        region.score = Number(score)
      }
      break
    }
  }
}

const confirmObjectiveAnswers = () => {
  let setCount = 0
  for (const q of objectiveQuestionList.value) {
    if (form.standardAnswers[q.no]) {
      setCount++
    }
  }
  ElMessage.success(`已确认 ${setCount} 道客观题答案，共 ${objectiveQuestionList.value.length} 道`)
}

const confirmSubjectiveAnswers = () => {
  let setCount = 0
  for (const q of subjectiveQuestionList.value) {
    if (form.standardAnswers[q.no]) {
      setCount++
    }
  }
  ElMessage.success(`已确认 ${setCount} 道主观题答案，共 ${subjectiveQuestionList.value.length} 道`)
}

const onRegionSelected = (region) => {
  selectedRegion.value = region
}

const onRegionCreated = (region) => {
  if (pendingRegionTarget.value) {
    pendingRegionTarget.value = null
    activeTool.value = 'select'
  }

  // 主观题区域：同步当前小题分值
  if (region.type === 'subjective') {
    const row = subjectiveQuestionList.value.find(q => String(q.no) === String(region.questionNo))
    if (row) {
      region.score = Number(row.score)
    }
  }

  // 客观题区域：尝试自动拆分
  if (region.type === 'objective') {
    const unassigned = getUnassignedObjectiveQuestions()
    if (unassigned.length > 0) {
      // 移除刚创建的大区域，改为拆分
      allRegions.value = allRegions.value.filter(r => r.key !== region.key)
      pendingSplitRegion.value = region
      const startNo = parseInt(region.questionNo) || parseInt(unassigned[0].no)
      const endNo = parseInt(unassigned[unassigned.length - 1].no)
      splitForm.startNo = startNo
      splitForm.endNo = endNo
      splitForm.cols = suggestCols(region.w, region.h, unassigned.length + 1)
      showSplitDialog.value = true
    }
  }
}

const suggestCols = (w, h, count) => {
  if (!w || !h || !count) return 1
  // 根据区域宽高比和题目数量估算列数
  const ratio = w / h
  if (ratio < 0.8) return 1
  if (ratio > 2.5) return Math.min(count, 8)
  if (ratio > 1.8) return Math.min(count, 6)
  if (ratio > 1.2) return Math.min(count, 5)
  if (ratio > 0.9) return Math.min(count, 4)
  return 1
}

const cancelSplit = () => {
  pendingSplitRegion.value = null
  showSplitDialog.value = false
}

const confirmSplit = () => {
  if (!pendingSplitRegion.value) {
    showSplitDialog.value = false
    return
  }
  const startNo = parseInt(splitForm.startNo)
  const endNo = parseInt(splitForm.endNo)
  const cols = parseInt(splitForm.cols)

  if (isNaN(startNo) || isNaN(endNo) || isNaN(cols) || startNo > endNo || cols < 1) {
    ElMessage.warning('请输入有效的拆分参数')
    return
  }

  const total = endNo - startNo + 1
  const { x, y, w, h, page } = pendingSplitRegion.value
  const rows = Math.ceil(total / cols)
  const cellW = w / cols
  const cellH = h / rows
  const direction = splitForm.direction || 'horizontal'

  const newRegions = []
  for (let i = 0; i < total; i++) {
    const questionNo = startNo + i
    let row, col
    if (direction === 'vertical') {
      // 纵向：先从上到下，再从左到右
      col = Math.floor(i / rows)
      row = i % rows
    } else {
      // 横向：先从左到右，再从上到下
      row = Math.floor(i / cols)
      col = i % cols
    }
    newRegions.push({
      key: `objective_${page}_${Date.now()}_${i}`,
      type: 'objective',
      page,
      questionNo: String(questionNo),
      field: null,
      x: Math.round(x + col * cellW),
      y: Math.round(y + row * cellH),
      w: Math.round(col === cols - 1 ? (x + w) - (x + col * cellW) : cellW),
      h: Math.round(row === rows - 1 ? (y + h) - (y + row * cellH) : cellH)
    })
  }

  allRegions.value = [...allRegions.value, ...newRegions]
  pendingSplitRegion.value = null
  nextTick(() => {
    showSplitDialog.value = false
    ElMessage.success(`已拆分为 ${total} 道客观题区域`)
  })
}

const handleDelete = () => {
  if (!selectedRegion.value) return
  canvasComp.value?.deleteSelected()
}

const handleReplace = () => {
  fileInput.value?.click()
}

const handleClear = () => {
  ElMessageBox.confirm('确定清空所有模板和框选区域吗？', '提示', {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    templateImageUrl.value = ''
    allRegions.value = []
    form.templateImage = ''
    ElMessage.success('已清空')
  }).catch(() => {})
}

const handleSplit = () => {
  ElMessageBox.prompt('设置试卷页数', '拆试卷', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: String(pageCount.value),
    inputValidator: (val) => {
      const n = parseInt(val)
      if (isNaN(n) || n < 1 || n > 10) return '请输入1-10之间的数字'
      return true
    }
  }).then(({ value }) => {
    pageCount.value = parseInt(value)
    ElMessage.success(`已设置为 ${pageCount.value} 页`)
  }).catch(() => {})
}

const onFileChange = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
    ElMessage.warning('请上传图片或 PDF 文件')
    return
  }

  loading.value = true
  try {
    const res = await uploadAnswerCardTemplate(file, examId, currentSubjectId.value)
    // 后端对 PDF 返回第一页 PNG 预览；图片直接返回原图
    templateImageUrl.value = res.previewUrl || res.fileUrl || ''
    templatePagePreviews.value = res.pagePreviews || [templateImageUrl.value]
    form.templateImage = res.fileUrl || ''
    if (res.pageCount) {
      pageCount.value = res.pageCount
    }
    loading.value = false
    ElMessage.success('模板上传成功')
  } catch (error) {
    loading.value = false
    ElMessage.error(error?.response?.data?.detail || '上传失败')
  }
  e.target.value = ''
}

const applyBatchAnswer = () => {
  const answers = batchAnswerText.value.toUpperCase().replace(/\s/g, '')
  if (!answers) {
    ElMessage.warning('请输入答案')
    return
  }
  const letters = answers.split('')
  for (let i = 0; i < objectiveQuestionList.value.length && i < letters.length; i++) {
    form.standardAnswers[objectiveQuestionList.value[i].no] = letters[i]
  }
  ElMessage.success('批量设置成功')
  showBatchAnswer.value = false
  batchAnswerText.value = ''
}

onMounted(async () => {
  loading.value = true
  try {
    const examRes = await getExam(examId)
    examName.value = examRes.examName
    subjects.value = examRes.subjects || []

    if (subjects.value.length > 0) {
      const defaultSubject = querySubjectId && subjects.value.some(s => s.subjectId === querySubjectId)
        ? querySubjectId
        : subjects.value[0].subjectId
      currentSubjectId.value = defaultSubject
      await loadSubjectConfig(currentSubjectId.value)
    }
    pushHistory()
  } catch (error) {
    ElMessage.error('加载考试信息失败')
  } finally {
    loading.value = false
  }
})

const loadSubjectConfig = async (subjectId) => {
  try {
    const res = await getAnswerCardConfig(examId, subjectId)
    applyConfig(res)
  } catch (error) {
    // 尚未配置，使用默认
    form.questionsConfig.questionGroups = []
    form.standardAnswers = {}
    form.markPoints = []
    allRegions.value = []
    templateImageUrl.value = ''
  }
}

const applyConfig = (res) => {
  form.templateId = res.templateId
  form.questionsConfig = res.questionsConfig || form.questionsConfig
  form.standardAnswers = res.standardAnswers || {}
  form.markPoints = res.markPoints || []
  form.regions = res.regions || []

  if (!form.questionsConfig.studentNumber) {
    form.questionsConfig.studentNumber = {
      configType: 'handwrite',
      digits: 10,
      position: { x: 20, y: 20, w: 160, h: 30 }
    }
  }
  if (!form.questionsConfig.questionGroups) {
    form.questionsConfig.questionGroups = []
  }

  // 清除旧版本自动生成的默认题目组（没有 type 的无效数据）
  form.questionsConfig.questionGroups = form.questionsConfig.questionGroups.filter(group => {
    return group.type && String(group.type).trim() !== ''
  })

  // 恢复 regions
  allRegions.value = form.regions.length > 0 ? form.regions : [
    ...form.markPoints.map((r, i) => ({
      key: `subj_${i}`,
      type: 'subjective',
      page: r.page || 1,
      questionNo: r.questionNo,
      x: r.x, y: r.y, w: r.w, h: r.h,
      score: r.score
    }))
  ]

  // 确保主观题区域 score 与 individualScores 一致
  for (const group of form.questionsConfig.questionGroups) {
    if (group.type !== 'subjective') continue
    const individual = group.individualScores || {}
    for (let i = 0; i < group.count; i++) {
      const no = String(group.startNo + i)
      const score = individual[no] ?? group.scorePerQuestion
      const region = allRegions.value.find(r => r.type === 'subjective' && String(r.questionNo) === no)
      if (region && score !== undefined) {
        region.score = Number(score)
      }
    }
  }

  if (res.templateImage) {
    templateImageUrl.value = res.templateImage
  }
  if (res.pageCount) {
    pageCount.value = res.pageCount
  }
  if (res.pagePreviews && res.pagePreviews.length > 0) {
    templatePagePreviews.value = res.pagePreviews
  } else {
    templatePagePreviews.value = res.templateImage ? [res.templateImage] : []
  }
}

const saveCurrentSubject = async () => {
  // 过滤非法区域，确保坐标为有效整数
  const validRegions = allRegions.value.filter(r => {
    return r && r.key && r.type && r.page > 0 &&
      Number.isFinite(r.x) && Number.isFinite(r.y) &&
      Number.isFinite(r.w) && Number.isFinite(r.h) &&
      r.w > 0 && r.h > 0
  }).map(r => ({
    key: r.key,
    type: r.type,
    page: r.page,
    questionNo: r.questionNo ?? null,
    field: r.field ?? null,
    x: Math.round(r.x),
    y: Math.round(r.y),
    w: Math.round(r.w),
    h: Math.round(r.h),
    score: Number.isFinite(r.score) ? Number(r.score) : null
  }))

  form.regions = validRegions
  form.markPoints = validRegions
    .filter(r => r.type === 'subjective' && r.questionNo)
    .map(r => ({
      questionNo: String(r.questionNo),
      page: r.page,
      x: r.x, y: r.y, w: r.w, h: r.h,
      score: r.score
    }))

  const payload = {
    examId,
    subjectId: currentSubjectId.value,
    templateId: form.templateId || 1,
    templateImage: form.templateImage || templateImageUrl.value,
    pageCount: pageCount.value,
    pagePreviews: templatePagePreviews.value,
    questionsConfig: form.questionsConfig,
    standardAnswers: form.standardAnswers,
    markPoints: form.markPoints,
    regions: form.regions
  }

  try {
    await saveAnswerCardConfig(payload)
    ElMessage.success('答题卡配置保存成功')
  } catch (error) {
    const detail = error?.response?.data?.detail
    if (Array.isArray(detail)) {
      const msg = detail.map(e => `${e.loc?.join('.') || ''}: ${e.msg}`).join('; ')
      ElMessage.error(`保存失败：${msg}`)
    } else if (detail) {
      ElMessage.error(`保存失败：${detail}`)
    } else {
      ElMessage.error('保存失败')
    }
    console.error('保存答题卡配置失败:', error)
  }
}

const resetCurrentSubject = () => {
  ElMessageBox.confirm('确定重置当前科目配置吗？', '提示', {
    type: 'warning'
  }).then(() => {
    loadSubjectConfig(currentSubjectId.value)
    ElMessage.success('已重置')
  }).catch(() => {})
}

const reprocessScans = async () => {
  if (!currentSubjectId.value) {
    ElMessage.warning('请先选择科目')
    return
  }
  try {
    await ElMessageBox.confirm(
      '重新处理将使用当前答题卡配置重新切割所有已上传的扫描页，是否继续？',
      '重新处理扫描',
      { type: 'warning' }
    )
    const res = await reprocessExamSubject(examId, currentSubjectId.value)
    ElMessage.success(res.message || '已重新提交处理')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重新处理扫描失败:', error)
    }
  }
}
</script>

<style scoped>
.answer-card-config-page {
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.page-header {
  background: #fff;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f2f5;
}

.canvas-toolbar {
  background: #fff;
  padding: 8px 16px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.zoom-label {
  font-size: 13px;
  color: #606266;
  min-width: 50px;
  text-align: center;
}

.canvas-scroll {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.empty-template {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.right-panel {
  width: 340px;
  background: #fff;
  border-left: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stats-row {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
}

.stat-num {
  font-weight: bold;
  color: #303133;
}

.stat-score {
  color: #409EFF;
  font-weight: bold;
  margin-left: 4px;
}

.panel-collapse {
  flex: 1;
  overflow-y: auto;
  border: none;
  --el-collapse-border-color: transparent;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

.tag-right {
  margin-left: auto;
}

.panel-toolbar {
  padding: 8px 0;
}

.question-list {
  max-height: 300px;
  overflow-y: auto;
}

.question-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  gap: 8px;
  transition: background 0.2s;
}

.question-item:hover {
  background: #f5f7fa;
}

.question-item.selected {
  background: #ecf5ff;
}

.q-no {
  width: 36px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.q-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.q-type {
  font-size: 12px;
  color: #909399;
}

.q-score {
  font-size: 11px;
  color: #606266;
}

.q-answer {
  font-size: 12px;
  min-width: 50px;
  text-align: center;
}

.unset {
  color: #F56C6C;
  font-size: 12px;
}

.q-status {
  font-size: 16px;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.student-item:hover {
  background: #f5f7fa;
}

.student-item.selected {
  background: #ecf5ff;
}

.s-label {
  font-size: 13px;
}

.s-status {
  font-size: 16px;
}

.count-row {
  text-align: right;
  font-size: 12px;
  color: #606266;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
  margin-top: 8px;
}

.panel-footer {
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}

.panel-footer .el-button {
  flex: 1;
}

.batch-answer-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.split-dialog-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 16px;
  line-height: 1.6;
}

.split-form .el-form-item {
  margin-bottom: 12px;
}

.split-preview {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  font-size: 13px;
  color: #606266;
  text-align: center;
}

.question-group-form {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #ebeef5;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
}

.form-input {
  width: 70px;
}

.form-select {
  flex: 1;
}

.question-table {
  margin-bottom: 12px;
}

.question-table .el-input {
  width: 100%;
}

.question-summary {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  margin-bottom: 12px;
}

.btn-group {
  display: flex;
  gap: 10px;
}

.confirm-btn {
  flex: 1;
}

.answer-set {
  color: #67C23A;
  font-weight: 500;
}

.student-info-section {
  padding: 8px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.usage-scenario {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.usage-scenario p {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
}

.usage-scenario p:last-child {
  margin-bottom: 0;
}

.student-info-status {
  margin-bottom: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.status-label {
  color: #606266;
}

.status-value.success {
  color: #67C23A;
  font-weight: 500;
}

.status-value.warning {
  color: #E6A23C;
  font-weight: 500;
}

.student-field-list {
  margin-bottom: 12px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  overflow: hidden;
}

.student-field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  font-size: 13px;
}

.student-field-item + .student-field-item {
  border-top: 1px solid #F2F6FC;
}

.student-field-item .field-label {
  flex: 1;
  color: #606266;
}

.example-content {
  padding: 10px 0;
}

.operation-instruction {
  color: #F56C6C;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 4px;
}

.example-image {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.mock-answer-sheet {
  position: relative;
  width: 100%;
  max-width: 500px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 20px;
}

.exam-header {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #ebeef5;
}

.exam-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 6px;
}

.exam-subtitle {
  font-size: 11px;
  color: #909399;
}

.exam-code-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.exam-code-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.exam-code-box {
  flex: 1;
  font-family: monospace;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  letter-spacing: 3px;
  text-align: center;
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 3px;
}

.student-info-area-with-frame {
  position: relative;
  border: 2px solid #67C23A;
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 16px;
  background: #f0f9eb;
}

.student-info-label {
  position: absolute;
  top: -11px;
  left: 12px;
  background: #67C23A;
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 500;
}

.student-info-content {
  padding-top: 4px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.info-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.info-barcode {
  font-family: monospace;
  font-size: 13px;
  font-weight: bold;
  color: #303133;
  letter-spacing: 2px;
}

.info-text {
  font-size: 12px;
  color: #303133;
}

.fill-area {
  margin-top: 8px;
}

.fill-grid {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.fill-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.fill-digit {
  font-size: 10px;
  color: #909399;
  font-weight: 500;
}

.fill-circles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fill-circle {
  width: 14px;
  height: 14px;
  border: 1px solid #909399;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  color: #909399;
}

.fill-circle.filled {
  background: #303133;
  color: #fff;
  border-color: #303133;
}

.objective-area-demo {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
}

.objective-title {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.option-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-row {
  display: flex;
  gap: 8px;
}

.option-cell {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
}

.option-no {
  font-size: 10px;
  color: #909399;
  min-width: 16px;
}

.option-letters {
  display: flex;
  gap: 2px;
}

.option-letter {
  width: 12px;
  height: 12px;
  border: 1px solid #c0c4cc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  color: #909399;
}

.option-letter.filled {
  background: #303133;
  color: #fff;
  border-color: #303133;
}

.annotation-frame {
  position: absolute;
  top: 116px;
  left: 30px;
  right: 30px;
  height: 130px;
  border: 2px solid #67C23A;
  border-radius: 4px;
  pointer-events: none;
}

.annotation-label {
  position: absolute;
  top: -11px;
  left: 12px;
  background: #67C23A;
  color: #fff;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 3px;
  font-weight: 500;
}

.example-desc {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
}

.example-desc p {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.example-desc p:last-child {
  margin-bottom: 0;
}
</style>