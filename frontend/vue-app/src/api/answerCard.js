import request from './request'

export const getAnswerCardTemplates = (params = {}) => {
  return request.get('/api/v1/answer-card/templates', { params })
}

export const getAnswerCardTemplate = (id) => {
  return request.get(`/api/v1/answer-card/templates/${id}`)
}

export const createAnswerCardTemplate = (data) => {
  return request.post('/api/v1/answer-card/templates', data)
}

export const updateAnswerCardTemplate = (id, data) => {
  return request.put(`/api/v1/answer-card/templates/${id}`, data)
}

export const deleteAnswerCardTemplate = (id) => {
  return request.delete(`/api/v1/answer-card/templates/${id}`)
}

export const uploadThirdPartyTemplate = (formData) => {
  return request.post('/api/v1/answer-card/third-party', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getAnswerCardConfig = (examId, subjectId) => {
  return request.get('/api/v1/answer-card/config', {
    params: { examId, subjectId }
  })
}

export const saveAnswerCardConfig = (data) => {
  return request.post('/api/v1/answer-card/config', data)
}

export const listExamAnswerCardConfigs = (examId) => {
  return request.get('/api/v1/answer-card/config/list', {
    params: { examId }
  })
}

export const uploadAnswerCardTemplate = (file, examId, subjectId) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('examId', examId)
  formData.append('subjectId', subjectId)
  return request.post('/api/v1/answer-card/upload-template', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
