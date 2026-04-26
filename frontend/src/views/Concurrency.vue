<template>
  <div>
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="(model, url) in metrics" :key="url">
        <div class="stat-icon" :style="{ background: getIconColor(url) }">
          <el-icon><Cpu /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-title">{{ getModelName(url) }}</div>
          <div class="stat-row">
            <span class="stat-label">活跃</span>
            <span class="stat-value stat-active">{{ model.active }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">排队</span>
            <span class="stat-value" :class="{ 'stat-warning': model.waiting > 0 }">{{ model.waiting }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">拒绝</span>
            <span class="stat-value stat-rejected">{{ model.rejected }}</span>
          </div>
        </div>
      </div>
      <div v-if="!loading && Object.keys(metrics).length === 0" class="empty-state">
        <el-empty description="暂无模型数据" />
      </div>
    </div>

    <!-- 详细表格 -->
    <div class="detail-panel" v-loading="loading">
      <h3 class="panel-title">模型详情</h3>
      <table class="data-table" v-if="Object.keys(metrics).length > 0">
        <thead>
          <tr>
            <th>模型 URL</th>
            <th>活跃请求</th>
            <th>排队等待</th>
            <th>总请求数</th>
            <th>已拒绝</th>
            <th>超时</th>
            <th>运行时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(model, url) in metrics" :key="url">
            <td class="url-cell">
              <el-tooltip :content="url" placement="top">
                <span>{{ getModelName(url) }}</span>
              </el-tooltip>
            </td>
            <td>
              <el-tag type="success" size="small" v-if="model.active > 0">{{ model.active }}</el-tag>
              <span v-else class="text-muted">0</span>
            </td>
            <td>
              <el-tag type="warning" size="small" v-if="model.waiting > 0">{{ model.waiting }}</el-tag>
              <span v-else class="text-muted">0</span>
            </td>
            <td>{{ model.total_requests }}</td>
            <td>
              <el-tag type="danger" size="small" v-if="model.rejected > 0">{{ model.rejected }}</el-tag>
              <span v-else class="text-muted">0</span>
            </td>
            <td>
              <el-tag type="info" size="small" v-if="model.timeout > 0">{{ model.timeout }}</el-tag>
              <span v-else class="text-muted">0</span>
            </td>
            <td class="uptime">{{ formatUptime(model.uptime) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Cpu } from '@element-plus/icons-vue'
import request from '@/api/request'

const metrics = ref({})
const loading = ref(true)
let refreshTimer = null

const refreshInterval = 5000

async function loadMetrics() {
  try {
    const data = await request.get('/metrics')
    if (data && data.metrics) {
      metrics.value = data.metrics
    }
  } catch (error) {
    console.error('加载指标失败:', error)
  } finally {
    loading.value = false
  }
}

function getModelName(url) {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname
  } catch {
    return url.length > 30 ? url.substring(0, 30) + '...' : url
  }
}

function getModelColor(url) {
  let hash = 0
  for (let i = 0; i < url.length; i++) {
    hash = url.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1']
  return colors[Math.abs(hash) % colors.length]
}

function getIconColor(url) {
  const color = getModelColor(url)
  return `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`
}

function formatUptime(seconds) {
  if (!seconds || seconds < 0) return '-'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}小时${minutes}分`
  }
  return `${minutes}分钟`
}

onMounted(() => {
  loadMetrics()
  refreshTimer = setInterval(loadMetrics, refreshInterval)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, rgba(30, 23, 56, 0.8) 0%, rgba(20, 14, 40, 0.9) 100%);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #8b5cf6;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1edf7;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 12px;
  color: #8a7daa;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #f1edf7;
}

.stat-active {
  color: #10b981;
}

.stat-warning {
  color: #f59e0b;
}

.stat-rejected {
  color: #ef4444;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 40px;
}

.detail-panel {
  background: linear-gradient(135deg, rgba(30, 23, 56, 0.8) 0%, rgba(20, 14, 40, 0.9) 100%);
  border: 1px solid rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  padding: 24px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1edf7;
  margin: 0 0 20px;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table thead th {
  background: rgba(139, 92, 246, 0.08);
  color: #c4b5d0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.data-table tbody tr {
  transition: background 0.2s ease;
}

.data-table tbody tr:hover {
  background: rgba(139, 92, 246, 0.04);
}

.data-table tbody td {
  padding: 12px 16px;
  color: #f1edf7;
  font-size: 14px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.06);
}

.url-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.url-cell span {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #a899c0;
}

.text-muted {
  color: #524a75;
}

.uptime {
  color: #a899c0;
  font-size: 13px;
}
</style>
