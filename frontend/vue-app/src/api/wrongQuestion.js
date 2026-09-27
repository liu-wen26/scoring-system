import request from './request'

// 错题管理
export const wrongQuestionApi = {
  // 获取错题列表
  getList(params) {
    return request.get('/api/v1/wrong-question/list', { params })
  },

  // 获取错题详情
  getDetail(id) {
    return request.get(`/api/v1/wrong-question/detail/${id}`)
  },

  // 更新错题标注
  updateTag(id, data) {
    return request.put(`/api/v1/wrong-question/tag/${id}`, data)
  },

  // 批量标注
  batchTag(data) {
    return request.post('/api/v1/wrong-question/batch-tag', data)
  },

  // 删除错题
  delete(id) {
    return request.delete(`/api/v1/wrong-question/${id}`)
  },

  // 获取错题分析
  getAnalysis(examId) {
    return request.get(`/api/v1/wrong-question/analysis/${examId}`)
  },

  // 获取学生错题本
  getWrongBook(studentId, params) {
    return request.get(`/api/v1/wrong-question/book/${studentId}`, { params })
  },

  // 导出错题本
  exportWrongBook(params) {
    return request.get('/api/v1/wrong-question/export', {
      params,
      responseType: 'blob'
    })
  },

  // 收藏错题
  collect(id) {
    return request.post(`/api/v1/wrong-question/collect/${id}`)
  },

  // 取消收藏
  uncollect(id) {
    return request.delete(`/api/v1/wrong-question/collect/${id}`)
  }
}
