<template>
  <div class="region-canvas-wrapper">
    <div class="canvas-toolbar">
      <span class="toolbar-hint" v-if="!drawing && !moving">
        <el-icon><InfoFilled /></el-icon>
        拖拽鼠标框选区域 ｜ 点击已有区域选中后拖拽移动 ｜ 拖拽右下角调整大小 ｜ 右键删除
      </span>
      <span class="toolbar-hint" v-else-if="drawing">
        <el-icon><EditPen /></el-icon>
        正在框选，松开鼠标完成
      </span>
      <span class="toolbar-hint" v-else>
        <el-icon><Rank /></el-icon>
        正在移动区域
      </span>
      <el-button-group>
        <el-button size="small" :type="page === 1 ? 'primary' : ''" @click="page = 1">第 1 页</el-button>
        <el-button size="small" :type="page === 2 ? 'primary' : ''" @click="page = 2">第 2 页</el-button>
        <el-button size="small" :type="page === 3 ? 'primary' : ''" @click="page = 3">第 3 页</el-button>
      </el-button-group>
    </div>
    <div class="canvas-container" ref="containerRef">
      <canvas
        ref="canvasRef"
        :width="canvasWidth"
        :height="canvasHeight"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
        @contextmenu.prevent="onContextMenu"
        :style="{ cursor: cursorStyle }"
      />
      <div class="page-indicator" v-if="page > 1">
        <span>第 {{ page }} 页</span>
      </div>
    </div>
    <div class="region-list">
      <div
        v-for="region in pageRegions"
        :key="region.questionNo"
        class="region-list-item"
        :class="{ selected: selectedNo === region.questionNo }"
        @click="selectRegion(region.questionNo)"
      >
        <span class="region-color" :style="{ background: getColor(region.questionNo) }"></span>
        <span>第 {{ region.questionNo }} 题</span>
        <span class="region-coords">
          ({{ region.x }}, {{ region.y }}) {{ region.w }}×{{ region.h }}
        </span>
        <el-button type="danger" link size="small" @click.stop="deleteRegion(region.questionNo)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      <div v-if="pageRegions.length === 0" class="empty-hint">当前页暂无切割区域，请在画布上框选</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  questions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const canvasRef = ref(null)
const containerRef = ref(null)
const page = ref(1)

const canvasWidth = ref(600)
const canvasHeight = ref(840)

const selectedNo = ref(null)
const drawing = ref(false)
const moving = ref(false)
const resizing = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const drawCurrent = ref({ x: 0, y: 0 })
const moveOffset = ref({ x: 0, y: 0 })
const resizeCorner = ref('')

const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#00BCD4', '#FF9800', '#9C27B0', '#795548', '#607D8B']

const getColor = (questionNo) => {
  const idx = String(questionNo).charCodeAt(0) % colors.length
  return colors[idx]
}

const pageRegions = computed(() => {
  return props.modelValue.filter(r => r.page === page.value)
})

const cursorStyle = computed(() => {
  if (drawing.value) return 'crosshair'
  if (moving.value) return 'move'
  if (resizing.value) return 'nwse-resize'
  return 'crosshair'
})

const getCanvasPos = (e) => {
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasWidth.value / rect.width
  const scaleY = canvasHeight.value / rect.height
  return {
    x: Math.round((e.clientX - rect.left) * scaleX),
    y: Math.round((e.clientY - rect.top) * scaleY)
  }
}

const hitTest = (pos) => {
  const regions = [...pageRegions.value].reverse()
  for (const region of regions) {
    const rx = region.x, ry = region.y, rw = region.w, rh = region.h
    // 检查右下角 resize handle
    const handleSize = 10
    if (pos.x >= rx + rw - handleSize && pos.x <= rx + rw + handleSize &&
        pos.y >= ry + rh - handleSize && pos.y <= ry + rh + handleSize) {
      return { region, action: 'resize' }
    }
    // 检查是否在区域内
    if (pos.x >= rx && pos.x <= rx + rw && pos.y >= ry && pos.y <= ry + rh) {
      return { region, action: 'move' }
    }
  }
  return null
}

const onMouseDown = (e) => {
  if (e.button === 2) return
  const pos = getCanvasPos(e)
  const hit = hitTest(pos)

  if (hit) {
    selectRegion(hit.region.questionNo)
    if (hit.action === 'resize') {
      resizing.value = true
      resizeCorner.value = hit.region.questionNo
      moveOffset.value = { x: pos.x, y: pos.y }
    } else {
      moving.value = true
      moveOffset.value = { x: pos.x, y: pos.y }
    }
  } else {
    selectedNo.value = null
    drawing.value = true
    drawStart.value = pos
    drawCurrent.value = pos
  }
  draw()
}

const onMouseMove = (e) => {
  const pos = getCanvasPos(e)

  if (drawing.value) {
    drawCurrent.value = pos
    draw()
    return
  }

  if (moving.value && selectedNo.value) {
    const dx = pos.x - moveOffset.value.x
    const dy = pos.y - moveOffset.value.y
    moveOffset.value = pos

    const regions = [...props.modelValue]
    const region = regions.find(r => r.questionNo === selectedNo.value && r.page === page.value)
    if (region) {
      region.x = Math.max(0, Math.min(canvasWidth.value - region.w, region.x + dx))
      region.y = Math.max(0, Math.min(canvasHeight.value - region.h, region.y + dy))
      emit('update:modelValue', regions)
    }
    draw()
    return
  }

  if (resizing.value && resizeCorner.value) {
    const regions = [...props.modelValue]
    const region = regions.find(r => r.questionNo === resizeCorner.value && r.page === page.value)
    if (region) {
      const newW = Math.max(30, pos.x - region.x)
      const newH = Math.max(30, pos.y - region.y)
      region.w = Math.min(canvasWidth.value - region.x, newW)
      region.h = Math.min(canvasHeight.value - region.y, newH)
      emit('update:modelValue', regions)
    }
    draw()
    return
  }

  // 更新鼠标样式
  if (!drawing.value && !moving.value && !resizing.value) {
    const hit = hitTest(pos)
    canvasRef.value.style.cursor = hit?.action === 'resize' ? 'nwse-resize' : hit ? 'move' : 'crosshair'
  }
}

const onMouseUp = () => {
  if (drawing.value) {
    const x1 = Math.min(drawStart.value.x, drawCurrent.value.x)
    const y1 = Math.min(drawStart.value.y, drawCurrent.value.y)
    const x2 = Math.max(drawStart.value.x, drawCurrent.value.x)
    const y2 = Math.max(drawStart.value.y, drawCurrent.value.y)
    const w = x2 - x1
    const h = y2 - y1

    if (w > 10 && h > 10) {
      // 找到当前还未分配区域的主观题
      const assignedNos = new Set(props.modelValue.map(r => r.questionNo))
      const unassigned = props.questions.filter(q => !assignedNos.has(q))
      const targetQuestion = unassigned.length > 0 ? unassigned[0] : `Q${props.modelValue.length + 1}`

      const regions = [...props.modelValue, {
        questionNo: targetQuestion,
        page: page.value,
        x: Math.round(x1),
        y: Math.round(y1),
        w: Math.round(w),
        h: Math.round(h)
      }]
      emit('update:modelValue', regions)
      selectRegion(targetQuestion)
    }
    drawing.value = false
  }
  moving.value = false
  resizing.value = false
  resizeCorner.value = ''
  draw()
}

const onContextMenu = (e) => {
  const pos = getCanvasPos(e)
  const hit = hitTest(pos)
  if (hit) {
    deleteRegion(hit.region.questionNo)
  }
}

const selectRegion = (questionNo) => {
  selectedNo.value = questionNo
  draw()
}

const deleteRegion = (questionNo) => {
  const regions = props.modelValue.filter(r => !(r.questionNo === questionNo && r.page === page.value))
  if (selectedNo.value === questionNo) selectedNo.value = null
  emit('update:modelValue', regions)
  draw()
}

const draw = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = canvasWidth.value
  const h = canvasHeight.value

  ctx.clearRect(0, 0, w, h)

  // 背景 - 模拟答题卡
  ctx.fillStyle = '#fafafa'
  ctx.fillRect(0, 0, w, h)

  // 纸张边框
  ctx.strokeStyle = '#dcdfe6'
  ctx.lineWidth = 2
  ctx.strokeRect(5, 5, w - 10, h - 10)

  // 网格
  ctx.strokeStyle = '#f0f0f0'
  ctx.lineWidth = 0.5
  const gridSize = 30
  for (let x = gridSize; x < w; x += gridSize) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, h)
    ctx.stroke()
  }
  for (let y = gridSize; y < h; y += gridSize) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  // 页码标记
  ctx.fillStyle = '#c0c4cc'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`第 ${page.value} 页`, w / 2, h - 10)

  // 绘制已有区域
  for (const region of pageRegions.value) {
    const isSelected = selectedNo.value === region.questionNo
    const color = getColor(region.questionNo)

    // 填充
    ctx.fillStyle = isSelected ? `${color}30` : `${color}15`
    ctx.fillRect(region.x, region.y, region.w, region.h)

    // 边框
    ctx.strokeStyle = isSelected ? color : `${color}80`
    ctx.lineWidth = isSelected ? 2.5 : 1.5
    ctx.setLineDash(isSelected ? [] : [6, 3])
    ctx.strokeRect(region.x, region.y, region.w, region.h)
    ctx.setLineDash([])

    // 标签
    const label = `第${region.questionNo}题`
    ctx.font = `bold ${isSelected ? 14 : 12}px sans-serif`
    const textWidth = ctx.measureText(label).width
    const labelX = region.x + 4
    const labelY = region.y + 18

    // 标签背景
    ctx.fillStyle = color
    ctx.fillRect(labelX - 2, labelY - 14, textWidth + 8, 20)
    ctx.fillStyle = '#fff'
    ctx.fillText(label, labelX + 2, labelY)

    // 选中时显示 resize 手柄
    if (isSelected) {
      ctx.fillStyle = color
      ctx.fillRect(region.x + region.w - 8, region.y + region.h - 8, 10, 10)
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1
      ctx.strokeRect(region.x + region.w - 8, region.y + region.h - 8, 10, 10)
    }
  }

  // 绘制正在拖动的新区域
  if (drawing.value) {
    const x = Math.min(drawStart.value.x, drawCurrent.value.x)
    const y = Math.min(drawStart.value.y, drawCurrent.value.y)
    const rw = Math.abs(drawCurrent.value.x - drawStart.value.x)
    const rh = Math.abs(drawCurrent.value.y - drawStart.value.y)

    ctx.fillStyle = 'rgba(64, 158, 255, 0.2)'
    ctx.fillRect(x, y, rw, rh)
    ctx.strokeStyle = '#409EFF'
    ctx.lineWidth = 2
    ctx.setLineDash([4, 2])
    ctx.strokeRect(x, y, rw, rh)
    ctx.setLineDash([])

    // 显示尺寸
    ctx.fillStyle = '#409EFF'
    ctx.font = '11px sans-serif'
    ctx.fillText(`${Math.round(rw)} × ${Math.round(rh)}`, x + 4, y - 4)
  }
}

onMounted(() => {
  draw()
})

watch(page, () => {
  selectedNo.value = null
  nextTick(draw)
})

watch(() => props.modelValue, () => {
  nextTick(draw)
}, { deep: true })
</script>

<style scoped>
.region-canvas-wrapper {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  background: #fff;
}

.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-hint {
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.canvas-container {
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  background: #fff;
  overflow: hidden;
  max-width: 100%;
}

.canvas-container canvas {
  display: block;
  width: 100%;
  height: auto;
}

.page-indicator {
  position: absolute;
  bottom: 8px;
  right: 12px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.region-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.region-list-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: border-color 0.2s, background 0.2s;
}

.region-list-item:hover {
  border-color: #409EFF;
}

.region-list-item.selected {
  border-color: #409EFF;
  background: #ecf5ff;
}

.region-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.region-coords {
  color: #909399;
  font-size: 12px;
}

.empty-hint {
  color: #c0c4cc;
  font-size: 13px;
  padding: 4px 0;
}
</style>