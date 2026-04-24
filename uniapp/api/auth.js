import { get, post } from './request.js'

export function login(data) {
	return post('/auth/login', data)
}

export function logout() {
	return post('/auth/logout')
}

export function getMe() {
	return get('/auth/me')
}
