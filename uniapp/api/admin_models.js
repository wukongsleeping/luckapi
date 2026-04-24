import { get, post, put, del } from './request.js'

export function getModels(params = {}) {
	return get('/models', params)
}

export function getModel(id) {
	return get(`/models/${id}`)
}

export function createModel(data) {
	return post('/models', data)
}

export function updateModel(id, data) {
	return put(`/models/${id}`, data)
}

export function deleteModel(id) {
	return del(`/models/${id}`)
}
