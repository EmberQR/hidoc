import request from '@/utils/request'

export function getHomeData(hospital_id) {
  return request({
    url: '/api/home/data',
    method: 'get',
    params: { hospital_id }
  })
} 