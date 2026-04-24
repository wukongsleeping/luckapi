import { get, post, put, del } from './request.js'

export function getGroups(params = {}) {
	return get('/groups', params)
}

export function getGroup(id) {
	return get(`/groups/${id}`)
}

export function createGroup(data) {
	return post('/groups', data)
}

export function updateGroup(id, data) {
	return put(`/groups/${id}`, data)
}

export function deleteGroup(id) {
	return del(`/groups/${id}`)
}

export function assignUserToGroup(groupId, userId) {
	return post(`/groups/${groupId}/assign-user`, { user_id: userId })
}

export function removeUserFromGroup(groupId, userId) {
	return del(`/groups/${groupId}/assign-user/${userId}`)
}
