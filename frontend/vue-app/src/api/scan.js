import request from './request'

export function reprocessScanPage(scanPageId) {
  return request.post(`/api/v1/scan/reprocess/${scanPageId}`)
}

export function reprocessExamSubject(examId, subjectId) {
  return request.post(`/api/v1/scan/reprocess/exam/${examId}/${subjectId}`)
}
