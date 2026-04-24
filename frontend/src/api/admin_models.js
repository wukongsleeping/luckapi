import request from './request'

export function getGlobalModels(params = {}) {
  return request.get('/models', { params })
}

export function getGlobalModel(id) {
  return request.get(`/models/${id}`)
}

export function createGlobalModel(data) {
  return request.post('/models', data)
}

export function updateGlobalModel(id, data) {
  return request.put(`/models/${id}`, data)
}

export function deleteGlobalModel(id) {
  return request.delete(`/models/${id}`)
}
