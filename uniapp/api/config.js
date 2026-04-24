const STORAGE_KEY_BASE_URL = 'luckapi_baseUrl'
const DEFAULT_BASE_URL = 'http://10.222.9.24:8000/admin/api'

const TIMEOUT = 30000

export function getBaseUrl() {
	try {
		const stored = uni.getStorageSync(STORAGE_KEY_BASE_URL)
		if (stored && stored.startsWith('http')) {
			return stored
		}
	} catch (e) {
		// ignore
	}
	return DEFAULT_BASE_URL
}

export function isHttps(url) {
	return url && (url.startsWith('https://') || url.startsWith('wss://'))
}

export function getHttpsWarning(url) {
	if (!url) return false
	if (url.startsWith('http://')) return '当前使用 HTTP 协议，建议配置 HTTPS 以保护通信安全'
	return false
}

export default {
	get baseURL() {
		return getBaseUrl()
	},
	get timeout() {
		return TIMEOUT
	}
}

export function setBaseUrl(url) {
	try {
		uni.setStorageSync(STORAGE_KEY_BASE_URL, url)
	} catch (e) {
		// ignore
	}
}
