import request from './request'

export const login = (data) => {
  return request.post('/api/v1/user/login', data)
}

export const getMe = () => {
  return request.get('/api/v1/user/me')
}

export const getUsers = (params) => {
  return request.get('/api/v1/user/', { params })
}

export const createUser = (data) => {
  return request.post('/api/v1/user/', data)
}

export const updateUser = (id, data) => {
  return request.put(`/api/v1/user/${id}`, data)
}

export const deleteUser = (id) => {
  return request.delete(`/api/v1/user/${id}`)
}

// 学生档案
export const getStudents = (params) => {
  return request.get('/api/v1/user/students', { params })
}

export const getStudent = (id) => {
  return request.get(`/api/v1/user/students/${id}`)
}

export const createStudent = (data) => {
  return request.post('/api/v1/user/students', data)
}

export const batchCreateStudents = (data) => {
  return request.post('/api/v1/user/students/batch', data)
}

export const updateStudent = (id, data) => {
  return request.put(`/api/v1/user/students/${id}`, data)
}

export const deleteStudent = (id) => {
  return request.delete(`/api/v1/user/students/${id}`)
}

// 教师档案
export const getTeachers = (params) => {
  return request.get('/api/v1/user/teachers', { params })
}

export const getTeacher = (id) => {
  return request.get(`/api/v1/user/teachers/${id}`)
}

export const createTeacher = (data) => {
  return request.post('/api/v1/user/teachers', data)
}

export const batchCreateTeachers = (data) => {
  return request.post('/api/v1/user/teachers/batch', data)
}

export const updateTeacher = (id, data) => {
  return request.put(`/api/v1/user/teachers/${id}`, data)
}

export const deleteTeacher = (id) => {
  return request.delete(`/api/v1/user/teachers/${id}`)
}
