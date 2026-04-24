import { get, post } from './request.js'

export function getUsers(params = {}) {
	return get('/users', params)
}

export function getUser(id) {
	return get(`/users/${id}`)
}

export function createUser(data) {
	return post('/users', data)
}

export function updateUser(id, data) {
	return put(`/users/${id}`, data)
}

export function deleteUser(id) {
	return del(`/users/${id}`)
}

export function fetchApiKey(userId) {
	return get(`/users/${userId}/api-keys`)
}

export function renewApiKey(userId) {
	return post(`/users/${userId}/api-keys/renew`)
}
