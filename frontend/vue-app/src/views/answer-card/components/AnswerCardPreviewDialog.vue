<template>
  <el-dialog v-model="visible" title="答题卡预览" width="900px" top="5vh" destroy-on-close>
    <div class="preview-dialog-body">
      <div class="preview-actions">
        <el-button type="primary" :loading="downloading" @click="handleDownload">
          <el-icon><Download /></el-icon> 下载 PNG
        </el-button>
      </div>
      <div class="preview-scroll">
        <AnswerCardPaper ref="paperRef" :config="previewConfig" readonly />
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import AnswerCardPaper from './AnswerCardPaper.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  config: { type: Object, default: () => ({}) },
  templateName: { type: String, default: '答题卡' }
})
const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const downloading = ref(false)
const paperRef = ref(null)

const defaultConfig = () => ({
  title: '',
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
  sections: []
})

const previewConfig = computed(() => ({
  ...defaultConfig(),
  ...props.config,
  layout: 'one'
}))

const handleDownload = async () => {
  if (!paperRef.value?.paperRef) {
    ElMessage.warning('纸张未渲染')
    return
  }
  downloading.value = true
  try {
    await nextTick()
    const canvas = await html2canvas(paperRef.value.paperRef, {
      scale: 2,
      backgroundColor: '#ffffff',
      useCORS: true
    })
    const link = document.createElement('a')
    link.download = `${props.templateName || '答题卡'}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    ElMessage.success('下载已开始')
  } catch (e) {
    console.error(e)
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.preview-dialog-body {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.preview-actions {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.preview-scroll {
  max-height: 70vh;
  overflow: auto;
  padding: 12px;
  background: #f0f2f5;
  border-radius: 4px;
}
</style>
