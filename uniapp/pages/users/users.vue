<template>
	<view class="users-page">
		<view class="page-header">
			<text class="page-title">用户管理</text>
			<text class="header-actions" @click="handleLogout">退出</text>
		</view>

		<view class="search-bar">
			<input
				v-model="keyword"
				placeholder="搜索用户..."
				class="search-input"
				@confirm="handleSearch"
			/>
			<button class="search-btn" @click="handleSearch">搜索</button>
		</view>

		<view class="user-list">
			<view
				v-for="(item, index) in userList"
				:key="item.id"
				class="list-item"
			>
			<view class="user-info" @click="goToDetail(item)">
				<text class="user-name">{{ item.display_name || item.username }}</text>
				<text class="user-username">@{{ item.username }}</text>
				<view class="group-tags" v-if="item.group_names && item.group_names.length > 0">
					<text class="group-tag" v-for="(name, idx) in item.group_names" :key="idx">{{ name }}</text>
				</view>
			</view>
				<view class="user-actions">
					<text class="action-btn edit" @click.stop="goToDetail(item)">编辑</text>
					<text class="action-btn delete" @click.stop="handleDelete(item)">删除</text>
				</view>
			</view>
		</view>
		<view class="empty-tip" v-if="userList.length === 0">暂无用户数据</view>

		<button class="fab" @click="showAddDialog = true">+</button>

		<view class="dialog-mask" v-if="showAddDialog" @click="showAddDialog = false">
			<view class="dialog" @click.stop>
				<text class="dialog-title">添加用户</text>
				<input v-model="newUser.username" placeholder="用户名" class="dialog-input" />
				<input v-model="newUser.display_name" placeholder="显示名称（可选）" class="dialog-input" />
				<input v-model="newUser.password" placeholder="密码" type="password" class="dialog-input" />
				<picker :value="roleIndex" :range="roleOptions" @change="onRoleChange">
					<view class="dialog-input">
						<text>{{ roleOptions[roleIndex] === 'user' ? '普通用户' : '管理员' }}</text>
					</view>
				</picker>
				<button class="dialog-btn" @click="handleAddUser">确定</button>
				<button class="dialog-btn cancel" @click="showAddDialog = false">取消</button>
			</view>
		</view>
	</view>
</template>

<script>
	import { getUsers, createUser, deleteUser } from '@/api/users.js'
	import { authStore } from '@/store/auth.js'

	export default {
		data() {
			return {
				userList: [],
				keyword: '',
				showAddDialog: false,
				newUser: {
					username: '',
					display_name: '',
					password: ''
				},
				roleIndex: 0,
				roleOptions: ['user', 'admin']
			}
		},
		onLoad() {
			this.fetchUsers()
		},
		onShow() {
			this.fetchUsers()
		},
		methods: {
		async fetchUsers() {
			try {
				const res = await getUsers()
				console.log('[DEBUG] users response:', JSON.stringify(res, null, 2))
				const items = res.items || []
				for (const u of items) {
					console.log(`[DEBUG] user ${u.id} (${u.username}): group_names=`, u.group_names)
				}
				this.userList = items
			} catch (err) {
				console.error('Failed to fetch users:', err)
			}
		},
			async handleSearch() {
				if (!this.keyword.trim()) {
					return this.fetchUsers()
				}
				try {
					const res = await getUsers({ search: this.keyword })
					this.userList = res.items || []
				} catch (err) {
					console.error('Search failed:', err)
				}
			},
			onRoleChange(e) {
				this.roleIndex = e.detail.value
			},
			goToDetail(item) {
				uni.navigateTo({
					url: `/pages/users/userDetail?id=${item.id}`
				})
			},
			async handleAddUser() {
				if (!this.newUser.username || !this.newUser.password) {
					uni.showToast({ title: '请填写用户名和密码', icon: 'none' })
					return
				}
				if (this.newUser.username.length < 3) {
					uni.showToast({ title: '用户名至少3个字符', icon: 'none' })
					return
				}
				if (this.newUser.password.length < 6) {
					uni.showToast({ title: '密码至少6个字符', icon: 'none' })
					return
				}
				this.showAddDialog = false
				try {
					const payload = {
						username: this.newUser.username,
						display_name: this.newUser.display_name,
						password: this.newUser.password,
						role: this.roleOptions[this.roleIndex]
					}
					await createUser(payload)
					uni.showToast({ title: '添加成功', icon: 'success' })
					this.newUser = { username: '', display_name: '', password: '' }
					this.roleIndex = 0
					this.fetchUsers()
				} catch (err) {
					console.error('Add user failed:', err)
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
					content: `确定删除用户 ${item.username} 吗？`,
					success: async (res) => {
						if (res.confirm) {
							try {
								await deleteUser(item.id)
								uni.showToast({ title: '删除成功', icon: 'success' })
								this.fetchUsers()
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
	.users-page {
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

	.user-list {
		margin-bottom: 20rpx;
	}

	.user-info {
		flex: 1;
	}

	.user-name {
		font-size: 32rpx;
		color: #f1f5f9;
		font-weight: 600;
		display: block;
	}

	.user-username {
		font-size: 24rpx;
		color: #94a3b8;
		margin-top: 8rpx;
		display: block;
	}

	.group-tags {
		display: flex;
		gap: 12rpx;
		margin-top: 12rpx;
		flex-wrap: wrap;
	}

	.group-tag {
		font-size: 22rpx;
		color: #6ee7b7;
		background: rgba(110, 231, 183, 0.1);
		border: 1rpx solid rgba(110, 231, 183, 0.3);
		border-radius: 8rpx;
		padding: 4rpx 16rpx;
	}

	.user-actions {
		display: flex;
		gap: 16rpx;
		margin-left: 24rpx;
	}
</style>
