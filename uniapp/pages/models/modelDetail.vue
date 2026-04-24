<template>
	<view class="model-detail-page">
		<view class="section">
			<text class="section-title">{{ isEdit ? '编辑模型' : '添加模型' }}</text>
			<view class="form-item">
				<text class="label">模型名称</text>
				<input v-model="form.model_name" placeholder="模型名称" class="input" />
			</view>
			<view class="form-item">
				<text class="label">API URL</text>
				<input v-model="form.api_url" placeholder="https://api.openai.com/v1" class="input" />
			</view>
			<view class="form-item" v-if="isEdit">
				<text class="label">API Key</text>
				<input v-model="form.api_key" placeholder="留空则不修改" type="password" class="input" />
			</view>
		</view>
		<view class="btn-save">
			<button class="save-btn" @click="handleSave">保存</button>
		</view>
	</view>
</template>

<script>
	import { getModel, createModel, updateModel } from '@/api/admin_models.js'

	export default {
		data() {
			return {
				modelId: '',
				isEdit: false,
				form: {
					model_name: '',
					api_url: '',
					api_key: ''
				}
			}
		},
		onLoad(options) {
			if (options.id) {
				this.modelId = options.id
				this.isEdit = true
				this.fetchModel(options.id)
			}
		},
		methods: {
			async fetchModel(id) {
				try {
					const res = await getModel(id)
					Object.assign(this.form, {
						model_name: res.model_name || '',
						api_url: res.api_url || '',
						api_key: ''
					})
				} catch (err) {
					console.error('Failed to fetch model:', err)
				}
			},
			async handleSave() {
				if (!this.form.model_name || !this.form.api_url) {
					uni.showToast({ title: '请填模型名称和 API URL', icon: 'none' })
					return
				}
				try {
					const data = {
						model_name: this.form.model_name,
						api_url: this.form.api_url
					}
					if (this.form.api_key) {
						data.api_key = this.form.api_key
					}
					if (this.isEdit) {
						await updateModel(this.modelId, data)
					} else {
						await createModel(data)
					}
					uni.showToast({ title: '保存成功', icon: 'success' })
					uni.switchTab({ url: '/pages/models/models' })
				} catch (err) {
					console.error('Save failed:', err)
				}
			}
		}
	}
</script>

<style>
	.model-detail-page {
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
	.input {
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
