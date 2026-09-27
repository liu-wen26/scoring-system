<template>
  <div class="answer-card-canvas">
    <div class="pages-container" ref="pagesContainer">
      <div
        v-for="(page, pageIdx) in pages"
        :key="pageIdx"
        class="page-wrapper"
        :style="{ width: displayWidth + 'px', height: displayHeight + 'px' }"
      >
        <canvas
          :ref="el => setCanvasRef(el, pageIdx)"
          :width="canvasWidth"
          :height="canvasHeight"
          class="page-canvas"
          @mousedown="onMouseDown($event, pageIdx)"
          @mousemove="onMouseMove($event, pageIdx)"
          @mouseup="onMouseUp($event, pageIdx)"
          @mouseleave="onMouseUp($event, pageIdx)"
          @contextmenu.prevent="onContextMenu($event, pageIdx)"
        />
        <div class="page-label">第 {{ pageIdx + 1 }} 页</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUpdated, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  templateImage: {
    type: String,
    default: ''
  },
  pagePreviews: {
    type: Array,
    default: () => []
  },
  pageCount: {
    type: Number,
    default: 1
  },
  activeTool: {
    type: String,
    default: 'select'
  },
  zoom: {
    type: Number,
    default: 100
  },
  studentFields: {
    type: Array,
    default: () => ['school', 'class', 'name', 'examNo', 'seatNo']
  },
  objectiveQuestions: {
    type: Array,
    default: () => []
  },
  subjectiveQuestions: {
    type: Array,
    default: () => []
  },
  nextRegionLabel: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'region-selected', 'image-loaded', 'region-created'])

const pagesContainer = ref(null)
const canvasRefs = ref([])

const DISPLAY_WIDTH = 560
const displayWidth = computed(() => DISPLAY_WIDTH * (props.zoom / 100))
const displayHeight = ref(790)

const canvasWidth = ref(DISPLAY_WIDTH)
const canvasHeight = ref(790)
const templateImgs = ref([])
const imgNaturalWidth = ref(0)
const imgNaturalHeight = ref(0)
const scaleRatio = ref(1)

const selectedKey = ref(null)
const drawing = ref(false)
const moving = ref(false)
const resizing = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const drawCurrent = ref({ x: 0, y: 0 })
const moveOffset = ref({ x: 0, y: 0 })
const drawType = ref('')
const drawPageIdx = ref(0)

const pages = computed(() => Array(props.pageCount).fill(null))

const setCanvasRef = (el, idx) => {
  if (el) canvasRefs.value[idx] = el
}

const getColor = (type) => {
  if (type === 'student') return '#67C23A'
  if (type === 'objective') return '#F56C6C'
  if (type === 'subjective') return '#409EFF'
  return '#909399'
}

const getRegionType = (tool) => {
  if (tool === 'student') return 'student'
  if (tool === 'objective') return 'objective'
  if (tool === 'subjective') return 'subjective'
  return null
}

const loadTemplateImages = () => {
  const previews = props.pagePreviews && props.pagePreviews.length > 0
    ? props.pagePreviews
    : (props.templateImage ? [props.templateImage] : [])

  if (previews.length === 0) {
    templateImgs.value = []
    imgNaturalWidth.value = 0
    imgNaturalHeight.value = 0
    scaleRatio.value = 1
    canvasWidth.value = DISPLAY_WIDTH
    canvasHeight.value = 790
    displayHeight.value = 790 * (props.zoom / 100)
    nextTick(redrawAll)
    return
  }

  const loadedImgs = []
  let loadedCount = 0

  previews.forEach((src, idx) => {
    const img = new Image()
    img.onload = () => {
      loadedImgs[idx] = img
      loadedCount++
      if (idx === 0) {
        imgNaturalWidth.value = img.width
        imgNaturalHeight.value = img.height
        const ratio = DISPLAY_WIDTH / img.width
        scaleRatio.value = ratio
        canvasWidth.value = DISPLAY_WIDTH
        canvasHeight.value = Math.round(img.height * ratio)
        displayHeight.value = canvasHeight.value * (props.zoom / 100)
      }
      if (loadedCount === previews.length) {
        templateImgs.value = loadedImgs
        nextTick(() => {
          redrawAll()
          emit('image-loaded', {
            width: imgNaturalWidth.value,
            height: imgNaturalHeight.value,
            displayWidth: canvasWidth.value,
            displayHeight: canvasHeight.value
          })
        })
      }
    }
    img.onerror = () => {
      loadedImgs[idx] = null
      loadedCount++
      if (loadedCount === previews.length) {
        templateImgs.value = loadedImgs
        nextTick(redrawAll)
      }
    }
    img.src = src
  })
}

watch(() => [props.templateImage, props.pagePreviews.join(',')], loadTemplateImages)

watch(() => props.zoom, () => {
  displayHeight.value = canvasHeight.value * (props.zoom / 100)
})

const getCanvasPos = (e, pageIdx) => {
  const canvas = canvasRefs.value[pageIdx]
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasWidth.value / rect.width
  const scaleY = canvasHeight.value / rect.height
  return {
    x: Math.round((e.clientX - rect.left) * scaleX),
    y: Math.round((e.clientY - rect.top) * scaleY)
  }
}

const hitTest = (pos, pageIdx) => {
  const regions = props.modelValue.filter(r => r.page === pageIdx + 1)
  for (let i = regions.length - 1; i >= 0; i--) {
    const region = regions[i]
    const rx = region.x * scaleRatio.value
    const ry = region.y * scaleRatio.value
    const rw = region.w * scaleRatio.value
    const rh = region.h * scaleRatio.value
    const handleSize = 10
    if (pos.x >= rx + rw - handleSize && pos.x <= rx + rw + handleSize &&
        pos.y >= ry + rh - handleSize && pos.y <= ry + rh + handleSize) {
      return { region, action: 'resize' }
    }
    if (pos.x >= rx && pos.x <= rx + rw && pos.y >= ry && pos.y <= ry + rh) {
      return { region, action: 'move' }
    }
  }
  return null
}

const getNextLabel = (type, pageIdx) => {
  const pageRegions = props.modelValue.filter(r => r.page === pageIdx + 1 && r.type === type)
  if (type === 'student') {
    const used = new Set(pageRegions.map(r => r.field))
    for (const f of props.studentFields) {
      const fieldKey = typeof f === 'object' ? f.key : f
      if (!used.has(fieldKey)) return fieldKey
    }
    return `student_${pageRegions.length + 1}`
  }
  if (type === 'objective') {
    const used = new Set(pageRegions.map(r => String(r.questionNo)))
    const allQ = props.objectiveQuestions
    for (const q of allQ) {
      if (!used.has(String(q.no))) return String(q.no)
    }
    return `Q${pageRegions.length + 1}`
  }
  if (type === 'subjective') {
    const used = new Set(pageRegions.map(r => String(r.questionNo)))
    const allQ = props.subjectiveQuestions
    for (const q of allQ) {
      if (!used.has(String(q.no))) return String(q.no)
    }
    return `S${pageRegions.length + 1}`
  }
  return `R${pageRegions.length + 1}`
}

const onMouseDown = (e, pageIdx) => {
  if (e.button === 2) return
  const pos = getCanvasPos(e, pageIdx)
  const hit = hitTest(pos, pageIdx)
  const type = getRegionType(props.activeTool)

  if (hit && props.activeTool === 'select') {
    selectedKey.value = hit.region.key
    emit('region-selected', hit.region)
    if (hit.action === 'resize') {
      resizing.value = true
      moveOffset.value = pos
    } else {
      moving.value = true
      moveOffset.value = pos
    }
    redrawAll()
    return
  }

  if (type) {
    selectedKey.value = null
    drawing.value = true
    drawStart.value = pos
    drawCurrent.value = pos
    drawType.value = type
    drawPageIdx.value = pageIdx
    redrawAll()
    return
  }

  selectedKey.value = null
  emit('region-selected', null)
  redrawAll()
}

const onMouseMove = (e, pageIdx) => {
  const pos = getCanvasPos(e, pageIdx)

  if (drawing.value && drawPageIdx.value === pageIdx) {
    drawCurrent.value = pos
    redrawAll()
    return
  }

  if (moving.value && selectedKey.value) {
    const regions = [...props.modelValue]
    const region = regions.find(r => r.key === selectedKey.value)
    if (region) {
      const dx = (pos.x - moveOffset.value.x) / scaleRatio.value
      const dy = (pos.y - moveOffset.value.y) / scaleRatio.value
      moveOffset.value = pos
      region.x = Math.max(0, Math.min(imgNaturalWidth.value - region.w, region.x + dx))
      region.y = Math.max(0, Math.min(imgNaturalHeight.value - region.h, region.y + dy))
      emit('update:modelValue', regions)
    }
    redrawAll()
    return
  }

  if (resizing.value && selectedKey.value) {
    const regions = [...props.modelValue]
    const region = regions.find(r => r.key === selectedKey.value)
    if (region) {
      const newW = Math.max(20, (pos.x / scaleRatio.value - region.x))
      const newH = Math.max(20, (pos.y / scaleRatio.value - region.y))
      region.w = Math.min(imgNaturalWidth.value - region.x, newW)
      region.h = Math.min(imgNaturalHeight.value - region.y, newH)
      emit('update:modelValue', regions)
    }
    redrawAll()
    return
  }

  const canvas = canvasRefs.value[pageIdx]
  if (canvas && props.activeTool === 'select') {
    const hit = hitTest(pos, pageIdx)
    canvas.style.cursor = hit?.action === 'resize' ? 'nwse-resize' : hit ? 'move' : 'default'
  } else if (canvas) {
    canvas.style.cursor = 'crosshair'
  }
}

const onMouseUp = (e, pageIdx) => {
  if (drawing.value && drawPageIdx.value === pageIdx) {
    const x1 = Math.min(drawStart.value.x, drawCurrent.value.x)
    const y1 = Math.min(drawStart.value.y, drawCurrent.value.y)
    const x2 = Math.max(drawStart.value.x, drawCurrent.value.x)
    const y2 = Math.max(drawStart.value.y, drawCurrent.value.y)
    const w = x2 - x1
    const h = y2 - y1

    if (w > 10 && h > 10) {
      let label = getNextLabel(drawType.value, pageIdx)
      let fieldValue = drawType.value === 'student' ? label : null
      let questionNoValue = label

      if (props.nextRegionLabel && props.nextRegionLabel.type === drawType.value) {
        if (drawType.value === 'student') {
          fieldValue = props.nextRegionLabel.field || label
          questionNoValue = fieldValue
        } else {
          questionNoValue = props.nextRegionLabel.questionNo || label
        }
      }

      const key = `${drawType.value}_${pageIdx}_${Date.now()}`
      const newRegion = {
        key,
        type: drawType.value,
        page: pageIdx + 1,
        questionNo: questionNoValue,
        field: fieldValue,
        x: Math.round(x1 / scaleRatio.value),
        y: Math.round(y1 / scaleRatio.value),
        w: Math.round(w / scaleRatio.value),
        h: Math.round(h / scaleRatio.value)
      }
      const regions = [...props.modelValue, newRegion]
      emit('update:modelValue', regions)
      selectedKey.value = key
      emit('region-selected', newRegion)
      emit('region-created', newRegion)
    }
    drawing.value = false
  }
  moving.value = false
  resizing.value = false
  redrawAll()
}

const onContextMenu = (e, pageIdx) => {
  const pos = getCanvasPos(e, pageIdx)
  const hit = hitTest(pos, pageIdx)
  if (hit) {
    const regions = props.modelValue.filter(r => r.key !== hit.region.key)
    if (selectedKey.value === hit.region.key) selectedKey.value = null
    emit('update:modelValue', regions)
    emit('region-selected', null)
    redrawAll()
  }
}

const redrawAll = () => {
  for (let i = 0; i < props.pageCount; i++) {
    drawPage(i)
  }
}

const drawPage = (pageIdx) => {
  const canvas = canvasRefs.value[pageIdx]
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = canvasWidth.value
  const h = canvasHeight.value

  ctx.clearRect(0, 0, w, h)

  const pageImg = templateImgs.value[pageIdx]
  if (pageImg) {
    ctx.drawImage(pageImg, 0, 0, w, h)
  } else {
    ctx.fillStyle = '#f5f7fa'
    ctx.fillRect(0, 0, w, h)
    ctx.fillStyle = '#c0c4cc'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('请上传答题卡模板图片', w / 2, h / 2)
  }

  ctx.strokeStyle = '#dcdfe6'
  ctx.lineWidth = 1
  ctx.strokeRect(0.5, 0.5, w - 1, h - 1)

  const cornerSize = 10
  ctx.fillStyle = '#303133'
  ctx.fillRect(0, 0, cornerSize, 3)
  ctx.fillRect(0, 0, 3, cornerSize)
  ctx.fillRect(w - cornerSize, 0, cornerSize, 3)
  ctx.fillRect(w - 3, 0, 3, cornerSize)
  ctx.fillRect(0, h - cornerSize, cornerSize, 3)
  ctx.fillRect(0, h - 3, 3, cornerSize)
  ctx.fillRect(w - cornerSize, h - 3, cornerSize, 3)
  ctx.fillRect(w - 3, h - cornerSize, 3, cornerSize)

  const pageRegions = props.modelValue.filter(r => r.page === pageIdx + 1)
  for (const region of pageRegions) {
    const isSelected = selectedKey.value === region.key
    const color = getColor(region.type)
    const rx = region.x * scaleRatio.value
    const ry = region.y * scaleRatio.value
    const rw = region.w * scaleRatio.value
    const rh = region.h * scaleRatio.value

    ctx.fillStyle = `${color}20`
    ctx.fillRect(rx, ry, rw, rh)

    ctx.strokeStyle = color
    ctx.lineWidth = isSelected ? 2.5 : 2
    ctx.setLineDash(isSelected ? [] : [5, 3])
    ctx.strokeRect(rx, ry, rw, rh)
    ctx.setLineDash([])

    let label = ''
    if (region.type === 'student') {
      const fieldLabels = { school: '学校', class: '班级', name: '姓名', examNo: '考号', seatNo: '座位号' }
      label = fieldLabels[region.field] || region.field
    } else {
      label = `第${region.questionNo}题`
    }

    ctx.font = `bold ${isSelected ? 13 : 12}px sans-serif`
    const tw = ctx.measureText(label).width
    ctx.fillStyle = color
    ctx.fillRect(rx + 2, ry + 2, tw + 10, 20)
    ctx.fillStyle = '#fff'
    ctx.textAlign = 'left'
    ctx.fillText(label, rx + 7, ry + 17)

    if (isSelected) {
      ctx.fillStyle = color
      ctx.fillRect(rx + rw - 7, ry + rh - 7, 10, 10)
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1.5
      ctx.strokeRect(rx + rw - 7, ry + rh - 7, 10, 10)
    }
  }

  if (drawing.value && drawPageIdx.value === pageIdx) {
    const x = Math.min(drawStart.value.x, drawCurrent.value.x)
    const y = Math.min(drawStart.value.y, drawCurrent.value.y)
    const rw = Math.abs(drawCurrent.value.x - drawStart.value.x)
    const rh = Math.abs(drawCurrent.value.y - drawStart.value.y)
    const color = getColor(drawType.value)

    ctx.fillStyle = `${color}30`
    ctx.fillRect(x, y, rw, rh)
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.setLineDash([5, 3])
    ctx.strokeRect(x, y, rw, rh)
    ctx.setLineDash([])

    const realW = Math.round(rw / scaleRatio.value)
    const realH = Math.round(rh / scaleRatio.value)
    ctx.fillStyle = color
    ctx.font = '11px sans-serif'
    ctx.fillText(`${realW} × ${realH}`, x + 4, y - 4)
  }
}

const deleteSelected = () => {
  if (!selectedKey.value) return
  const regions = props.modelValue.filter(r => r.key !== selectedKey.value)
  emit('update:modelValue', regions)
  selectedKey.value = null
  emit('region-selected', null)
  redrawAll()
}

const selectByKey = (key) => {
  selectedKey.value = key
  redrawAll()
}

defineExpose({ deleteSelected, selectByKey, redrawAll })

onMounted(() => {
  loadTemplateImages()
})

onUpdated(() => {
  nextTick(redrawAll)
})

watch(() => props.modelValue, () => {
  nextTick(redrawAll)
}, { deep: true })

watch(() => props.pageCount, () => {
  nextTick(redrawAll)
})
</script>

<style scoped>
.answer-card-canvas {
  width: 100%;
}

.pages-container {
  display: flex;
  gap: 24px;
  padding: 10px 20px 30px;
  align-items: flex-start;
}

.page-wrapper {
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  background: #fff;
}

.page-canvas {
  display: block;
  width: 100%;
  height: auto;
  cursor: crosshair;
}

.page-label {
  position: absolute;
  bottom: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
</style>