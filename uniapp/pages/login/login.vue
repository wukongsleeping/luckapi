<template>
	<view class="login-page">
		<!-- Background decoration -->
		<view class="bg-glow" />
		
		<view class="login-card">
			<view class="brand">
				<view class="logo">
					<view class="logo-icon" />
				</view>
				<text class="brand-name">LuckApi</text>
				<text class="brand-subtitle">移动端管理面板</text>
			</view>

			<view class="form">
				<view class="form-item">
					<input
						v-model="form.username"
						placeholder="用户名"
						class="input"
						:adjust-padding="false"
						:focus="focusState === 'username'"
					/>
					<view class="input-hint" v-if="focusState === 'username'">
						请输入您的登录用户名
					</view>
				</view>
				<view class="form-item">
					<input
						v-model="form.password"
						type="password"
						placeholder="密码"
						class="input"
						:adjust-padding="false"
						:focus="focusState === 'password'"
					/>
					<view class="input-hint" v-if="focusState === 'password'">
						请输入登录密码，至少 8 位
					</view>
				</view>
				<button
					class="btn-login"
					:loading="loading"
					:disabled="loading"
					@click="handleLogin"
				>
					登录
				</button>
			</view>

			<!-- Server Address -->
			<view class="server-section">
				<view class="server-info">
					<text class="server-indicator" />
					<text class="server-label">{{ currentServer }}</text>
				</view>
				<text class="https-warning" v-if="!isHttps">⚠ HTTP</text>
				<view class="btn-server" @click="openServerDialog">
					<text class="btn-server-icon">⚙</text>
					<text class="btn-server-text">修改</text>
				</view>
			</view>
		</view>

		<!-- Server Dialog -->
		<view class="dialog-mask" v-if="showDialog" @click="showDialog = false">
			<view class="dialog" @click.stop>
				<text class="dialog-title">配置服务器</text>
				<view class="input-hint" style="margin-bottom: 20rpx; text-align: left;">
					请输入 API 地址，例如：<br>
					<text style="color: #34d399;">http://10.222.9.24:8000/admin/api</text>
				</view>
				<textarea
					v-model="serverUrl"
					placeholder="http://服务器 IP:8000/admin/api"
					class="dialog-input"
					:adjust-padding="false"
					maxlength="200"
				/>
				<button class="dialog-btn" @click="confirmServer">保存</button>
				<button class="dialog-btn cancel" @click="showDialog = false">取消</button>
			</view>
		</view>
	</view>
</template>

<script>
	import { authStore } from '@/store/auth.js'
	import { getBaseUrl, setBaseUrl } from '@/api/config.js'

	export default {
		data() {
			return {
				loading: false,
				showDialog: false,
				focusState: '',
				serverUrl: '',
				form: {
					username: '',
					password: ''
				}
			}
		},
		computed: {
			currentServer() {
				return getBaseUrl()
			},
			isHttps() {
				return getBaseUrl().startsWith('https://')
			}
		},
		onLoad() {
			if (authStore.isLoggedIn) {
				uni.switchTab({ url: '/pages/users/users' })
			}
		},
		methods: {
			openServerDialog() {
				this.serverUrl = getBaseUrl()
				this.showDialog = true
			},
			confirmServer() {
				if (!this.serverUrl) {
					uni.showToast({ title: '服务器地址不能为空', icon: 'none' })
					return
				}
				let url = this.serverUrl.trim()
				if (!url.startsWith('http://') && !url.startsWith('https://')) {
					uni.showToast({ title: '需要以 http:// 或 https:// 开头', icon: 'none' })
					return
				}
				setBaseUrl(url)
				this.showDialog = false
				uni.showToast({ title: '已保存', icon: 'success' })
			},
			async handleLogin() {
				if (!this.form.username || !this.form.password) {
					uni.showToast({ title: '请填写用户名和密码', icon: 'none' })
					return
				}
				this.loading = true
				try {
					await authStore.login(this.form.username, this.form.password)
					uni.switchTab({ url: '/pages/users/users' })
				} catch (err) {
					uni.showToast({ title: err.message || '登录失败', icon: 'none' })
				} finally {
					this.loading = false
				}
			}
		}
	}
</script>

<style>
	.login-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #0f172a;
		position: relative;
		overflow: hidden;
	}

	.bg-glow {
		position: absolute;
		top: -100rpx;
		left: -100rpx;
		width: 600rpx;
		height: 600rpx;
		background: radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%);
		border-radius: 50%;
		pointer-events: none;
	}

	.login-card {
		width: 90%;
		max-width: 600rpx;
		padding: 60rpx 40rpx 40rpx;
		background: #1e293b;
		border: 1rpx solid #334155;
		border-radius: 32rpx;
		text-align: center;
		box-shadow: 0 24rpx 48rpx rgba(0, 0, 0, 0.4);
		position: relative;
		z-index: 1;
	}

	.brand {
		margin-bottom: 48rpx;
	}

	.logo {
		width: 120rpx;
		height: 120rpx;
		margin: 0 auto 24rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		border-radius: 32rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.25);
	}

	.logo-icon {
		width: 48rpx;
		height: 48rpx;
		background: #fff;
		border-radius: 12rpx;
	}

	.brand-name {
		font-size: 56rpx;
		font-weight: 800;
		color: #f1f5f9;
		letter-spacing: -1rpx;
		display: block;
		margin-bottom: 8rpx;
	}

	.brand-subtitle {
		font-size: 26rpx;
		color: #94a3b8;
		letter-spacing: 0.5rpx;
	}

	.form {
		margin-bottom: 32rpx;
	}

	.form-item {
		margin-bottom: 24rpx;
	}

	.input {
		width: 100%;
		height: 88rpx;
		background: #0f172a;
		border: 2rpx solid #334155;
		border-radius: 16rpx;
		padding: 0 24rpx;
		color: #f1f5f9;
		font-size: 30rpx;
	}

	.input:focus {
		border-color: #10b981;
	}

	.input-hint {
		margin-top: 10rpx;
		font-size: 22rpx;
		color: #64748b;
		line-height: 1.5;
	}

	.btn-login {
		margin-top: 40rpx;
		width: 100%;
		height: 92rpx;
		line-height: 92rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		font-size: 32rpx;
		font-weight: 600;
		border-radius: 16rpx;
		border: none;
		box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.25);
	}

	.btn-login:active {
		opacity: 0.9;
		transform: scale(0.98);
	}

	.server-section {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-top: 24rpx;
		border-top: 1rpx solid #334155;
	}

	.server-info {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 10rpx;
	}

	.server-indicator {
		width: 10rpx;
		height: 10rpx;
		background: #10b981;
		border-radius: 50%;
	}

	.server-label {
		font-size: 22rpx;
		color: #94a3b8;
		word-break: break-all;
	}

	.btn-server {
		display: flex;
		align-items: center;
		gap: 6rpx;
		padding: 10rpx 20rpx;
		border-radius: 10rpx;
	}

	.btn-server:active {
		background: rgba(148, 163, 184, 0.1);
	}

	.btn-server-icon {
		font-size: 28rpx;
		color: #94a3b8;
	}

	.btn-server-text {
		font-size: 24rpx;
		color: #94a3b8;
	}

	.https-warning {
		color: #f59e0b;
		font-size: 22rpx;
		margin-left: 12rpx;
		white-space: nowrap;
	}
</style>
