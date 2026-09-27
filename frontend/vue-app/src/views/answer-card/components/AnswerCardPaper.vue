<template>
  <div class="paper-pages">
    <div
      v-for="(page, pageIdx) in pages"
      :key="pageIdx"
      class="paper"
      :class="[layoutClass, colorClass, { 'not-first': pageIdx > 0 }]"
      :style="paperStyle"
      ref="paperRef"
    >
      <div v-if="pageIdx === 0" class="first-page-header">
        <!-- 顶部标题 -->
        <div class="paper-title">
          <input
            v-if="!readonly"
            :value="config.title"
            @input="onTitleInput"
            class="title-input"
            placeholder="请输入答题卡标题"
          />
          <div v-else class="title-text">{{ config.title || '请输入答题卡标题' }}</div>
        </div>

        <!-- 上部分区：左侧信息 + 右侧准考证号 -->
        <div class="top-section">
          <div class="top-left" :style="topLeftStyle">
            <!-- 考生信息点 -->
            <div class="student-basic">
              <span v-for="field in studentInfo.fields" :key="field.id" class="basic-item">
                {{ field.label || '信息' }}：{{ field.placeholder || '________' }}
              </span>
            </div>

            <!-- 注意事项 -->
            <div class="notes-box" v-if="config.showNotes">
              <div class="notes-title">注意事项：</div>
              <p>1、请注意客观题填涂需清晰，完整覆盖选项。</p>
              <p>2、保持卡面清洁，不要折叠，不要弄破。</p>
              <div class="notes-marks">
                <div class="mark-item">
                  <span>正确填涂</span>
                  <span class="mark-box filled" />
                </div>
                <div class="mark-item">
                  <span>缺考填涂标记</span>
                  <span class="mark-box" />
                </div>
              </div>
            </div>
          </div>

          <div class="top-right" :style="topRightStyle">
            <div class="exam-no-header">
              <span class="exam-no-label">准考证号</span>
              <el-button v-if="!readonly" type="primary" link size="small" class="edit-btn" @click="emit('edit-student-info')">
                编辑
              </el-button>
            </div>

            <!-- 准考证号输入与填涂区 -->
            <div class="exam-no-wrap" v-if="showBubbleGrid">
              <div class="exam-no-inputs">
                <div v-for="d in digits" :key="`in-${d}`" class="no-input-box">
                  <input class="digit-input" maxlength="1" />
                </div>
              </div>
              <div class="bubble-grid">
                <div class="bubble-row" v-for="row in 10" :key="`row-${row}`">
                  <div class="bubble-cell" v-for="d in digits" :key="`cell-${row}-${d}`">
                    {{ row - 1 }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 仅手写考号 -->
            <div class="exam-no-inputs-only" v-else>
              <div v-for="d in digits" :key="`in-${d}`" class="no-input-box">
                <input class="digit-input" maxlength="1" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="sub-page-header">
        <div class="sub-page-title">{{ config.title || '答题卡' }}</div>
        <div class="sub-page-no">第 {{ pageIdx + 1 }} 页</div>
      </div>

      <!-- 答题区域 -->
      <div class="sections-container" :style="sectionsStyle">
        <div
          v-for="(section, idx) in page.sections"
          :key="section.id || idx"
          class="section-block"
        >
          <div class="section-header">
            <span class="section-title">{{ section.groupNo ? section.groupNo + '、' : '' }}{{ section.title || sectionTypeLabel(section.type) }}</span>
            <span class="section-score" v-if="section.score">（共{{ section.count }}题，{{ section.score }}分）</span>
          </div>

          <!-- 客观题 -->
          <div v-if="section.type === 'choice'" class="choice-area">
            <div v-if="section.subQuestions && section.subQuestions.length" class="choice-table">
              <div v-for="(col, cIdx) in choiceColumns(section)" :key="cIdx" class="choice-column">
                <div v-for="(q, qIdx) in col" :key="qIdx" class="choice-row">
                  <span class="choice-num">{{ q.questionNo }}</span>
                  <span class="choice-bubble" v-for="opt in choiceOptions(q)" :key="opt">{{ opt }}</span>
                </div>
              </div>
            </div>
            <div v-else class="choice-table">
              <div v-for="(col, cIdx) in choiceColumns(section)" :key="cIdx" class="choice-column">
                <div v-for="item in col" :key="item.index" class="choice-row">
                  <span class="choice-num">{{ item.index }}</span>
                  <span class="choice-bubble" v-for="opt in ['A','B','C','D']" :key="opt">{{ opt }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 填空题 -->
          <div v-else-if="section.type === 'fill'" class="fill-area">
            <div v-for="i in Math.min(section.count, 10)" :key="i" class="fill-row">
              <span class="fill-num">{{ i }}.</span>
              <span class="fill-blank"></span>
            </div>
          </div>

          <!-- 解答题 -->
          <div v-else-if="section.type === 'subjective'" class="subjective-area">
            <div
              v-if="section.content || !readonly"
              class="subjective-content"
              :class="{ editable: !readonly }"
              :contenteditable="!readonly"
              v-html="section.content"
              @blur="updateSectionContent($event, section)"
            ></div>
            <div v-if="section.subQuestions && section.subQuestions.length">
              <div v-for="(q, qIdx) in section.subQuestions" :key="qIdx" class="sub-question-block">
                <div class="sub-question-title">{{ q.questionNo }}（{{ q.score }}分）</div>
                <div v-if="q.hasAnswerLine" class="answer-lines" :style="subQuestionLineStyle(q)">
                  <div v-for="i in (q.lineCount || 8)" :key="i" class="answer-row"></div>
                </div>
                <div v-else class="no-line-hint">（本题不配置答题线）</div>
              </div>
            </div>
            <div v-else class="answer-lines" :style="subjectiveStyle(section)">
              <div v-for="i in (section.rows || 8)" :key="i" class="answer-row"></div>
            </div>
          </div>

          <!-- 作文 -->
          <div v-else-if="section.type === 'composition_cn' || section.type === 'composition_en'" class="composition-area">
            <div class="composition-grid">
              <div v-for="i in 400" :key="i" class="comp-cell"></div>
            </div>
          </div>

          <!-- 非作答区 -->
          <div v-else class="blank-section">
            <span class="blank-hint">请勿在此区域作答</span>
          </div>
        </div>
      </div>

      <!-- 页脚 -->
      <div class="paper-footer">
        <span class="footer-label">请在各题目的答题区域内作答，超出黑色矩形边框限定区域的答案无效</span>
        <span class="page-no-label">第 {{ pageIdx + 1 }} 页</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  config: { type: Object, required: true },
  readonly: { type: Boolean, default: false }
})
const emit = defineEmits(['update:config', 'edit-student-info'])

const paperRef = ref(null)

const layoutClass = computed(() => `layout-${props.config.layout || 'one'}`)
const colorClass = computed(() => `color-${props.config.color || 'black'}`)
const digits = computed(() => props.config.digits || 8)
const showBubbleGrid = computed(() => (props.config.studentNumberTypes || []).includes('bubble'))
const showBarcode = computed(() => (props.config.studentNumberTypes || []).includes('barcode'))
const studentInfo = computed(() => {
  const info = props.config.studentInfo || {}
  if (Array.isArray(info.fields) && info.fields.length > 0) {
    return { fields: info.fields }
  }
  return {
    fields: [
      { id: 'name', label: info.nameLabel || '姓名', placeholder: '________' },
      { id: 'class', label: info.classLabel || '班级', placeholder: '________' }
    ]
  }
})

const sectionsStyle = computed(() => {
  const map = { one: 1, two: 2, three: 3 }
  return { columnCount: map[props.config.layout] || 1 }
})

const topLeftStyle = computed(() => ({
  flex: 1
}))

const topRightStyle = computed(() => {
  const d = digits.value || 8
  return {
    width: `${d * 23 + 26}px`,
    flexShrink: 0
  }
})

const paperStyle = computed(() => {
  const pxPerMm = 3.7795
  const sizes = {
    one: { width: 210 * pxPerMm, height: 297 * pxPerMm }
  }
  const size = sizes.one
  return {
    width: `${Math.round(size.width)}px`,
    height: `${Math.round(size.height)}px`
  }
})

// 估算各题块高度（px），用于分页
const estimateSectionHeight = (section) => {
  const headerHeight = 43 // section-header + border
  const padding = 24 // 上下 padding
  switch (section.type) {
    case 'choice': {
      const total = section.subQuestions && section.subQuestions.length ? section.subQuestions.length : (section.count || 0)
      const columns = Math.ceil(total / 5)
      const columnsPerLine = 5
      const lines = Math.ceil(columns / columnsPerLine)
      return headerHeight + padding + lines * 160
    }
    case 'fill': {
      const count = Math.min(section.count || 0, 10)
      return headerHeight + padding + count * 34
    }
    case 'subjective': {
      if (section.subQuestions && section.subQuestions.length) {
        const totalRows = section.subQuestions.reduce((sum, q) => {
          return sum + (q.hasAnswerLine ? (q.lineCount || 8) : 1)
        }, 0)
        return headerHeight + padding + totalRows * 28 + section.subQuestions.length * 22
      }
      const rows = section.rows || 8
      return headerHeight + padding + rows * 28
    }
    case 'composition_cn':
    case 'composition_en':
      return headerHeight + padding + 420
    case 'blank':
      return 100
    default:
      return headerHeight + padding
  }
}

// 单页可用内容高度（A4 297mm 换算为 px 后减去页眉页脚）
const getPageContentHeight = () => {
  const pxPerMm = 3.7795
  const pageHeight = 297 * pxPerMm // ~1123px
  const firstPageReserved = 420 // 标题 + 考生信息区 + 页脚 + padding
  const subPageReserved = 220 // 简化页眉 + 页脚 + padding
  return { first: pageHeight - firstPageReserved, sub: pageHeight - subPageReserved }
}

const pages = computed(() => {
  const sections = props.config.sections || []
  // 多栏布局暂按单页处理，依赖 CSS 列排版
  if ((props.config.layout || 'one') !== 'one') {
    return [{ sections }]
  }

  const { first, sub } = getPageContentHeight()
  const result = []
  let currentPage = []
  let currentHeight = 0
  let isFirstPage = true

  for (const section of sections) {
    const h = estimateSectionHeight(section)
    const limit = isFirstPage ? first : sub

    // 当前页剩余空间不足以放下该 section 时，换页
    if (currentPage.length > 0 && currentHeight + h > limit) {
      result.push({ sections: currentPage })
      currentPage = []
      currentHeight = 0
      isFirstPage = false
    }

    currentPage.push(section)
    currentHeight += h
  }

  if (currentPage.length > 0) {
    result.push({ sections: currentPage })
  }

  return result.length > 0 ? result : [{ sections: [] }]
})

const choiceOptions = (q) => {
  const count = q.optionCount || 4
  if (q.subType === 'judge') return ['对', '错']
  const base = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
  return base.slice(0, count)
}

const sectionTypeLabel = (type) => {
  const map = {
    choice: '客观题',
    fill: '填空题',
    subjective: '解答题',
    composition_cn: '作文（语）',
    composition_en: '作文（英）',
    blank: '非作答区'
  }
  return map[type] || '未知'
}

const onTitleInput = (e) => {
  emit('update:config', { ...props.config, title: e.target.value })
}

const updateSectionContent = (e, section) => {
  const html = e.target.innerHTML
  const newSections = props.config.sections.map(s => {
    if (s === section) {
      return { ...s, content: html }
    }
    return s
  })
  emit('update:config', { ...props.config, sections: newSections })
}

const choiceColumns = (section) => {
  const perColumn = 5
  if (section.subQuestions && section.subQuestions.length) {
    const cols = []
    for (let i = 0; i < section.subQuestions.length; i += perColumn) {
      cols.push(section.subQuestions.slice(i, i + perColumn))
    }
    return cols
  }
  const total = section.count || 0
  const cols = []
  for (let i = 0; i < total; i += perColumn) {
    const col = []
    for (let j = i; j < Math.min(i + perColumn, total); j++) {
      col.push({ index: j + 1 })
    }
    cols.push(col)
  }
  return cols
}

const subjectiveStyle = (section) => {
  const rows = section.rows || 8
  return {
    minHeight: `${rows * 28 + 24}px`
  }
}

const subQuestionLineStyle = (q) => {
  const rows = q.lineCount || 8
  return {
    minHeight: `${rows * 28 + 12}px`
  }
}

defineExpose({ paperRef })
</script>

<style scoped>
.paper-pages {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.paper {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 56.7px 45.4px 37.8px;
  position: relative;
  box-sizing: border-box;
  color: #000;
  line-height: 1.5;
  font-size: 14px;
  display: flex;
  flex-direction: column;
}
.paper.color-red {
  color: #c03639;
}

/* 标题 */
.paper-title {
  text-align: center;
  padding: 0 0 16px;
}
.title-input,
.title-text {
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

/* 上部分区 */
.top-section {
  display: flex;
  border: 1px solid #000;
  margin: 0;
  min-height: 226.8px;
}
.top-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #000;
}
.student-basic {
  padding: 12px 14px;
  border-bottom: 1px solid #000;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  white-space: nowrap;
}
.notes-box {
  flex: 1;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
}
.notes-title {
  font-weight: bold;
  margin-bottom: 6px;
  font-size: 13px;
}
.notes-box p {
  margin: 0 0 4px;
  font-size: 12px;
}
.notes-marks {
  display: flex;
  gap: 16px;
  margin-top: auto;
  padding-top: 10px;
}
.mark-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.mark-box {
  width: 16px;
  height: 16px;
  border: 1px solid #000;
}
.mark-box.filled {
  background: #000;
}

/* 右侧准考证号 */
.top-right {
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.exam-no-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 4px;
}
.exam-no-label {
  font-size: 12px;
  font-weight: bold;
}
.exam-no-wrap {
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px;
  border: 1px solid #000;
}
.exam-no-inputs {
  display: flex;
  gap: 3px;
}
.no-input-box {
  width: 20px;
  height: 20px;
  border: 1px solid #000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.digit-input {
  width: 100%;
  height: 100%;
  border: none;
  text-align: center;
  outline: none;
  font-size: 11px;
  background: transparent;
}
.bubble-grid {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.bubble-row {
  display: flex;
  gap: 3px;
}
.bubble-cell {
  width: 20px;
  height: 18px;
  border: 1px solid #000;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  line-height: 1;
  background: #fff;
}
.exam-no-inputs-only {
  display: flex;
  gap: 3px;
  padding: 4px;
  border: 1px solid #000;
}

/* 后续页简化页眉 */
.sub-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #000;
  margin: 0;
  margin-top: 0;
}
.sub-page-title {
  font-size: 18px;
  font-weight: bold;
}
.sub-page-no {
  font-size: 13px;
  color: #666;
}

/* 试卷结构区 */
.sections-container {
  flex: 1;
  padding: 20px 0;
  overflow: hidden;
  column-gap: 20px;
}
.section-block {
  break-inside: avoid;
  margin-bottom: 20px;
  border: 1px solid #000;
}
.section-header {
  background: #f5f5f5;
  padding: 8px 12px;
  border-bottom: 1px solid #000;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.section-title {
  font-size: 14px;
  font-weight: bold;
}
.section-score {
  font-size: 12px;
  color: #666;
}

/* 客观题 */
.choice-area {
  padding: 12px;
}
.choice-table {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 16px;
  align-content: flex-start;
}
.choice-column {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.choice-row {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
}
.choice-num {
  width: 22px;
  text-align: right;
  font-weight: bold;
}
.choice-bubble {
  width: 18px;
  height: 18px;
  border: 1px solid #000;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

/* 填空题 */
.fill-area {
  padding: 12px;
}
.fill-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}
.fill-num {
  font-size: 13px;
  font-weight: bold;
  width: 22px;
  text-align: right;
}
.fill-blank {
  flex: 1;
  border-bottom: 1px solid #000;
  height: 22px;
}

/* 解答题 */
.subjective-area {
  padding: 12px;
  min-height: 120px;
}
.subjective-content {
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.6;
}
.subjective-content.editable {
  border: 1px dashed transparent;
  padding: 4px;
  min-height: 28px;
}
.subjective-content.editable:hover {
  border-color: #c0c4cc;
  background: #fafafa;
}
.subjective-content.editable:focus {
  outline: none;
  border-color: #409eff;
  background: #fff;
}
.answer-row {
  border-bottom: 1px solid #e0e0e0;
  height: 28px;
}
.sub-question-block {
  margin-bottom: 12px;
}
.sub-question-block:last-child {
  margin-bottom: 0;
}
.sub-question-title {
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 6px;
}
.no-line-hint {
  font-size: 12px;
  color: #999;
  padding: 8px 0;
}

/* 作文 */
.composition-area {
  padding: 12px;
}
.composition-grid {
  display: grid;
  grid-template-columns: repeat(20, 1fr);
  border: 1px solid #000;
}
.comp-cell {
  border: 1px solid #f0f0f0;
  aspect-ratio: 1;
}

/* 非作答区 */
.blank-section {
  padding: 32px 12px;
  text-align: center;
}
.blank-hint {
  font-size: 14px;
  color: #999;
}

/* 页脚 */
.paper-footer {
  margin-top: auto;
  padding: 12px 0;
  border-top: 1px dashed #ccc;
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 16px;
}
.footer-label {
  font-size: 11px;
  color: #999;
}
.page-no-label {
  font-size: 11px;
  color: #999;
}

/* 布局 */
.layout-one .sections-container {
  column-count: 1;
}
.layout-two .sections-container {
  column-count: 2;
}
.layout-three .sections-container {
  column-count: 3;
}
.layout-two .first-page-header {
  width: calc((100% - 20px) / 2);
}
.layout-three .first-page-header {
  width: calc((100% - 40px) / 3);
}
</style>
