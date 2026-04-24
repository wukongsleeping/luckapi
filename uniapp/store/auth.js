import { login as loginAPI, getMe, logout as logoutAPI } from '@/api/auth.js'

const STORAGE_KEY_TOKEN = 'luckapi_token'
const STORAGE_KEY_USER = 'luckapi_user'

let token = ''
let user = null
try {
	token = uni.getStorageSync(STORAGE_KEY_TOKEN) || ''
	user = JSON.parse(uni.getStorageSync(STORAGE_KEY_USER) || 'null')
} catch (e) {
	console.warn('Failed to read auth storage, session may be lost: ' + e.message)
}

const state = {
	token: token,
	user: user
}

function save() {
	uni.setStorageSync(STORAGE_KEY_TOKEN, state.token)
	uni.setStorageSync(STORAGE_KEY_USER, JSON.stringify(state.user))
}

export const authStore = {
	get token() { return state.token },
	get isLoggedIn() { return !!state.token },
	get user() { return state.user },
	get userName() { return state.user ? (state.user.username || '') : '' },
	async login(username, password) {
		const res = await loginAPI({ username, password })
		const data = res.data || res
		if (data.access_token) {
			state.token = data.access_token
			state.user = data.user || null
			save()
		}
	},
	async fetchUser() {
		if (!state.token) return
		try {
			const res = await getMe()
			if (res.data || res) {
				state.user = res.data || res
				save()
			}
		} catch (e) {
			console.error('Failed to fetch user:', e)
		}
	},
	async logout() {
		try {
			await logoutAPI()
		} catch (e) {
			console.error('Logout API failed:', e)
		}
		state.token = ''
		state.user = null
		uni.removeStorageSync(STORAGE_KEY_TOKEN)
		uni.removeStorageSync(STORAGE_KEY_USER)
	},
	setToken(token) {
		state.token = token
		save()
	},
	setUser(user) {
		state.user = user
		save()
	},
	clearSession() {
		state.token = ''
		state.user = null
		uni.removeStorageSync(STORAGE_KEY_TOKEN)
		uni.removeStorageSync(STORAGE_KEY_USER)
	}
}
