import { getUserInfo } from '@/api/user'

// 检查用户是否已登录
export function isLoggedIn() {
  return localStorage.getItem('userInfo') !== null
}

// 获取用户信息
export function getStoredUserInfo() {
  try {
    const userInfo = localStorage.getItem('userInfo')
    return userInfo ? JSON.parse(userInfo) : null
  } catch (e) {
    console.error('解析用户信息失败', e)
    return null
  }
}

// 设置用户信息
export function setUserInfo(userInfo) {
  localStorage.setItem('userInfo', JSON.stringify(userInfo))
}

// 清除用户信息
export function clearUserInfo() {
  localStorage.removeItem('userInfo')
}

// 获取当前选择的医院
export function getCurrentHospital() {
  try {
    const hospitalInfo = localStorage.getItem('currentHospital')
    return hospitalInfo ? JSON.parse(hospitalInfo) : null
  } catch (e) {
    console.error('解析医院信息失败', e)
    return null
  }
}

// 校验登录状态
export function checkLoginStatus() {
  if (!isLoggedIn()) {
    return Promise.resolve(false)
  }
  
  // 调用后端接口验证登录状态
  return getUserInfo()
    .then(res => {
      if (res.code === 200 && res.data) {
        // 更新用户信息
        setUserInfo(res.data)
        return true
      } else {
        clearUserInfo()
        return false
      }
    })
    .catch(() => {
      clearUserInfo()
      return false
    })
} 