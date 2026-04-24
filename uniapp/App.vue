<script>
    import { connectNotify, disconnectNotify } from '@/api/notify.js'

    const authStore = require('./store/auth.js').authStore

    export default {
        onLaunch() {
            console.log('App Launch')
            try {
                this.initNotify()
            } catch (e) {
                console.error('App Launch Error:', e)
            }
        },
        onShow() {
            if (authStore.isLoggedIn && !this._notifyConnected) {
                this.initNotify()
            }
        },
        onHide() {
            console.log('App Hide')
        },
        methods: {
            initNotify() {
                if (!authStore.isLoggedIn) return
                this._notifyConnected = true
                connectNotify((type, payload) => {
                    this.handleNotify(type, payload)
                })
            },
            handleNotify(type, payload) {
                try {
                    const store = require('./store/notify.js').notifyStore
                    store.onRealtime(type, payload)
                } catch (e) {
                    console.error('Notify store update failed:', e)
                }
            },
        },
    }
</script>

<style>
	page {
		background-color: #0f172a;
		color: #f1f5f9;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		font-size: 28rpx;
		line-height: 1.6;
		font-weight: 400;
		-webkit-font-smoothing: antialiased;
	}

	view, text, input, button {
		box-sizing: border-box;
	}

	.search-bar {
		display: flex;
		gap: 16rpx;
		margin-bottom: 32rpx;
		align-items: center;
		padding: 0 24rpx;
		background: #1e293b;
		border-radius: 16rpx;
		padding: 16rpx;
	}

	.search-input {
		flex: 1;
		height: 72rpx;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 0 20rpx;
		color: #f1f5f9;
		font-size: 28rpx;
	}

	.search-input::placeholder {
		color: #64748b;
	}

	.search-btn {
		width: 120rpx;
		height: 72rpx;
		background: #1e293b;
		color: #94a3b8;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		font-size: 26rpx;
	}

	.list-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 32rpx 24rpx;
		background: #1e293b;
		border-radius: 16rpx;
		margin-bottom: 16rpx;
		border: 1rpx solid #334155;
		transition: all 200ms ease;
	}

	.list-item:active {
		background: #253043;
		transform: scale(0.98);
	}

	.action-btn {
		font-size: 24rpx;
		padding: 8rpx 16rpx;
		border-radius: 8rpx;
		font-weight: 500;
		transition: opacity 150ms ease;
	}

	.action-btn:active {
		opacity: 0.7;
	}

	.action-btn.edit {
		color: #34d399;
	}

	.action-btn.delete {
		color: #f87171;
	}

	.fab {
		position: fixed;
		right: 32rpx;
		bottom: 112rpx;
		width: 96rpx;
		height: 96rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		font-size: 56rpx;
		border: none;
		border-radius: 50%;
		line-height: 96rpx;
		text-align: center;
		box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.3);
		transition: all 200ms ease;
		z-index: 100;
	}

	.fab:active {
		transform: scale(0.95);
		box-shadow: 0 4rpx 16rpx rgba(16, 185, 129, 0.4);
	}

	.dialog-mask {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 999;
		backdrop-filter: blur(4rpx);
	}

	.dialog {
		width: 88%;
		max-width: 680rpx;
		background: #1e293b;
		border: 1rpx solid #334155;
		border-radius: 24rpx;
		padding: 40rpx 32rpx 32rpx;
		box-shadow: 0 24rpx 48rpx rgba(0, 0, 0, 0.4);
	}

	.dialog-title {
		font-size: 36rpx;
		color: #f1f5f9;
		font-weight: 600;
		margin-bottom: 32rpx;
		text-align: center;
	}

	.dialog-input {
		width: 100%;
		height: 72rpx;
		background: #0f172a;
		border: 1rpx solid #334155;
		border-radius: 12rpx;
		padding: 0 20rpx;
		color: #f1f5f9;
		font-size: 28rpx;
		margin-bottom: 20rpx;
	}

	.dialog-input::placeholder {
		color: #64748b;
	}

	.dialog-btn {
		width: 100%;
		height: 76rpx;
		background: linear-gradient(135deg, #10b981, #059669);
		color: #fff;
		border: none;
		border-radius: 12rpx;
		font-size: 30rpx;
		font-weight: 600;
		margin-top: 20rpx;
	}

	.dialog-btn:active {
		opacity: 0.9;
	}

	.dialog-btn.cancel {
		background: #334155;
		color: #e2e8f0;
	}

	.empty-tip {
		text-align: center;
		color: #64748b;
		font-size: 28rpx;
		padding: 80rpx 0;
		line-height: 1.6;
	}

	.logout-btn {
		font-size: 24rpx;
		color: #f87171;
		padding: 12rpx 20rpx;
		white-space: nowrap;
		border-radius: 8rpx;
		transition: background 150ms ease;
	}

	.logout-btn:active {
		background: rgba(248, 113, 113, 0.1);
	}
</style>
