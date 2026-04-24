<template>
	<view class="models-page">
		<view class="page-header">
			<text class="page-title">模型管理</text>
			<text class="header-actions" @click="handleLogout">退出</text>
		</view>

		<view class="search-bar">
			<input
				v-model="keyword"
				placeholder="搜索模型..."
				class="search-input"
				@confirm="handleSearch"
			/>
			<button class="search-btn" @click="handleSearch">搜索</button>
		</view>

		<view class="model-list">
			<view
				v-for="(item, index) in modelList"
				:key="item.id"
				class="list-item"
			>
				<view class="model-info" @click="goToDetail(item)">
					<text class="model-name">{{ item.model_name }}</text>
					<text class="model-url">{{ item.api_url }}</text>
				</view>
				<view class="model-actions">
					<text class="action-btn edit" @click.stop="goToDetail(item)">编辑</text>
					<text class="action-btn delete" @click.stop="handleDelete(item)">删除</text>
				</view>
			</view>
		</view>
		<view class="empty-tip" v-if="modelList.length === 0">暂无模型数据</view>

		<button class="fab" @click="showAddDialog = true">+</button>

		<view class="dialog-mask" v-if="showAddDialog" @click="showAddDialog = false">
			<view class="dialog" @click.stop>
				<text class="dialog-title">添加模型</text>
				<input v-model="newModel.model_name" placeholder="模型名称" class="dialog-input" />
				<input v-model="newModel.api_url" placeholder="API URL" class="dialog-input" />
				<input v-model="newModel.api_key" placeholder="API Key" type="password" class="dialog-input" />
				<button class="dialog-btn" @click="handleAddModel">确定</button>
				<button class="dialog-btn cancel" @click="showAddDialog = false">取消</button>
			</view>
		</view>
	</view>
</template>

<script>
import { getModels, createModel, deleteModel } from '@/api/admin_models.js'
import { authStore } from '@/store/auth.js'

	export default {
		data() {
			return {
				modelList: [],
				keyword: '',
				showAddDialog: false,
				newModel: {
					model_name: '',
					api_url: '',
					api_key: ''
				}
			}
		},
		onLoad() {
			this.fetchModels()
		},
		onShow() {
			if (this.modelList.length === 0) {
				this.fetchModels()
			}
		},
		methods: {
			async fetchModels() {
				try {
					const res = await getModels()
					this.modelList = res.items || []
				} catch (err) {
					console.error('Failed to fetch models:', err)
				}
			},
			async handleSearch() {
				if (!this.keyword.trim()) {
					return this.fetchModels()
				}
				try {
					const res = await getModels({ search: this.keyword })
					this.modelList = res.items || []
				} catch (err) {
					console.error('Search failed:', err)
				}
			},
			goToDetail(item) {
				uni.navigateTo({
					url: `/pages/models/modelDetail?id=${item.id}`
				})
			},
			async handleAddModel() {
				if (!this.newModel.model_name || !this.newModel.api_url || !this.newModel.api_key) {
					uni.showToast({ title: '请填写完整信息', icon: 'none' })
					return
				}
				this.showAddDialog = false
				try {
					await createModel({
						model_name: this.newModel.model_name,
						api_url: this.newModel.api_url,
						api_key: this.newModel.api_key
					})
					uni.showToast({ title: '添加成功', icon: 'success' })
					this.newModel = { model_name: '', api_url: '', api_key: '' }
					this.fetchModels()
				} catch (err) {
					console.error('Add model failed:', err)
				}
			},
			async handleLogout() {
				uni.showModal({
					title: '提示',
					content: '确定退出登录吗？',
					success: (res) => {
						if (res.confirm) {
							authStore.clearSession()
							uni.reLaunch({ url: '/pages/login/login' })
						}
					}
				})
			},
			handleDelete(item) {
				uni.showModal({
					title: '确认删除',
					content: `确定删除模型 ${item.model_name} 吗？`,
					success: async (res) => {
						if (res.confirm) {
							try {
								await deleteModel(item.id)
								uni.showToast({ title: '删除成功', icon: 'success' })
								this.fetchModels()
							} catch (err) {
								console.error('Delete failed:', err)
							}
						}
					}
				})
			}
		}
	}
</script>

<style>
	.models-page {
		padding: 24rpx;
		background: #0f172a;
		min-height: 100vh;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 32rpx;
		padding: 0 8rpx;
	}

	.page-title {
		font-size: 44rpx;
		font-weight: 700;
		color: #f1f5f9;
		letter-spacing: -0.5rpx;
	}

	.header-actions {
		font-size: 26rpx;
		color: #94a3b8;
		padding: 12rpx 20rpx;
		border-radius: 8rpx;
	}

	.header-actions:active {
		background: rgba(148, 163, 184, 0.1);
	}

	.model-list {
		margin-bottom: 20rpx;
	}

	.model-info {
		flex: 1;
	}

	.model-name {
		font-size: 32rpx;
		color: #f1f5f9;
		font-weight: 600;
		display: block;
	}

	.model-url {
		font-size: 24rpx;
		color: #94a3b8;
		margin-top: 8rpx;
		display: block;
	}

	.model-actions {
		display: flex;
		gap: 16rpx;
		margin-left: 24rpx;
	}
</style>
