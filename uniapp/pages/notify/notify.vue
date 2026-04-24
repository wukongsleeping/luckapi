<template>
	<view class="notify-page">
		<view class="page-header">
			<text class="page-title">消息通知</text>
			<view class="header-status" :class="{ connected: wsConnected }">
				<view class="status-dot"></view>
				<text>{{ wsConnected ? '已连接' : '未连接' }}</text>
			</view>
		</view>

		<view class="event-list">
			<view
				v-for="(item, index) in eventList"
				:key="item.event_id || index"
				class="event-card"
				:class="{ 'event-completed': item.event === 'qa_completed' }"
			>
				<view class="event-header">
					<view class="event-badge" :class="getBadgeClass(item)">
						<text v-if="item.event === 'qa_started'">连接</text>
						<text v-else-if="item.status === 'success'">完成</text>
						<text v-else-if="item.status === 'error'">失败</text>
						<text v-else-if="item.status === 'timeout'">超时</text>
						<text v-else>完成</text>
					</view>
					<text class="event-time">{{ formatTime(item.created_at) }}</text>
				</view>

				<text class="event-model">{{ item.model }}</text>

				<view v-if="item.event === 'qa_started'" class="event-detail">
					<text class="detail-text">IP: {{ item.client_ip || '未知' }}</text>
				</view>

				<view v-else class="event-detail">
					<text class="detail-text" v-if="item.client_ip">IP: {{ item.client_ip }} · </text>
					<text class="detail-text" v-if="item.latency_ms > 0">{{ item.latency_ms }}ms</text>
					<text class="detail-text" v-if="item.total_tokens > 0"> · {{ item.prompt_tokens }}+{{ item.completion_tokens }} tokens</text>
					<text class="detail-status" v-if="item.status && item.status !== 'success'">{{ item.status }}</text>
				</view>
			</view>
		</view>

		<view class="empty-tip" v-if="eventList.length === 0 && !loading">
			<text>暂无消息通知</text>
			<text class="empty-hint">代理请求到达时将实时显示</text>
		</view>

		<view class="empty-tip" v-if="loading">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script>
	const NOTIFY_INTERVAL = 60000  // 自动刷新间隔 (1分钟)

	let _refreshTimer = null
	let _uniListener = null

	export default {
		data() {
			return {
				eventList: [],
				wsConnected: false,
				loading: true,
			}
		},
		onLoad() {
			this.fetchRecent()
			this.bindListeners()
			this.startAutoRefresh()
		},
		onUnload() {
			this.unbindListeners()
			this.stopAutoRefresh()
		},
		onHide() {
			this.unbindListeners()
			this.stopAutoRefresh()
		},
		onShow() {
			this.fetchRecent()
			this.bindListeners()
			this.startAutoRefresh()
		},
		methods: {
			getBadgeClass(item) {
				if (item.event === 'qa_started') return 'badge-started'
				if (item.status === 'success') return 'badge-success'
				if (item.status === 'error' || item.status === 'timeout') return 'badge-error'
				return 'badge-success'
			},
			formatTime(ts) {
				if (!ts && ts !== 0) return ''
				const now = Date.now() / 1000
				const diff = now - ts
				if (diff < 60) return '刚刚'
				if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
				if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
				const d = new Date(ts * 1000)
				return (d.getMonth()+1) + '/' + d.getDate() + ' ' +
					String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0')
			},
			async fetchRecent() {
				const { getRecentNotifications } = await import('@/api/notify.js')
				try {
					const events = getRecentNotifications()
					const list = []
					for (const e of events) {
						const isStarted = e.event === 'qa_started' || e._event === 'qa_started'
						const isCompleted = e.event === 'qa_completed' || e._event === 'qa_completed'
						if (!isStarted && !isCompleted) continue

						const status = e.status || (isCompleted ? 'success' : 'connected')
						const promptT = e.prompt_tokens ?? e.tokens?.prompt ?? 0
						const completionT = e.completion_tokens ?? e.tokens?.completion ?? 0
						const totalT = e.total_tokens ?? e.tokens?.total ?? 0

						list.push({
							event: isStarted ? 'qa_started' : 'qa_completed',
							model: e.model || e.target_model || '未知模型',
							client_ip: e.client_ip || '',
							status: status,
							latency_ms: e.latency_ms || 0,
							prompt_tokens: Number(promptT) || 0,
							completion_tokens: Number(completionT) || 0,
							total_tokens: Number(totalT) || 0,
							event_id: e.event_id || '',
							record_id: e.record_id || '',
							start_time: e.start_time || 0,
							created_at: e.created_at || e.ts || 0,
						})
					}
					list.sort((a, b) => (b.created_at || 0) - (a.created_at || 0))
					this.eventList = list
					this.loading = false
				} catch (err) {
					console.error('Failed to fetch notifications:', err)
					this.loading = false
				}
			},
			onNotifyUpdate(data) {
				this.wsConnected = true
				if (!data || !data.items) return
				const { getRecentNotifications } = require('@/api/notify.js')
				const events = getRecentNotifications()
				const list = []
				for (const e of events) {
					const isStarted = e.event === 'qa_started' || e._event === 'qa_started'
					const isCompleted = e.event === 'qa_completed' || e._event === 'qa_completed'
					if (!isStarted && !isCompleted) continue
					const status = e.status || (isCompleted ? 'success' : 'connected')
					const promptT = e.prompt_tokens ?? e.tokens?.prompt ?? 0
					const completionT = e.completion_tokens ?? e.tokens?.completion ?? 0
					const totalT = e.total_tokens ?? e.tokens?.total ?? 0
					list.push({
						event: isStarted ? 'qa_started' : 'qa_completed',
						model: e.model || e.target_model || '未知模型',
						client_ip: e.client_ip || '',
						status: status,
						latency_ms: e.latency_ms || 0,
						prompt_tokens: Number(promptT) || 0,
						completion_tokens: Number(completionT) || 0,
						total_tokens: Number(totalT) || 0,
						event_id: e.event_id || '',
						record_id: e.record_id || '',
						start_time: e.start_time || 0,
						created_at: e.created_at || e.ts || 0,
					})
				}
				list.sort((a, b) => (b.created_at || 0) - (a.created_at || 0))
				this.eventList = list
			},
			bindListeners() {
				_uniListener = data => {
					this.onNotifyUpdate(data)
				}
				uni.$off('notify_update', _uniListener)
				uni.$on('notify_update', _uniListener)
			},
			unbindListeners() {
				if (_uniListener) {
					uni.$off('notify_update', _uniListener)
					_uniListener = null
				}
			},
			startAutoRefresh() {
				this.stopAutoRefresh()
				_refreshTimer = setInterval(() => {
					this.fetchRecent()
				}, NOTIFY_INTERVAL)
			},
			stopAutoRefresh() {
				clearInterval(_refreshTimer)
			}
		}
	}
</script>

<style>
	.notify-page {
		padding: 24rpx;
		background: #0f172a;
		min-height: 100vh;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24rpx;
		padding: 0 8rpx 20rpx;
		border-bottom: 1rpx solid #1e293b;
	}

	.page-title {
		font-size: 44rpx;
		font-weight: 700;
		color: #f1f5f9;
		letter-spacing: -0.5rpx;
	}

	.header-status {
		display: flex;
		align-items: center;
		gap: 8rpx;
		font-size: 24rpx;
		color: #64748b;
	}

	.header-status.connected {
		color: #10b981;
	}

	.status-dot {
		width: 12rpx;
		height: 12rpx;
		border-radius: 50%;
		background: #334155;
	}

	.header-status.connected .status-dot {
		background: #10b981;
		box-shadow: 0 0 8rpx rgba(16, 185, 129, 0.5);
	}

	.event-list {
		margin-top: 8rpx;
	}

	.event-card {
		background: #1e293b;
		border-radius: 16rpx;
		padding: 24rpx;
		margin-bottom: 16rpx;
		border: 1rpx solid #334155;
	}

	.event-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12rpx;
	}

	.event-badge {
		font-size: 22rpx;
		padding: 4rpx 16rpx;
		border-radius: 8rpx;
		font-weight: 600;
	}

	.badge-started {
		background: rgba(59, 130, 246, 0.15);
		color: #60a5fa;
	}

	.badge-success {
		background: rgba(16, 185, 129, 0.15);
		color: #34d399;
	}

	.badge-error {
		background: rgba(239, 68, 68, 0.15);
		color: #f87171;
	}

	.event-time {
		font-size: 22rpx;
		color: #64748b;
	}

	.event-model {
		font-size: 32rpx;
		font-weight: 600;
		color: #f1f5f9;
		display: block;
		margin-bottom: 12rpx;
	}

	.event-detail {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 4rpx;
	}

	.detail-text {
		font-size: 24rpx;
		color: #94a3b8;
	}

	.detail-status {
		font-size: 24rpx;
		color: #f87171;
		font-weight: 500;
	}

	.event-card.event-completed {
		border-left: 4rpx solid #10b981;
	}

	.empty-tip {
		text-align: center;
		color: #64748b;
		font-size: 28rpx;
		padding: 120rpx 0;
		line-height: 1.6;
	}

	.empty-hint {
		font-size: 24rpx;
		color: #475569;
		margin-top: 12rpx;
		display: block;
	}
</style>
