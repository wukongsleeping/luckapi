<template>
  <div>
    <!-- 统计行 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value" :style="{ color: pagination.total > 0 ? '#06d6a0' : '#64748b' }">{{ pagination.total }}</div>
        <div class="stat-label">总记录数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #06d6a0">{{ totalTokens.toLocaleString() }}</div>
        <div class="stat-label">总 Token 数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #60a5fa">{{ avgLatency.toFixed(0) }}ms</div>
        <div class="stat-label">平均延迟</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #06d6a0">{{ successRate }}%</div>
        <div class="stat-label">成功率</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-row">
        <el-select v-model="filterUserId" placeholder="按用户筛选" clearable class="filter-select" style="width: 180px">
          <el-option v-for="u in allUsers" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="按状态筛选" clearable class="filter-select" style="width: 140px">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="error" />
          <el-option label="超时" value="timeout" />
        </el-select>
        <el-input v-model="filterModel" placeholder="按模型名筛选" clearable class="filter-input" style="width: 220px" />
        <el-date-picker
          v-model="filterDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始"
          end-placeholder="结束"
          value-format="YYYY-MM-DD"
          class="filter-dates"
          style="width: 260px"
        />
        <el-button @click="loadRecords" class="btn-search">查询</el-button>
        <el-button @click="resetFilter" class="btn-reset">重置</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-panel" v-loading="loading">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 60px">ID</th>
            <th style="width: 130px">用户</th>
            <th style="width: 150px">模型</th>
            <th style="width: 50px">方法</th>
            <th style="width: 80px">状态</th>
            <th style="width: 80px">上游状态</th>
            <th style="width: 90px">Prompt Tokens</th>
            <th style="width: 90px">Completion Tokens</th>
            <th style="width: 90px">总 Tokens</th>
            <th style="width: 90px">延迟</th>
            <th style="width: 160px">时间</th>
            <th style="width: 130px; text-align: right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(rec, idx) in records" :key="rec.id" class="table-row" :style="{ animationDelay: idx * 0.03 + 's' }">
            <td><span class="cell-id">{{ rec.id }}</span></td>
            <td>
              <span class="cell-user" @click="showUserDetail(rec)" style="cursor: pointer">{{ userName(rec.user_id) }}</span>
            </td>
            <td>
              <span class="badge-model">{{ rec.target_model }}</span>
            </td>
            <td><span class="method-badge" :class="rec.method.toLowerCase()">{{ rec.method }}</span></td>
            <td>
              <span class="badge-status" :class="'status-' + rec.status">
                <span class="status-dot" />
                {{ statusLabel(rec.status) }}
              </span>
            </td>
            <td>
              <span class="upstream-status" :class="rec.upstream_status >= 200 && rec.upstream_status < 300 ? 'us-ok' : 'us-err'">
                {{ rec.upstream_status || '-' }}
              </span>
            </td>
            <td class="cell-number">{{ fmtNum(rec.request_tokens) }}</td>
            <td class="cell-number">{{ fmtNum(rec.response_tokens) }}</td>
            <td class="cell-number" style="color: #06d6a0; font-weight: 600">{{ fmtNum(rec.total_tokens) }}</td>
            <td class="cell-number" style="color: {{ rec.latency_ms > 1000 ? '#f59e0b' : '#94a3b8' }}">{{ rec.latency_ms }}ms</td>
            <td><span class="cell-date">{{ formatTime(rec.created_at) }}</span></td>
            <td class="cell-actions">
              <el-button @click="viewDetail(rec)" class="btn-cell" size="small">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button @click="confirmDelete(rec)" class="btn-cell btn-danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </td>
          </tr>
          <tr v-if="!loading && records.length === 0">
            <td colspan="12" class="empty-row">暂无对话记录</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row pagination-center" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next, sizes"
          :page-sizes="[20, 50, 100]"
          @current-change="loadRecords"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="对话详情" width="900px" class="glass-dialog" top="5vh">
      <div class="detail-section" v-if="detailRecord">
        <div class="detail-meta">
          <div class="meta-grid">
            <div class="meta-item"><span class="meta-label">用户ID</span><span class="meta-value">{{ detailRecord.user_id }}</span></div>
            <div class="meta-item"><span class="meta-label">模型</span><span class="meta-value">{{ detailRecord.target_model }}</span></div>
            <div class="meta-item"><span class="meta-label">状态</span><span class="meta-value">{{ statusLabel(detailRecord.status) }}</span></div>
            <div class="meta-item"><span class="meta-label">延迟</span><span class="meta-value">{{ detailRecord.latency_ms }}ms</span></div>
            <div class="meta-item"><span class="meta-label">Token 总计</span><span class="meta-value">{{ fmtNum(detailRecord.total_tokens) }}</span></div>
            <div class="meta-item"><span class="meta-label">时间</span><span class="meta-value">{{ formatFullTime(detailRecord.created_at) }}</span></div>
          </div>
        </div>
        <div class="detail-body">
          <div class="detail-block">
            <div class="block-header">
              <span>请求内容</span>
              <el-button @click="copyText(detailRecord.request_body)" size="small" class="btn-copy-inline">复制</el-button>
            </div>
            <pre class="json-block">{{ formatJson(detailRecord.request_body) }}</pre>
          </div>
          <div class="detail-block" v-if="detailRecord.response_body">
            <div class="block-header">
              <span>响应内容</span>
              <el-button @click="copyText(detailRecord.response_body)" size="small" class="btn-copy-inline">复制</el-button>
            </div>
            <pre class="json-block">{{ formatJson(detailRecord.response_body) }}</pre>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Delete } from '@element-plus/icons-vue'
import { getQaRecords, getQaRecord, deleteQaRecord, exportQaRecords } from '@/api/qa'
import { getUsers } from '@/api/user'

const records = ref([])
const loading = ref(false)
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const filterUserId = ref('')
const filterStatus = ref('')
const filterModel = ref('')
const filterDateRange = ref(null)
const allUsers = ref([])

// Detail dialog
const showDetailDialog = ref(false)
const detailRecord = ref(null)

// Stats
const totalTokens = computed(() => records.value.reduce((sum, r) => sum + (r.total_tokens || 0), 0))
const avgLatency = computed(() => records.value.length ? records.value.reduce((s, r) => s + r.latency_ms, 0) / records.value.length : 0)
const successCount = computed(() => records.value.filter(r => r.status === 'success').length)
const successRate = computed(() => records.value.length ? (successCount.value / records.value.length * 100).toFixed(1) : 0)

const userName = (userId) => {
  const u = allUsers.value.find(user => user.id === userId)
  return u ? u.username : `#${userId}`
}

function statusLabel(s) {
  return { success: '成功', error: '失败', timeout: '超时' }[s] || s
}

function fmtNum(n) {
  return n != null ? n.toLocaleString() : '-'
}

function formatTime(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatFullTime(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatJson(raw) {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制')).catch(() => ElMessage.error('复制失败'))
}

async function loadRecords() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }
    if (filterUserId.value || filterUserId.value === 0) params.user_id = filterUserId.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterModel.value) params.model = filterModel.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.date_from = filterDateRange.value[0]
      params.date_to = filterDateRange.value[1]
    }

    const res = await getQaRecords(params)
    records.value = res.items || []
    pagination.value.total = res.total || 0
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  filterUserId.value = ''
  filterStatus.value = ''
  filterModel.value = ''
  filterDateRange.value = null
  pagination.value.page = 1
  loadRecords()
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  loadRecords()
}

async function loadUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500 })
    allUsers.value = res.items || []
  } catch {}
}

async function viewDetail(rec) {
  detailRecord.value = rec
  showDetailDialog.value = true
}

async function showUserDetail(rec) {
  // Just show the name, don't navigate (no user detail in QA context)
}

async function confirmDelete(rec) {
  await ElMessageBox.confirm(`确定删除此对话记录 (ID: ${rec.id})？`, '确认删除', { type: 'warning' })
  await deleteQaRecord(rec.id)
  ElMessage.success('已删除')
  loadRecords()
}

onMounted(async () => {
  await loadUsers()
  await loadRecords()
})
</script>

<style scoped>
.filter-bar {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select :deep(.el-input__wrapper),
.filter-input :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(6, 214, 160, 0.1);
  border-radius: 10px;
  box-shadow: none;
  padding-left: 12px;
}

.filter-select :deep(.el-input__inner),
.filter-input :deep(.el-input__inner) {
  color: #e2e8f0;
  font-size: 13px;
}

.filter-select :deep(.el-input__inner::placeholder),
.filter-input :deep(.el-input__inner::placeholder) {
  color: #475569;
}

.filter-select :deep(.el-select__wrapper),
.filter-dates :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(6, 214, 160, 0.1);
  border-radius: 10px;
  box-shadow: none;
}

.filter-select :deep(.el-select__placeholder),
.filter-dates :deep(.el-input__inner) {
  color: #94a3b8;
}

.btn-reset {
  background: rgba(100, 116, 139, 0.08);
  color: #94a3b8;
  border: 1px solid rgba(100, 116, 139, 0.15);
  border-radius: 10px;
  padding: 0 16px;
  font-size: 13px;
}

.cell-user {
  color: #60a5fa;
  transition: color 0.15s;
}

.cell-user:hover {
  color: #06d6a0;
}

.badge-model {
  font-size: 12px;
  font-weight: 500;
  color: #e2e8f0;
}

.method-badge {
  font-size: 11px;
  font-weight: 700;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  padding: 2px 6px;
  border-radius: 4px;
  color: #94a3b8;
}

.status-success .status-dot { background: #06d6a0; box-shadow: 0 0 6px rgba(6, 214, 160, 0.5); }
.status-error .status-dot { background: #f87171; box-shadow: 0 0 6px rgba(248, 113, 113, 0.5); }
.status-timeout .status-dot { background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }

.upstream-status {
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  font-size: 12px;
  font-weight: 600;
}

.us-ok { color: #06d6a0; }
.us-err { color: #f87171; }

.cell-number {
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  font-size: 12px;
  text-align: right;
}

/* Detail dialog */
.detail-section {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-meta {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(6, 214, 160, 0.06);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 11px;
  color: #475569;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.meta-value {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-block {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(6, 214, 160, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(6, 214, 160, 0.03);
  border-bottom: 1px solid rgba(6, 214, 160, 0.06);
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

.btn-copy-inline {
  background: rgba(6, 214, 160, 0.08);
  border: none;
  color: #06d6a0;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
}

.json-block {
  margin: 0;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
  color: #cbd5e1;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
