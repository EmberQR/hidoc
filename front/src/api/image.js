import request from '@/utils/request'

// 获取当前医生创建的所有影像列表
export function listImages() {
    return request({
        url: '/api/image/list',
        method: 'get'
    })
}

// 上传新影像
export function addImage(formData) {
    return request({
        url: '/api/image/add',
        method: 'post',
        data: formData
        // axios 会自动为 FormData 设置正确的 Content-Type
    })
}

// 删除影像
export function deleteImage(image_id) {
    return request({
        url: `/api/image/${image_id}`,
        method: 'delete'
    })
}

// 编辑影像备注
export function updateImage(image_id, data) {
    return request({
        url: `/api/image/${image_id}`,
        method: 'put',
        data
    })
}

// 获取单个影像的预览信息
export function getImagePreview(image_id, params) {
  return request({
    url: `/api/image/${image_id}`,
    method: 'get',
    params
  })
}

export function addAnnotation(data) {
  return request({
    url: '/api/image/annotate',
    method: 'post',
    data
  })
}

export function getAnnotations(params) {
  return request({
    url: '/api/image/annotate',
    method: 'get',
    params
  })
}

export function deleteAnnotation(data) {
  return request({
    url: '/api/image/annotate',
    method: 'delete',
    data
  });
}

export function updateAnnotation(data) {
  return request({
    url: '/api/image/annotate',
    method: 'put',
    data
  });
}

// AI分割相关
export function addImageSeg(data) {
  return request({
    url: '/api/image/seg',
    method: 'post',
    data
  });
}

export function getImageSegList(params) {
  return request({
    url: '/api/image/seg/list',
    method: 'get',
    params
  });
} 