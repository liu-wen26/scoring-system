import request from './request'

// 成绩报告
export const reportApi = {
  // 获取考试成绩报告
  getExamReport(examId, params) {
    return request.get(`/api/v1/report/exam/${examId}`, { params })
  },

  // 获取成绩排名
  getRanking(examId, params) {
    return request.get(`/api/v1/report/exam/${examId}/ranking`, { params })
  },

  // 获取学生个人报告
  getStudentReport(studentId, examId, subjectId) {
    return request.get(`/api/v1/report/student/${studentId}/report`, { params: { exam_id: examId, subject_id: subjectId } })
  },

  // 获取学生错题集
  getStudentWrongQuestions(studentId, examId, subjectId) {
    return request.get(`/api/v1/report/student/${studentId}/wrong-questions`, { params: { exam_id: examId, subject_id: subjectId } })
  },

  // 获取班级报告
  getClassReport(classId, examId, subjectId) {
    return request.get(`/api/v1/report/class/${classId}`, { params: { exam_id: examId, subject_id: subjectId } })
  },

  // 获取班级小题分析
  getQuestionAnalysis(classId, examId, subjectId) {
    return request.get(`/api/v1/report/class/${classId}/question-analysis`, { params: { exam_id: examId, subject_id: subjectId } })
  },

  // 获取各科成绩分析
  getSubjectAnalysis(examId) {
    return request.get(`/api/v1/report/subject-analysis/${examId}`)
  },

  // 获取学生成绩趋势
  getScoreTrend(studentId, subjectId) {
    return request.get(`/api/v1/report/trend/${studentId}`, { params: { subject_id: subjectId } })
  },

  // 导出报告
  exportReport(examId, data) {
    return request.post(`/api/v1/report/export/${examId}`, data)
  }
}
