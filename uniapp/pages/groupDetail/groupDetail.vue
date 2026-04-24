<template>
	<view class="group-detail-page">
		<view class="section" v-if="group">
			<text class="section-title">基本信息</text>
			<view class="form-item">
				<text class="label">分组名称</text>
				<input v-model="form.name" placeholder="分组名称" class="input" />
			</view>
			<view class="form-item">
				<text class="label">模型名称（可选）</text>
				<input v-model="form.model_name" placeholder="模型名称" class="input" />
			</view>
			<view class="form-item">
				<text class="label">模型 URL（可选）</text>
				<input v-model="form.model_url" placeholder="API 地址" class="input" />
			</view>
			<view class="form-item">
				<text class="label">API Key（可选）</text>
				<input v-model="form.model_api_key" placeholder="API Key" type="text" class="input" />
			</view>
		</view>

		<view class="section" v-if="group && (group.model_name || group.model_url || modelApiKey)">
			<text class="section-title">模型配置</text>
			<view class="form-item" v-if="group.model_name">
				<text class="label">模型名称</text>
				<text class="config-value">{{ group.model_name }}</text>
			</view>
			<view class="form-item" v-if="group.model_url">
				<text class="label">模型 URL</text>
				<view class="url-row">
					<text class="config-value url-text">{{ group.model_url }}</text>
					<view class="copy-icon" @click="copyUrl" v-if="group.model_url">📋</view>
				</view>
			</view>
			<view class="form-item" v-if="modelApiKey || group.model_api_key">
				<text class="label">API Key</text>
				<view class="api-key-box">
					<text class="api-key-text">{{ modelApiKey }}</text>
					<button class="copy-btn" @click="copyApikey">复制</button>
				</view>
				<text class="hint-text" v-if="!group.model_api_key">未配置 API Key</text>
			</view>
		</view>

		<view class="section" v-if="group && group.member_ids && group.member_ids.length > 0">
			<text class="section-title">组成员 ({{ group.member_ids.length }})</text>
			<view class="member-list">
				<view class="member-item" v-for="uid in group.member_ids" :key="uid">
					<text class="member-name">{{ userNames[uid] || '用户' + uid }}</text>
					<text class="remove-member" @click="removeMember(uid)">✕</text>
				</view>
			</view>
		</view>

		<view class="section" v-if="userSelectOptions.length > 0">
			<text class="section-title">添加成员</text>
			<picker :value="userSelectIndex" :range="userSelectOptions" range-key="label" @change="onUserSelect">
				<view class="picker-input">{{ getUserSelectLabel() }}</view>
			</picker>
			<button class="add-member-btn" @click="addMember">添加</button>
		</view>

		<view class="btn-save">
			<button class="save-btn" @click="handleSave">保存</button>
			<button class="delete-btn" @click="handleDelete" v-if="group">删除分组</button>
		</view>
	</view>
</template>

<script>
	import { getGroup, createGroup, updateGroup, deleteGroup, assignUserToGroup, removeUserFromGroup } from '@/api/groups.js'
	import { getUsers } from '@/api/users.js'

	export default {
		data() {
			return {
				group: null,
				groupId: '',
				isEdit: false,
				form: {
					name: ''
				},
				modelApiKey: '',
				userNames: {},
				userOptions: [],
				selectedUser: null,
				userSelectIndex: -1
			}
		},
		computed: {
			userSelectOptions() {
				return this.userOptions
			}
		},
		onLoad(options) {
			if (options.id) {
				this.groupId = options.id
				this.isEdit = true
				this.fetchGroup(options.id)
				this.fetchUserList()
			}
		},
		methods: {
			getUserSelectLabel() {
				if (!this.userOptions || this.userSelectIndex < 0 || this.userSelectIndex >= this.userOptions.length) {
					return '请选择用户'
				}
				return this.userOptions[this.userSelectIndex].label
			},
			async fetchGroup(id) {
				try {
					const res = await getGroup(id)
					this.group = res
					Object.assign(this.form, {
						name: res.name || '',
						model_name: res.model_name || '',
						model_url: res.model_url || '',
						model_api_key: res.model_api_key || ''
					})
					this.modelApiKey = res.model_api_key || ''
					this.$nextTick(() => {
						this.buildUserOptions()
					})
				} catch (err) {
					console.error('Failed to fetch group:', err)
				}
			},
			async fetchUserList() {
				try {
					const res = await getUsers()
					const users = res.items || []
					this.userNames = {}
					users.forEach(u => {
						this.userNames[u.id] = u.display_name || u.username
					})
					this.buildUserOptions()
				} catch (err) {
					console.error('Failed to fetch user list:', err)
				}
			},
			buildUserOptions() {
				if (!this.group || !this.group.member_ids) {
					this.userOptions = []
					return
				}
				const excludeIds = new Set(this.group.member_ids)
				this.userOptions = Object.keys(this.userNames)
					.filter(uid => !excludeIds.has(parseInt(uid)))
					.map(uid => ({
						value: uid,
						label: this.userNames[uid]
					}))
				if (this.userSelectIndex >= this.userOptions.length) {
					this.userSelectIndex = -1
					this.selectedUser = null
				}
			},
			onUserSelect(e) {
				this.userSelectIndex = e.detail.value
				this.selectedUser = this.userOptions[this.userSelectIndex]
			},
			async addMember() {
				if (!this.selectedUser) {
					uni.showToast({ title: '请选择用户', icon: 'none' })
					return
				}
				try {
					await assignUserToGroup(this.groupId, parseInt(this.selectedUser.value))
					uni.showToast({ title: '添加成功', icon: 'success' })
					this.userSelectIndex = -1
					this.selectedUser = null
					await this.fetchGroup(this.groupId)
					await this.fetchUserList()
					this.buildUserOptions()
				} catch (err) {
					console.error('Add member failed:', err)
				}
			},
			async removeMember(uid) {
				uni.showModal({
					title: '确认移除',
					content: '确定移除此成员？',
					success: async (res) => {
						if (res.confirm) {
							try {
								await removeUserFromGroup(this.groupId, uid)
								uni.showToast({ title: '已移除', icon: 'success' })
								await this.fetchGroup(this.groupId)
								await this.fetchUserList()
								this.buildUserOptions()
							} catch (err) {
								console.error('Remove member failed:', err)
							}
						}
					}
				})
			},
			async handleSave() {
				if (!this.form.name) {
					uni.showToast({ title: '请输入分组名称', icon: 'none' })
					return
				}
				try {
					await updateGroup(this.groupId, {
						name: this.form.name,
						model_name: this.form.model_name || null,
						model_url: this.form.model_url || null,
						model_api_key: this.form.model_api_key || null
					})
					uni.showToast({ title: '保存成功', icon: 'success' })
					this.fetchGroup(this.groupId)
				} catch (err) {
					console.error('Save failed:', err)
				}
			},
			async handleDelete() {
				uni.showModal({
					title: '确认删除',
					content: '确定删除此分组？',
					success: async (res) => {
						if (res.confirm) {
							try {
								await deleteGroup(this.groupId)
								uni.showToast({ title: '删除成功', icon: 'success' })
								uni.switchTab({ url: '/pages/groups/groups' })
							} catch (err) {
								console.error('Delete failed:', err)
							}
						}
					}
				})
			},
			copyApikey() {
				if (!this.modelApiKey) {
					uni.showToast({ title: '无 API Key', icon: 'none' })
					return
				}
				uni.setClipboardData({
					data: this.modelApiKey,
					success() {
						uni.showToast({ title: '已复制', icon: 'success' })
					}
				})
			},
			copyUrl() {
				if (!this.group || !this.group.model_url) return
				uni.setClipboardData({
					data: this.group.model_url,
					success() {
						uni.showToast({ title: '已复制', icon: 'success' })
					}
				})
			}
		}
	}
</script>

<style>
	.group-detail-page {
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
	.form-item .input {
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
	.config-value {
		font-size: 28rpx;
		color: #e2e8f0;
		word-break: break-all;
	}
	.url-row {
		display: flex;
		align-items: center;
		gap: 16rpx;
	}
	.url-text {
		flex: 1;
	}
	.copy-icon {
		font-size: 28rpx;
		padding: 8rpx;
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
	.hint-text {
		font-size: 24rpx;
		color: #64748b;
		text-align: center;
		display: block;
		margin-top: 10rpx;
	}
	.label {
		font-size: 28rpx;
		color: #94a3b8;
		margin-bottom: 10rpx;
		display: block;
	}
	.add-member-btn {
		margin-top: 20rpx;
		height: 76rpx;
		line-height: 76rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		border: none;
		border-radius: 12rpx;
		font-size: 30rpx;
		font-weight: 600;
	}
	.picker-input {
		height: 80rpx;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 0 20rpx;
		color: #f1f5f9;
		font-size: 28rpx;
	}
	.member-list {
		margin-bottom: 20rpx;
	}
	.member-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 20rpx 24rpx;
		margin-bottom: 10rpx;
	}
	.member-name {
		font-size: 28rpx;
		color: #f1f5f9;
	}
	.remove-member {
		color: #f87171;
		font-size: 32rpx;
		padding: 0 10rpx;
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
		margin-bottom: 20rpx;
	}
	.delete-btn {
		width: 100%;
		height: 88rpx;
		background: #1e293b;
		color: #f87171;
		border: 1rpx solid #f87171;
		border-radius: 16rpx;
		font-size: 32rpx;
		font-weight: 600;
		line-height: 88rpx;
	}
</style>
