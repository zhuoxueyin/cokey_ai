import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

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
    const msg = error.response?.data?.message || error.message || '网络异常'
    message.error(msg)
    return Promise.reject(error)
  }
)

service.interceptors.request.use(
  (config: any) => {
    // 自动添加JWT令牌
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

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
    const msg = error.response?.data?.message || error.message || '网络异常'
    message.error(msg)
    return Promise.reject(error)
  }
)

export default service
