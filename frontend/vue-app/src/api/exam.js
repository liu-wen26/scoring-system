import request from './request'

export const getExams = (params) => {
  return request.get('/api/v1/exam/', { params })
}

export const getExam = (id) => {
  return request.get(`/api/v1/exam/${id}`)
}

export const createExam = (data) => {
  return request.post('/api/v1/exam/', data)
}

export const updateExam = (id, data) => {
  return request.put(`/api/v1/exam/${id}`, data)
}

export const deleteExam = (id) => {
  return request.delete(`/api/v1/exam/${id}`)
}

export const updateExamStatus = (id, status) => {
  return request.put(`/api/v1/exam/${id}/status`, null, { params: { status } })
}

export const getSubjectsByExam = (examId) => {
  return request.get(`/api/v1/exam/${examId}/subjects`)
}

export const getSubjects = (params) => {
  return request.get('/api/v1/exam/meta/subjects', { params })
}

export const getGrades = () => {
  return request.get('/api/v1/exam/meta/grades')
}

export const getClasses = (gradeId) => {
  const params = {}
  if (gradeId) params.gradeId = gradeId
  return request.get('/api/v1/exam/meta/classes', { params })
}

export const getStudentCount = (params) => {
  return request.get('/api/v1/exam/meta/student-count', { params })
}

export const getExamQuestions = (examId, subjectId) => {
  return request.get(`/api/v1/exam/${examId}/questions`, { params: { subjectId } })
}
