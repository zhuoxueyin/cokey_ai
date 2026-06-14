import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
})

service.interceptors.request.use(
  (config: AxiosRequestConfig) => {
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
