import config from './config.js'

function request(url, method = 'GET', data = null, needAuth = true) {
	return new Promise((resolve, reject) => {
		const header = {
			'Content-Type': 'application/json',
		}
		if (needAuth) {
			const token = uni.getStorageSync('luckapi_token')
			if (token) {
				header['Authorization'] = `Bearer ${token}`
			}
		}

		const fullUrl = config.baseURL + url

		uni.request({
			url: fullUrl,
			method,
			data: data,
			header,
			timeout: config.timeout,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res.data)
				} else if (res.statusCode === 401) {
					uni.removeStorageSync('luckapi_token')
					uni.removeStorageSync('luckapi_user')
					uni.showToast({ title: '请重新登录', icon: 'none' })
					setTimeout(() => {
						uni.reLaunch({ url: '/pages/login/login' })
					}, 1500)
					reject(new Error('Unauthorized'))
				} else {
					const detail = res.data?.detail || '请求失败'
					uni.showToast({ title: detail, icon: 'none' })
					reject(new Error(detail))
				}
			},
			fail: (err) => {
				uni.showToast({ title: '网络错误', icon: 'none' })
				reject(err)
			}
		})
	})
}

export function get(url, params = {}) {
	return request(url, 'GET', params)
}

export function post(url, data = {}) {
	return request(url, 'POST', data)
}

export function put(url, data = {}) {
	return request(url, 'PUT', data)
}

export function del(url) {
	return request(url, 'DELETE')
}
