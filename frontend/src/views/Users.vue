<template>
  <div>
    <!-- 统计行 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value" :style="{ color: pagination.total > 0 ? '#06d6a0' : '#64748b' }">{{ pagination.total }}</div>
        <div class="stat-label">用户总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #06d6a0">{{ activeCount }}</div>
        <div class="stat-label">正常使用</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f59e0b">{{ bannedCount }}</div>
        <div class="stat-label">已封禁</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f87171">{{ disabledCount }}</div>
        <div class="stat-label">已禁用</div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-group">
        <el-input
          v-model="searchQuery"
          placeholder="按用户名或显示名称搜索..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @keyup.enter="() => loadUsers(true)"
          @clear="() => loadUsers(true)"
        >
          <template #append>
            <button class="btn-search" @click="loadUsers(true)">搜索</button>
          </template>
        </el-input>
      </div>
      <el-button type="primary" @click="showCreateDialog = true" class="btn-add">
        <el-icon><Plus /></el-icon>
        添加用户
      </el-button>
    </div>

    <!-- 表格 -->
    <div class="table-panel" v-loading="loading">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 70px">ID</th>
            <th>用户</th>
            <th>角色</th>
            <th>所属分组</th>
            <th>状态</th>
            <th style="width: 110px">余额</th>
            <th style="width: 100px">IP 白名单</th>
            <th style="width: 180px">创建时间</th>
            <th style="width: 260px; text-align: right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, idx) in users" :key="user.id" class="table-row" :style="{ animationDelay: idx * 0.04 + 's' }">
            <td>
              <span class="cell-id">{{ user.id }}</span>
            </td>
            <td>
              <div class="cell-user">
                <div class="user-avatar" :class="'avatar-' + (user.id % 5)">
                  {{ (user.display_name || user.username).charAt(0).toUpperCase() }}
                </div>
                <div class="user-main">
                  <div class="user-name">{{ user.username }}</div>
                  <div class="user-display">{{ user.display_name || '-' }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="badge-role" :class="user.role === 'admin' ? 'role-admin' : 'role-user'">
                {{ user.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td>
              <el-tag
                v-if="getGroupForUser(user.id)"
                size="small"
                effect="light"
                class="group-tag"
              >
                {{ getGroupForUser(user.id) }}
              </el-tag>
              <span v-else class="no-group">未分配</span>
            </td>
            <td>
              <span class="badge-status" :class="'status-' + user.status">
                <span class="status-dot" />
                {{ statusLabel(user.status) }}
              </span>
            </td>
            <td>
              <span class="cell-balance" :class="user.balance > 0 ? 'balance-positive' : 'balance-zero'">
                {{ user.balance.toLocaleString() }}
              </span>
            </td>
            <td>
              <el-tag v-if="user.allowed_ips && user.allowed_ips.trim()" size="small" effect="light" type="success" class="ip-tag">
                <el-icon style="margin-right: 3px;"><Lock /></el-icon>
                已设置
              </el-tag>
              <span v-else class="no-ip">无限制</span>
            </td>
            <td>
              <span class="cell-date">{{ formatDate(user.created_at) }}</span>
            </td>
            <td class="cell-actions">
              <el-button @click="viewApiKeys(user)" class="btn-cell" size="small">
                <el-icon><Key /></el-icon> Key
              </el-button>
              <el-button @click="editUser(user)" class="btn-cell" size="small">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button @click="confirmDelete(user)" class="btn-cell btn-danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </td>
          </tr>
          <tr v-if="!loading && users.length === 0">
            <td colspan="9" class="empty-row">暂无用户数据</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadUsers"
        />
      </div>
    </div>

    <!-- 新建对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建用户" width="520px" class="glass-dialog" :close-on-click-modal="false">
      <el-form :model="createForm" class="create-form">
        <div class="form-field">
          <label class="form-label">用户名 <span class="required">*</span></label>
          <el-input v-model="createForm.username" placeholder="请输入用户名" class="form-input" />
        </div>
        <div class="form-field">
          <label class="form-label">显示名称</label>
          <el-input v-model="createForm.display_name" placeholder="选填" class="form-input" />
        </div>
        <div class="form-field">
          <label class="form-label">密码 <span class="required">*</span></label>
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" class="form-input" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">角色</label>
            <el-select v-model="createForm.role" class="form-input">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </div>
          <div class="form-field">
            <label class="form-label">初始余额</label>
            <el-input-number v-model="createForm.initial_balance" :min="0" :step="100" class="form-input" />
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="submitting" class="btn-primary">创建</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑用户" width="520px" class="glass-dialog" :close-on-click-modal="false">
      <el-form :model="editForm" class="create-form">
        <div class="form-field">
          <label class="form-label">显示名称</label>
          <el-input v-model="editForm.display_name" class="form-input" />
        </div>
        <div class="form-field">
          <label class="form-label">新密码</label>
          <el-input v-model="editForm.password" type="password" placeholder="留空则不修改" class="form-input" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">角色</label>
            <el-select v-model="editForm.role" class="form-input">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </div>
          <div class="form-field">
            <label class="form-label">状态</label>
            <el-select v-model="editForm.status" class="form-input">
              <el-option label="正常使用" value="active" />
              <el-option label="已封禁" value="banned" />
              <el-option label="已禁用" value="disabled" />
            </el-select>
          </div>
        </div>
        <div class="form-field">
          <label class="form-label">余额</label>
          <el-input-number v-model="editForm.initial_balance" :min="0" :step="100" class="form-input" />
        </div>
        <div class="form-field">
          <label class="form-label">IP 白名单（逗号分隔，留空不限制）</label>
          <el-input v-model="editForm.allowed_ips" type="textarea" :rows="2" placeholder="例如：192.168.1.100, 10.0.0.0/24" class="form-input" />
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEdit" :loading="submitting" class="btn-primary">保存修改</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- API Key 对话框 -->
    <el-dialog v-model="showKeyDialog" :title="`API Key — ${currentUserName}`" width="620px" class="glass-dialog" :close-on-click-modal="false">
      <div class="key-intro">
        此 API Key 是用户通过 OpenAI 兼容接口访问分组内共享模型时的身份凭证。<strong>{{ currentUserName }}</strong> 当前通过 API Key 进行身份验证。
      </div>
      <div v-if="apiKeys.length > 0">
        <div v-for="key in apiKeys" :key="key.id" class="key-row">
          <div class="key-label">
            <span class="key-name">{{ key.name }}</span>
            <span class="key-status" :class="'status-' + key.status">{{ key.status }}</span>
          </div>
          <div class="key-value-wrap">
            <code class="key-value">{{ key.key }}</code>
            <el-button @click="copyText(key.key)" size="small" class="btn-copy">复制</el-button>
          </div>
        </div>
        <el-button @click="handleRenew" :loading="renewing" class="btn-renew">
          生成新 API Key
        </el-button>
      </div>
      <div v-else class="empty-keys">
        该用户暂未分配 API Key。
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Key, Edit, Delete, Lock } from '@element-plus/icons-vue'
import { getUsers, createUser, updateUser, deleteUser, getApiKeys, renewApiKey } from '@/api/user'

const router = useRouter()
const users = ref([])
const loading = ref(false)
const searchQuery = ref('')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showKeyDialog = ref(false)
const submitting = ref(false)
const renewing = ref(false)
const currentUserName = ref('')
const apiKeys = ref([])

const createForm = ref({
  username: '', display_name: '', password: '',
  role: 'user', initial_balance: 0,
})

const editForm = ref({
  id: null, display_name: '', password: '',
  role: 'user', status: 'active', initial_balance: 0, allowed_ips: '',
})

const activeCount = computed(() => users.value.filter(u => u.status === 'active').length)
const bannedCount = computed(() => users.value.filter(u => u.status === 'banned').length)
const disabledCount = computed(() => users.value.filter(u => u.status === 'disabled').length)

function statusLabel(s) {
  return { active: '正常使用', banned: '已封禁', disabled: '已禁用' }[s] || s
}
function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function getGroupForUser(userId) {
  const user = users.value.find(u => u.id === userId)
  if (!user || !user.group_names || user.group_names.length === 0) return null
  return user.group_names.join('、')
}

async function loadUsers(resetPage = false) {
  if (resetPage) pagination.value.page = 1
  loading.value = true
  try {
    const res = await getUsers({ page: pagination.value.page, page_size: pagination.value.pageSize, search: searchQuery.value })
    users.value = res.items || []
    pagination.value.total = res.total || 0
  } finally {
    loading.value = false
  }
}

function editUser(user) {
  Object.assign(editForm.value, {
    id: user.id, display_name: user.display_name, password: '',
    role: user.role, status: user.status, initial_balance: user.balance,
    allowed_ips: user.allowed_ips || '',
  })
  showEditDialog.value = true
}

async function handleEdit() {
  submitting.value = true
  try {
    const data = { ...editForm.value }; delete data.id
    if (!data.password) delete data.password
    await updateUser(editForm.value.id, data)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    loadUsers()
  } finally { submitting.value = false }
}

async function handleCreate() {
  if (!createForm.value.username || !createForm.value.password) {
    ElMessage.warning('用户名和密码为必填项')
    return
  }
  submitting.value = true
  try {
    await createUser(createForm.value)
    ElMessage.success('用户创建成功')
    showCreateDialog.value = false
    Object.assign(createForm.value, { username: '', display_name: '', password: '', role: 'user', initial_balance: 0 })
    loadUsers()
  } finally { submitting.value = false }
}

async function confirmDelete(user) {
  await ElMessageBox.confirm(`确定删除用户 "${user.username}"？此操作不可恢复。`, '确认删除', { type: 'warning' })
  await deleteUser(user.id)
  ElMessage.success('已删除')
  loadUsers()
}

async function viewApiKeys(user) {
  currentUserName.value = user.display_name || user.username
  showKeyDialog.value = true
  try { apiKeys.value = await getApiKeys(user.id) } catch { apiKeys.value = [] }
}

async function handleRenew() {
  if (!apiKeys.value.length) return
  renewing.value = true
  try {
    const r = await renewApiKey(apiKeys.value[0].user_id)
    apiKeys.value.length = 0
    apiKeys.value.push(r)
    ElMessage.success('新 API Key 已生成')
  } finally { renewing.value = false }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制')).catch(() => ElMessage.error('复制失败'))
}

onMounted(() => loadUsers())
</script>

<style scoped>
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  color: #fff;
  flex-shrink: 0;
}

.avatar-0 { background: linear-gradient(135deg, #06d6a0, #0891b2); }
.avatar-1 { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.avatar-2 { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.avatar-3 { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.avatar-4 { background: linear-gradient(135deg, #14b8a6, #06b6d4); }

.user-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 12px;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 13px;
}

.user-display {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge-role {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.role-admin {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.role-user {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.15);
}

.status-banned .status-dot { background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }
.status-disabled .status-dot { background: #f87171; box-shadow: 0 0 6px rgba(248, 113, 113, 0.5); }

.balance-positive {
  font-weight: 700;
  color: #06d6a0;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  font-size: 13px;
}

.balance-zero {
  color: #64748b;
  font-family: 'SFMono-Regular', 'Consolas', monospace;
  font-size: 13px;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.group-tag {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-radius: 6px;
}

.no-group {
  color: #475569;
  font-size: 12px;
}

.ip-tag {
  background: rgba(6, 214, 160, 0.1);
  border-color: rgba(6, 214, 160, 0.2);
  color: #06d6a0;
  border-radius: 6px;
  font-size: 11px;
}

.no-ip {
  color: #64748b;
  font-size: 12px;
}
</style>
