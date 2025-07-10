import request from '@/utils/request';

/**
 * 获取当前医生负责的病人列表
 * @param {object} params - 查询参数，如 { page, per_page }
 */
export function getPatientList(params) {
  return request({
    url: '/api/patient/list',
    method: 'get',
    params
  });
}

/**
 * 获取指定病人的病历列表
 * @param {object} params - 查询参数，如 { patient_id, page, per_page }
 */
export function getPatientCases(params) {
  return request({
    url: '/api/patient/case',
    method: 'get',
    params
  });
}

/**
 * 获取指定病人的AI辅诊记录列表
 * @param {object} params - 查询参数，如 { patient_id, page, per_page }
 */
export function getPatientAnalyses(params) {
  return request({
    url: '/api/patient/analyze',
    method: 'get',
    params
  });
}

/**
 * 对指定病人发起新的AI分析
 * @param {number} patientId - 病人ID
 */
export function startPatientAnalysis(patientId) {
  return request({
    url: '/api/patient/analyze',
    method: 'post',
    data: { patient_id: patientId }
  });
}

/**
 * 获取指定病人的详细信息
 * @param {number} patientId - 病人ID
 */
export function getPatientDetail(patientId) {
  return request({
    url: '/api/patient/detail',
    method: 'get',
    params: { patient_id: patientId }
  });
} 