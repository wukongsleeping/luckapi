import request from './request'

export function getGroups(params = {}) {
  return request.get('/groups', { params })
}

export function getGroup(id) {
  return request.get(`/groups/${id}`)
}

export function createGroup(data) {
  return request.post('/groups', data)
}

export function updateGroup(id, data) {
  return request.put(`/groups/${id}`, data)
}

export function deleteGroup(id) {
  return request.delete(`/groups/${id}`)
}

export function assignGroupUser(groupId, userId) {
  return request.post(`/groups/${groupId}/assign-user`, { user_id: userId })
}

export function removeGroupUser(groupId, userId) {
  return request.delete(`/groups/${groupId}/assign-user/${userId}`)
}

export function assignGroupModel(id, data) {
  return request.post(`/groups/${id}/models`, { model_name: data.model_name, api_url: data.api_url, api_key: data.api_key })
}
