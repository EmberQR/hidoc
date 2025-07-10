import request from '@/utils/request'

/**
 * 获取当前医生指定医院的科室列表
 * @param {object} params - 查询参数，例如 { hospital_id: 1 }
 */
export function getOffices(params) {
  return request({
    url: '/api/hospital/office',
    method: 'get',
    params
  })
}

/**
 * 查询病历列表
 * @param {object} params - 查询参数，例如 { office_id: 1, patient_name: '张三', page: 1, per_page: 10 }
 */
export function getCases(params) {
  return request({
    url: '/api/hospital/case',
    method: 'get',
    params
  })
}

/**
 * 添加新病人
 * @param {object} data - 病人信息，例如 { name: '李四', gender: '男', birthday: '2000-01-01' }
 */
export function addPatient(data) {
  return request({
    url: '/api/hospital/add_patient',
    method: 'post',
    data
  })
}

/**
 * 添加新病历
 * @param {object} data - 病历信息
 */
export function addCase(data) {
  return request({
    url: '/api/hospital/case',
    method: 'post',
    data
  })
}

/**
 * 更新病历
 * @param {object} data - 病历信息，必须包含 id
 */
export function updateCase(data) {
  return request({
    url: '/api/hospital/case',
    method: 'put',
    data
  })
}

/**
 * 根据姓名搜索病人
 * @param {object} params - 查询参数，例如 { name: '张三' }
 */
export function searchPatients(params) {
  return request({
    url: '/api/hospital/patient',
    method: 'get',
    params
  })
}

export function getCaseById(case_id) {
    return request({
        url: '/api/hospital/case/single',
        method: 'get',
        params: { case_id }
    })
}