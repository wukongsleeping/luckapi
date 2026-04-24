<template>
	<view class="user-detail-page">
		<view class="section">
			<text class="section-title">基本信息</text>
			<view class="form-item">
				<text class="label">用户名</text>
				<input v-model="form.username" placeholder="用户名" class="input" disabled />
			</view>
			<view class="form-item">
				<text class="label">显示名称</text>
				<input v-model="form.display_name" placeholder="显示名称" class="input" />
			</view>
			<view class="form-item">
				<text class="label">角色</text>
				<picker :value="roleIndex" :range="roleOptions" @change="onRoleChange">
					<view class="picker-input">{{ roleOptions[roleIndex] === 'user' ? '普通用户' : '管理员' }}</view>
				</picker>
			</view>
			<view class="form-item">
				<text class="label">状态</text>
				<picker :value="statusIndex" :range="statusOptions" @change="onStatusChange">
					<view class="picker-input">{{ statusOptions[statusIndex] }}</view>
				</picker>
			</view>
			<view class="form-item">
				<text class="label">初始余额</text>
				<input v-model.number="form.initial_balance" type="number" placeholder="初始余额" class="input" />
			</view>
			<view class="form-item">
				<text class="label">IP 白名单</text>
				<text class="ip-hint">{{ ipHint }}</text>
				<input
					v-model="newIp"
					placeholder="输入 IP 地址后点击添加"
					class="add-ip-input"
				/>
				<button class="add-ip-btn" @click="addIp">添加</button>
				<view class="ip-list" v-if="ipList.length > 0">
					<view v-for="(ip, index) in ipList" :key="index" class="ip-item">
						<text>{{ ip }}</text>
						<text class="remove-ip" @click="removeIp(index)">✕</text>
					</view>
				</view>
			</view>
		</view>

		<view class="section" v-if="userDetail.group_names && userDetail.group_names.length > 0">
			<text class="section-title">所属分组</text>
			<view class="group-tags">
				<text class="group-tag" v-for="(name, idx) in userDetail.group_names" :key="idx">{{ name }}</text>
			</view>
		</view>

		<view class="section" v-if="apiKey">
			<text class="section-title">API Key</text>
			<view class="api-key-box">
				<text class="api-key-text">{{ apiKey }}</text>
				<button class="copy-btn" @click="copyKey">复制</button>
			</view>
			<button class="renew-btn" @click="renewKey">刷新 API Key</button>
		</view>

		<view class="btn-save">
			<button class="save-btn" @click="handleSave">保存</button>
		</view>
	</view>
</template>

<script>
	import { getUser, updateUser, fetchApiKey, renewApiKey } from '@/api/users.js'

	export default {
		data() {
			return {
				userDetail: {},
				apiKey: '',
				form: {
					username: '',
					display_name: '',
					initial_balance: 0,
					allowed_ips: null
				},
				ipList: [],
				newIp: '',
				roleOptions: ['user', 'admin'],
				statusOptions: ['active', 'banned', 'disabled'],
				roleIndex: 0,
				statusIndex: 0
			}
		},
		computed: {
			ipHint() {
				return this.form.allowed_ips || '多个 IP 用逗号分隔'
			}
		},
		onLoad(options) {
			if (options.id) {
				this.fetchUserDetail(options.id)
			}
		},
		methods: {
			async fetchUserDetail(id) {
				try {
					const res = await getUser(id)
					this.userDetail = res
					Object.assign(this.form, {
						username: res.username || '',
						display_name: res.display_name || '',
						initial_balance: res.balance || 0,
						allowed_ips: res.allowed_ips || ''
					})
					this.ipList = this.parseIpList(res.allowed_ips)
					this.roleIndex = this.roleOptions.indexOf(res.role || 'user')
					this.statusIndex = this.statusOptions.indexOf(res.status || 'active')
					this.fetchApiKey(id)
				} catch (err) {
					console.error('Failed to fetch user detail:', err)
				}
			},
			async fetchApiKey(userId) {
				try {
					const res = await fetchApiKey(userId)
					if (res && res.length > 0) {
						this.apiKey = res[0].key
						if (typeof this.apiKey === 'string' && this.apiKey.length > 20) {
							this.apiKey = this.apiKey.substring(0, 20) + '...'
						}
					}
				} catch (err) {
					console.error('Failed to fetch api key:', err)
				}
			},
			parseIpList(str) {
				if (!str) return []
				return str.split(',').map(s => s.trim()).filter(Boolean)
			},
			addIp() {
				const ip = this.newIp.trim()
				if (!ip) return
				if (this.ipList.includes(ip)) {
					uni.showToast({ title: 'IP 已存在', icon: 'none' })
					return
				}
				this.ipList.push(ip)
				this.form.allowed_ips = this.ipList.join(',')
				this.newIp = ''
			},
			removeIp(index) {
				this.ipList.splice(index, 1)
				this.form.allowed_ips = this.ipList.join(',')
			},
			onRoleChange(e) {
				this.roleIndex = e.detail.value
				this.form.role = this.roleOptions[this.roleIndex]
			},
			onStatusChange(e) {
				this.statusIndex = e.detail.value
				this.form.status = this.statusOptions[this.statusIndex]
			},
			async handleSave() {
				try {
					const data = {
						display_name: this.form.display_name,
						initial_balance: this.form.initial_balance,
						allowed_ips: this.form.allowed_ips || null,
						role: this.form.role || 'user',
						status: this.form.status || 'active'
					}
					await updateUser(this.userDetail.id, data)
					uni.showToast({ title: '保存成功', icon: 'success' })
				} catch (err) {
					console.error('Save failed:', err)
				}
			},
			async renewKey() {
				uni.showModal({
					title: '确认刷新',
					content: '刷新后将生成新的 API Key，旧 Key 将失效。',
					success: async (res) => {
						if (res.confirm) {
							try {
								await renewApiKey(this.userDetail.id)
								this.apiKey = ''
								this.fetchApiKey(this.userDetail.id)
								uni.showToast({ title: 'API Key 已刷新', icon: 'success' })
							} catch (err) {
								console.error('Renew key failed:', err)
							}
						}
					}
				})
			},
			copyKey() {
				uni.setClipboardData({
					data: this.apiKey,
					success() {
						uni.showToast({ title: '已复制', icon: 'success' })
					}
				})
			}
		}
	}
</script>

<style>
	.user-detail-page {
		padding: 20rpx;
		background: #0f172a;
		min-height: 100vh;
	}
	.section {
		background: #1e293b;
		border-radius: 16rpx;
		padding: 32rpx 24rpx;
		margin-bottom: 16rpx;
		border: 1rpx solid #334155;
	}
	.section-title {
		font-size: 36rpx;
		color: #f1f5f9;
		font-weight: 600;
		margin-bottom: 32rpx;
		text-align: center;
	}
	.form-item {
		margin-bottom: 30rpx;
	}
	.label {
		font-size: 28rpx;
		color: #94a3b8;
		margin-bottom: 10rpx;
		display: block;
	}
	.input, .picker-input {
		width: 100%;
		height: 80rpx;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 0 20rpx;
		color: #f1f5f9;
		font-size: 28rpx;
		box-sizing: border-box;
	}
	.input[disabled] {
		opacity: 0.6;
	}
	.picker-input {
		height: 80rpx;
		line-height: 80rpx;
		color: #f1f5f9;
	}
	.ip-hint {
		font-size: 24rpx;
		color: #94a3b8;
		margin-bottom: 15rpx;
		display: block;
	}

	.group-tags {
		display: flex;
		gap: 12rpx;
		flex-wrap: wrap;
		justify-content: center;
	}

	.group-tag {
		font-size: 26rpx;
		color: #6ee7b7;
		background: rgba(110, 231, 183, 0.1);
		border: 1rpx solid rgba(110, 231, 183, 0.3);
		border-radius: 8rpx;
		padding: 8rpx 24rpx;
	}

	.ip-input-row {
		display: flex;
		align-items: center;
		margin-bottom: 15rpx;
	}
	.add-ip-input {
		flex: 1;
		height: 80rpx;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 0 20rpx;
		color: #f1f5f9;
		font-size: 28rpx;
	}
	.add-ip-btn {
		width: 140rpx;
		height: 80rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		border: none;
		border-radius: 12rpx;
		font-size: 28rpx;
		font-weight: 600;
		margin-left: 16rpx;
	}
	.ip-list {
		margin-top: 20rpx;
	}
	.ip-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 20rpx 24rpx;
		margin-bottom: 10rpx;
	}
	.remove-ip {
		color: #f87171;
		font-size: 32rpx;
		padding: 0 10rpx;
	}
	.api-key-box {
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 20rpx;
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20rpx;
	}
	.api-key-text {
		flex: 1;
		font-size: 24rpx;
		color: #94a3b8;
		word-break: break-all;
	}
	.copy-btn {
		width: 120rpx;
		height: 60rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		border: none;
		border-radius: 8rpx;
		font-size: 24rpx;
		font-weight: 600;
	}
	.renew-btn {
		width: 100%;
		height: 76rpx;
		background: #334155;
		color: #e2e8f0;
		border: none;
		border-radius: 12rpx;
		font-size: 30rpx;
		font-weight: 600;
		line-height: 76rpx;
	}
	.btn-save {
		margin-top: 40rpx;
		padding: 0 20rpx;
	}
	.save-btn {
		width: 100%;
		height: 88rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		border: none;
		border-radius: 16rpx;
		font-size: 32rpx;
		font-weight: 600;
		line-height: 88rpx;
	}
</style>
