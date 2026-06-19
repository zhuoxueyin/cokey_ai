import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import { message } from 'antd'

function extractErrorMessage(error: any): string {
  const data = error?.response?.data
  if (!data) return error?.message || '网络异常'
  if (typeof data.detail === 'string') return data.detail
  if (data.message) return data.message
  if (Array.isArray(data.detail)) {
    return data.detail.map((d: any) => d?.msg || String(d)).join('; ')
  }
  return '请求失败'
}

function handleUnauthorized(error: any) {
  if (error?.response?.status !== 401) return
  if (window.location.pathname === '/login') return
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  message.error(extractErrorMessage(error) || '登录已过期，请重新登录')
  window.location.href = '/login'
}

const attachAuthHeader = (instance: AxiosInstance) => {
  instance.interceptors.request.use(
    (config: any) => {
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error),
  )
}

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟基础超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 用于长时间任务的请求实例（30分钟超时）
export const longRunningService: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 1800000, // 30分钟超时，用于生图、视频等耗时任务
  headers: {
    'Content-Type': 'application/json',
  },
})

// 配置长时间任务请求的拦截器
longRunningService.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    if (res && res.code !== undefined) {
      if (res.code === 'success') {
        return res
      } else {
        message.error(res.message || '请求失败')
        return Promise.reject(res)
      }
    }
    return response.data
  },
  (error) => {
    handleUnauthorized(error)
    message.error(extractErrorMessage(error))
    return Promise.reject(error)
  }
)

attachAuthHeader(longRunningService)

attachAuthHeader(service)

service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    if (res && res.code !== undefined) {
      if (res.code === 'success') {
        return res
      } else {
        message.error(res.message || '请求失败')
        return Promise.reject(res)
      }
    }
    return response.data
  },
  (error) => {
    handleUnauthorized(error)
    message.error(extractErrorMessage(error))
    return Promise.reject(error)
  }
)

export default service
