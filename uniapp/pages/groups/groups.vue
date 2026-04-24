<template>
	<view class="groups-page">
		<view class="page-header">
			<text class="page-title">分组管理</text>
			<text class="header-actions" @click="handleLogout">退出</text>
		</view>

		<view class="search-bar">
			<input
				v-model="keyword"
				placeholder="搜索分组..."
				class="search-input"
				@confirm="handleSearch"
			/>
			<button class="search-btn" @click="handleSearch">搜索</button>
		</view>

		<view class="group-list">
			<view
				v-for="(item, index) in groupList"
				:key="item.id"
				class="list-item"
			>
				<view class="group-info" @click="goToDetail(item)">
					<text class="group-name">{{ item.name }}</text>
					<text class="group-members">{{ item.member_ids ? item.member_ids.length : 0 }} 人</text>
				</view>
				<view class="group-actions">
					<text class="action-btn edit" @click.stop="goToDetail(item)">编辑</text>
					<text class="action-btn delete" @click.stop="confirmDelete(item)">删除</text>
				</view>
			</view>
		</view>
		<view class="empty-tip" v-if="groupList.length === 0">暂无分组数据</view>

		<button class="fab" @click="showAddDialog = true">+</button>

		<view class="dialog-mask" v-if="showAddDialog" @click="showAddDialog = false">
			<view class="dialog" @click.stop>
				<text class="dialog-title">添加分组</text>
				<input v-model="groupName" placeholder="分组名称" class="dialog-input" />
				<input v-model="groupModelName" placeholder="模型名称（可选）" class="dialog-input" />
				<input v-model="groupModelUrl" placeholder="模型 URL（可选）" class="dialog-input" />
				<input v-model="groupApiKey" placeholder="API Key（可选）" type="password" class="dialog-input" />
				<button class="dialog-btn" @click="handleAddGroup">确定</button>
				<button class="dialog-btn cancel" @click="showAddDialog = false">取消</button>
			</view>
		</view>
	</view>
</template>

<script>
import { createGroup, deleteGroup, getGroups } from '@/api/groups.js'
import { authStore } from '@/store/auth.js'

	export default {
		data() {
			return {
				groupList: [],
				keyword: '',
				showAddDialog: false,
				groupName: '',
				groupModelName: '',
				groupModelUrl: '',
				groupApiKey: ''
			}
		},
		onLoad() {
			this.fetchGroups()
		},
		onShow() {
			if (this.groupList.length === 0) {
				this.fetchGroups()
			}
		},
		methods: {
			async fetchGroups() {
				try {
					const res = await getGroups()
					this.groupList = res.items || []
				} catch (err) {
					console.error('Failed to fetch groups:', err)
				}
			},
			async handleSearch() {
				if (!this.keyword.trim()) {
					return this.fetchGroups()
				}
				try {
					const res = await getGroups({ search: this.keyword })
					this.groupList = res.items || []
				} catch (err) {
					console.error('Search failed:', err)
				}
			},
			goToDetail(item) {
				uni.navigateTo({
					url: `/pages/groupDetail/groupDetail?id=${item.id}`
				})
			},
			async confirmDelete(item) {
				uni.showModal({
					title: '确认删除',
					content: `确定要删除分组「${item.name}」吗？`,
					success: async (res) => {
						if (res.confirm) {
							try {
								await deleteGroup(item.id)
								uni.showToast({ title: '删除成功', icon: 'success' })
								this.fetchGroups()
							} catch (err) {
								console.error('Delete group failed:', err)
							}
						}
					}
				})
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
			async handleAddGroup() {
				if (!this.groupName.trim()) {
					uni.showToast({ title: '请输入分组名称', icon: 'none' })
					return
				}
				this.showAddDialog = false
				try {
					await createGroup({
						name: this.groupName,
						model_name: this.groupModelName || null,
						model_url: this.groupModelUrl || null,
						model_api_key: this.groupApiKey || null
					})
					uni.showToast({ title: '添加成功', icon: 'success' })
					this.groupName = ''
					this.groupModelName = ''
					this.groupModelUrl = ''
					this.groupApiKey = ''
					this.fetchGroups()
				} catch (err) {
					console.error('Add group failed:', err)
				}
			}
		}
	}
</script>

<style>
	.groups-page {
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

	.group-list {
		margin-bottom: 20rpx;
	}

	.group-info {
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.group-name {
		font-size: 32rpx;
		color: #f1f5f9;
		font-weight: 600;
		display: block;
	}

	.group-members {
		font-size: 24rpx;
		color: #94a3b8;
		margin-top: 8rpx;
		display: block;
	}

	.group-actions {
		display: flex;
		gap: 16rpx;
		margin-left: 24rpx;
	}
</style>
