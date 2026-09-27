import request from './request'

// 阅卷管理
export const markApi = {
  // 获取阅卷分配列表
  getAllocations(params) {
    return request.get('/api/v1/mark/allocations', { params })
  },

  // 创建阅卷分配
  createAllocation(data) {
    return request.post('/api/v1/mark/allocations', data)
  },

  // 删除阅卷分配
  deleteAllocation(id) {
    return request.delete(`/api/v1/mark/allocations/${id}`)
  },

  // 批量删除阅卷分配
  batchDeleteAllocations(ids) {
    return request.delete('/api/v1/mark/allocations', { params: { allocation_ids: ids } })
  },

  // 获取当前用户的阅卷任务
  getTasks(status = 'pending') {
    return request.get('/api/v1/mark/tasks', { params: { status } })
  },

  // 获取试卷详情
  getPaperDetail(scanPageId) {
    return request.get(`/api/v1/mark/paper/${scanPageId}`)
  },

  // 提交阅卷分数
  submitScore(scanPageId, data) {
    return request.post(`/api/v1/mark/score/${scanPageId}`, data)
  },

  // 获取阅卷进度
  getProgress(examId, subjectId) {
    return request.get(`/api/v1/mark/progress/${examId}`, { params: { subject_id: subjectId } })
  },

  // 获取阅卷结果列表
  getResults(examId, params) {
    return request.get(`/api/v1/mark/results/${examId}`, { params })
  },

  // 复核分数（仲裁）
  reviewScore(resultId, data) {
    return request.post(`/api/v1/mark/review/${resultId}`, data)
  },

  // 获取按题阅卷任务列表
  getQuestionMarkTasks(params) {
    const { examId, subjectId, questionNo, status } = params
    return request.get(`/api/v1/mark/tasks/question/${examId}/${subjectId}`, {
      params: { question_no: questionNo, status }
    })
  },

  // 提交单题阅卷分数
  submitQuestionScore(resultId, data) {
    return request.post(`/api/v1/mark/score/question/${resultId}`, data)
  },

  // AI 阅卷配置
  getAIConfig() {
    return request.get('/api/v1/mark/ai/config')
  },
  saveAIConfig(data) {
    return request.post('/api/v1/mark/ai/config', data)
  },

  // AI 阅卷任务
  createAIMarkTask(data) {
    return request.post('/api/v1/mark/ai/tasks', data)
  },
  getAIMarkTask(taskId) {
    return request.get(`/api/v1/mark/ai/tasks/${taskId}`)
  },
  stopAIMarkTask(taskId) {
    return request.post(`/api/v1/mark/ai/tasks/${taskId}/stop`)
  },
  getNextAIPaper(taskId) {
    return request.post(`/api/v1/mark/ai/tasks/${taskId}/next`)
  },
  scoreAIPaper(taskId) {
    return request.post(`/api/v1/mark/ai/tasks/${taskId}/score`)
  }
}

// 便捷导出
export const getQuestionMarkTasks = markApi.getQuestionMarkTasks
export const submitQuestionScore = markApi.submitQuestionScore
export const getAIConfig = markApi.getAIConfig
export const saveAIConfig = markApi.saveAIConfig
export const createAIMarkTask = markApi.createAIMarkTask
export const getAIMarkTask = markApi.getAIMarkTask
export const stopAIMarkTask = markApi.stopAIMarkTask
export const getNextAIPaper = markApi.getNextAIPaper
export const scoreAIPaper = markApi.scoreAIPaper
