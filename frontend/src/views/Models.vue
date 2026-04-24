<template>
  <div>
    <!-- 统计行 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value" :style="{ color: pagination.total > 0 ? '#06d6a0' : '#64748b' }">{{ pagination.total }}</div>
        <div class="stat-label">可用模型</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #3b82f6">{{ groupCount }}</div>
        <div class="stat-label">分组绑定</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f59e0b">{{ userCount }}</div>
        <div class="stat-label">使用用户数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #8b5cf6">24h</div>
        <div class="stat-label">最近活跃</div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-group">
        <el-input
          v-model="searchQuery"
          placeholder="按模型名称或 API 地址搜索..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @keyup.enter="() => loadModels(true)"
          @clear="() => loadModels(true)"
        >
          <template #append>
            <button class="btn-search" @click="loadModels(true)">搜索</button>
          </template>
        </el-input>
      </div>
      <el-button type="primary" @click="showDialog = true; editingId = null; resetForm()" class="btn-add">
        <el-icon><Plus /></el-icon>
        添加模型
      </el-button>
    </div>

    <!-- 表格 -->
    <div class="table-panel" v-loading="loading">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 70px">ID</th>
            <th>模型名称</th>
            <th>API 地址</th>
            <th>状态</th>
            <th style="width: 180px">创建时间</th>
            <th style="width: 200px; text-align: right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(model, idx) in models" :key="model.id" class="table-row" :style="{ animationDelay: idx * 0.04 + 's' }">
            <td><span class="cell-id">{{ model.id }}</span></td>
            <td>
              <span class="cell-model-name">{{ model.model_name }}</span>
            </td>
            <td>
              <span class="cell-url" @click="openUrl(model.api_url)">{{ model.api_url }}</span>
            </td>
            <td>
              <span class="badge-status" :class="model.status === 'active' ? 'status-active' : 'status-inactive'">
                <span class="status-dot" />
                {{ model.status === 'active' ? '正常运行' : '维护中' }}
              </span>
            </td>
            <td><span class="cell-date">{{ formatDate(model.created_at) }}</span></td>
            <td class="cell-actions">
              <el-button @click="editModel(model)" class="btn-cell" size="small">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button @click="confirmDelete(model)" class="btn-cell btn-danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </td>
          </tr>
          <tr v-if="!loading && models.length === 0">
            <td colspan="6" class="empty-row">暂无模型配置</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination-row" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadModels"
        />
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑模型' : '添加模型'" width="520px" class="glass-dialog" :close-on-click-modal="false">
      <div class="form-panels">
        <div class="form-left">
          <h3 class="form-section-title">基本信息</h3>
          <div class="form-field">
            <label class="form-label">模型名称 <span class="required">*</span></label>
            <el-input v-model="form.model_name" placeholder="例：gpt-4、claude-3" class="form-input" />
          </div>
          <div class="form-field">
            <label class="form-label">API 地址 <span class="required">*</span></label>
            <el-input v-model="form.api_url" placeholder="例：http://localhost:8000/v1" class="form-input" />
          </div>
          <div class="form-field">
            <label class="form-label">认证 Key <span class="required">*</span></label>
            <el-input v-model="form.api_key" type="password" placeholder="上游模型的 API 认证 Key" class="form-input" show-password />
          </div>
        </div>
        <div class="form-right">
          <h3 class="form-section-title">使用说明</h3>
          <div class="usage-hint">
            <p class="usage-text">模型配置将被分组引用，同一分组内所有用户共享此模型配置。</p>
            <p class="usage-text">每个用户拥有独立的 API Key，通过 OpenAI 兼容接口调用。</p>
            <pre class="code-block"><code>base_url = "your-api-endpoint"
model = "{{ form.model_name || 'gpt-4' }}"
api_key = "USER_KEY"</code></pre>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="submitting" class="btn-primary">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { getUsers } from '@/api/user.js'
import { getGlobalModels, createGlobalModel, updateGlobalModel, deleteGlobalModel } from '@/api/admin_models.js'

const models = ref([])
const loading = ref(false)
const searchQuery = ref('')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const showDialog = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const form = ref({
  model_name: '', api_url: '', api_key: '',
})

const groupCount = ref(0)
const userCount = ref(0)

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function openUrl(url) {
  window.open(url, '_blank')
}

async function loadGroups() {
  try {
    let totalUsers = 0
    try {
      const users = await getUsers({ page: 1, page_size: 1 })
      totalUsers = users.total || 0
    } catch {}
    try {
      const { getGroups } = await import('@/api/groups.js')
      const groupsRes = await getGroups({ page: 1, page_size: 1 })
      groupCount.value = groupsRes.total || 0
    } catch {}
    userCount.value = totalUsers
  } catch {}
}

async function loadModels(resetPage = false) {
  if (resetPage) pagination.value.page = 1
  loading.value = true
  try {
    const res = await getGlobalModels({ page: pagination.value.page, page_size: pagination.value.pageSize, search: searchQuery.value })
    models.value = res.items || []
    pagination.value.total = res.total || 0
  } catch (e) {
    models.value = []
    pagination.value.total = 0
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form.value, { model_name: '', api_url: '', api_key: '' })
  editingId.value = null
}

function editModel(m) {
  Object.assign(form.value, { model_name: m.model_name, api_url: m.api_url, api_key: m.api_key })
  editingId.value = m.id
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.model_name || !form.value.api_url || !form.value.api_key) {
    ElMessage.warning('请填写所有必填项')
    return
  }
  submitting.value = true
  try {
    if (editingId.value) {
      const data = { model_name: form.value.model_name, api_url: form.value.api_url }
      if (form.value.api_key) {
        data.api_key = form.value.api_key
      }
      await updateGlobalModel(editingId.value, data)
      ElMessage.success('模型配置已更新')
    } else {
      await createGlobalModel({
        model_name: form.value.model_name,
        api_url: form.value.api_url,
        api_key: form.value.api_key,
      })
      ElMessage.success('模型添加成功')
    }
    showDialog.value = false
    resetForm()
    loadModels()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally { submitting.value = false }
}

async function confirmDelete(m) {
  await ElMessageBox.confirm(`确定删除模型 "${m.model_name}"？如果它正被分组使用，请先解除绑定。`, '确认删除', { type: 'warning' })
  try {
    await deleteGlobalModel(m.id)
    ElMessage.success('已删除')
    loadModels()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => { loadModels(); loadGroups() })
</script>

<style scoped>
.cell-model-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 13px;
}

.cell-url {
  color: #60a5fa;
  font-size: 12px;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.cell-url:hover { color: #93c5fd; text-decoration: underline; }

.status-inactive .status-dot { background: #64748b; }

.form-panels {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

.form-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(6, 214, 160, 0.06);
}

.usage-hint {
  background: rgba(59, 130, 246, 0.04);
  border: 1px solid rgba(59, 130, 246, 0.1);
  border-radius: 10px;
  padding: 14px 16px;
}

.usage-text {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.7;
  margin: 0 0 12px;
}

.usage-text:last-child { margin-bottom: 0; }

.code-block {
  margin: 0;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(6, 214, 160, 0.08);
  border-radius: 8px;
  overflow-x: auto;
}

.code-block code {
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  font-size: 11px;
  color: #06d6a0;
  line-height: 1.7;
  white-space: pre;
}
</style>
