import request from '@/utils/request'

// 用户登录
export function login(data) {
  return request({
    url: '/api/login',
    method: 'post',
    data
  })
}

// 用户注册
export function register(data) {
  return request({
    url: '/api/register',
    method: 'post',
    data
  })
}

// 获取用户信息
export function getUserInfo(userId) {
  return request({
    url: '/api/user/info',
    method: 'get',
    params: userId ? { userId } : {}
  })
}

// 获取医生的医院列表
export function getUserHospitals() {
  return request({
    url: '/api/user/hospitals',
    method: 'get'
  })
}

// 退出登录
export function logout() {
  return request({
    url: '/api/logout',
    method: 'post'
  })
}

// 编辑用户信息
export function editUserInfo(data) {
  return request({
    url: '/api/user/update',
    method: 'put',
    data
  })
}

// 上传用户头像
export function uploadUserAvatar(avatarFile) {
  const formData = new FormData()
  formData.append('avatar', avatarFile)
  
  return request({
    url: '/user/upload_avatar',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
} 