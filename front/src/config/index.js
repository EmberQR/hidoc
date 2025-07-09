// API基础URL配置
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://hidoc.ember.ac.cn/api'
  : 'http://localhost:9888/'

export default {
  API_BASE_URL
} 