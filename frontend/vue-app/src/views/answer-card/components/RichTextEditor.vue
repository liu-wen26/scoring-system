<template>
  <div class="rich-editor">
    <div class="toolbar">
      <button type="button" class="tool-btn" @click="exec('bold')" title="加粗"><b>B</b></button>
      <button type="button" class="tool-btn" @click="exec('italic')" title="倾斜"><i>I</i></button>
      <button type="button" class="tool-btn" @click="exec('underline')" title="下划线"><u>U</u></button>
      <span class="tool-sep"></span>
      <button type="button" class="tool-btn" @click="exec('foreColor', '#f56c6c')" title="字体颜色"><span class="color-a" style="color:#f56c6c">A</span></button>
      <button type="button" class="tool-btn" @click="exec('hiliteColor', '#fef0f0')" title="背景颜色"><span class="color-a" style="background:#fef0f0">A</span></button>
      <span class="tool-sep"></span>
      <el-select v-model="fontSize" size="small" class="tool-select" @change="setFontSize">
        <el-option label="默认字号" value="" />
        <el-option label="12px" value="12px" />
        <el-option label="14px" value="14px" />
        <el-option label="16px" value="16px" />
        <el-option label="18px" value="18px" />
        <el-option label="20px" value="20px" />
      </el-select>
      <el-select v-model="fontName" size="small" class="tool-select" @change="setFontName">
        <el-option label="默认字体" value="" />
        <el-option label="宋体" value="SimSun" />
        <el-option label="黑体" value="SimHei" />
        <el-option label="微软雅黑" value="Microsoft YaHei" />
        <el-option label="楷体" value="KaiTi" />
      </el-select>
      <span class="tool-sep"></span>
      <button type="button" class="tool-btn" @click="exec('undo')" title="撤销">↶</button>
      <button type="button" class="tool-btn" @click="exec('redo')" title="重做">↷</button>
      <span class="tool-sep"></span>
      <button type="button" class="tool-btn" @click="insertImage" title="插入图片">🖼</button>
      <span class="tool-sep"></span>
      <button type="button" class="tool-btn" @click="exec('justifyLeft')" title="左对齐">≡</button>
      <button type="button" class="tool-btn" @click="exec('justifyCenter')" title="居中">≡</button>
      <button type="button" class="tool-btn" @click="exec('justifyRight')" title="右对齐">≡</button>
      <span class="tool-sep"></span>
      <el-select v-model="lineHeight" size="small" class="tool-select" @change="setLineHeight">
        <el-option label="默认行高" value="" />
        <el-option label="1" value="1" />
        <el-option label="1.5" value="1.5" />
        <el-option label="2" value="2" />
      </el-select>
    </div>
    <div
      ref="editorRef"
      class="editor-content"
      contenteditable="true"
      v-html="modelValue"
      @input="onInput"
      @blur="onBlur"
      @focus="onFocus"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'change'])

const editorRef = ref(null)
const fontSize = ref('')
const fontName = ref('')
const lineHeight = ref('')
const isFocused = ref(false)

const onInput = () => {
  const html = editorRef.value.innerHTML
  emit('update:modelValue', html)
  emit('change', html)
}

const onBlur = () => {
  isFocused.value = false
  const html = editorRef.value.innerHTML
  emit('update:modelValue', html)
  emit('change', html)
}

const onFocus = () => {
  isFocused.value = true
}

const exec = (command, value = null) => {
  document.execCommand(command, false, value)
  editorRef.value.focus()
  onInput()
}

const setFontSize = (val) => {
  if (val) exec('fontSize', '7')
  // execCommand fontSize uses 1-7; we set style after
  if (val && editorRef.value) {
    const selection = window.getSelection()
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0)
      const span = document.createElement('span')
      span.style.fontSize = val
      try {
        range.surroundContents(span)
      } catch (e) {
        // fallback: wrap selected nodes
      }
    }
  }
}

const setFontName = (val) => {
  if (val) exec('fontName', val)
}

const setLineHeight = (val) => {
  if (!val || !editorRef.value) return
  const selection = window.getSelection()
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0)
    const span = document.createElement('span')
    span.style.lineHeight = val
    try {
      range.surroundContents(span)
      onInput()
    } catch (e) {}
  }
}

const insertImage = () => {
  const url = window.prompt('请输入图片地址', 'https://')
  if (url) {
    exec('insertImage', url)
  }
}

watch(() => props.modelValue, (newVal) => {
  if (editorRef.value && editorRef.value.innerHTML !== newVal && !isFocused.value) {
    editorRef.value.innerHTML = newVal
  }
})
</script>

<style scoped>
.rich-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}
.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px 8px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}
.tool-btn {
  min-width: 28px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid transparent;
  background: #fff;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  line-height: 1;
  color: #606266;
}
.tool-btn:hover {
  border-color: #c6e2ff;
  color: #409eff;
  background: #ecf5ff;
}
.tool-sep {
  width: 1px;
  height: 18px;
  background: #dcdfe6;
  margin: 0 2px;
}
.tool-select {
  width: 90px;
}
.color-a {
  display: inline-block;
  padding: 0 2px;
  font-weight: bold;
}
.editor-content {
  min-height: 120px;
  max-height: 240px;
  overflow-y: auto;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.6;
  outline: none;
  background: #fff;
}
.editor-content:empty:before {
  content: '请输入内容…';
  color: #c0c4cc;
}
</style>
