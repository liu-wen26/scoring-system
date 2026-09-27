import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  
  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => userInfo.value?.role || '')
  
  // Actions
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }
  
  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }
  
  const login = async (credentials) => {
    const res = await loginApi(credentials)
    setToken(res.accessToken)
    userInfo.value = res.user
    return res
  }
  
  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const res = await getMe()
      userInfo.value = res
    } catch (error) {
      clearToken()
      throw error
    }
  }
  
  const logout = () => {
    clearToken()
  }
  
  return {
    token,
    userInfo,
    isLoggedIn,
    userRole,
    login,
    fetchUserInfo,
    logout
  }
})
