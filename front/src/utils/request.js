import axios from 'axios'
import { ElMessage } from 'element-plus'
import config from '../config'

// 创建axios实例
const service = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: 60000,
  withCredentials: true
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 为AI相关的API设置更长的超时时间（120秒）
    if (config.url && config.url.includes('/ai/')) {
      config.timeout = 120000 // 120秒
    }

    if (config.url && config.url.includes('/ai-chat/')){
      config.timeout = 120000 // 120秒
    }

    if (config.url && config.url.includes('/image/')){
      config.timeout = 600000 // 10分钟
    }
    
    // 从localStorage中获取token（如果有）
    const userInfo = localStorage.getItem('userInfo')
    if (userInfo) {
      try {
        const user = JSON.parse(userInfo)
        if (user && user.token) {
          // 在请求头中添加token
          config.headers['Authorization'] = user.token;
        }
      } catch (e) {
        console.error('解析用户信息失败', e)
      }
    }
    return config
  },
  error => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    // 根据后端接口约定，判断请求是否成功
    if (res.code && res.code !== 200 && res.code !== 201) {
      // 如果是未登录状态
      if (res.code === 401) {
        // 清除本地存储的用户信息
        localStorage.removeItem('userInfo')
      }
      
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    } else {
      return res
    }
  },
  error => {
    // 处理401未授权错误
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('userInfo')
      // 非登录页面才跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    console.error('响应错误：', error)
    ElMessage.error(error.message || '服务器异常')
    return Promise.reject(error)
  }
)

export default service 