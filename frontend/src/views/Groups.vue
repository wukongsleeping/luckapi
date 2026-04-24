<template>
  <div>
    <!-- 统计行 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value" :style="{ color: pagination.total > 0 ? '#06d6a0' : '#64748b' }">{{ pagination.total }}</div>
        <div class="stat-label">分组总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #3b82f6">{{ totalMembers }}</div>
        <div class="stat-label">已分配用户</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f59e0b">{{ totalModels }}</div>
        <div class="stat-label">使用模型</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #8b5cf6">{{ pendingCount }}</div>
        <div class="stat-label">未分配用户</div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-group">
        <el-input
          v-model="searchQuery"
          placeholder="按分组名称搜索..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @keyup.enter="() => loadGroups(true)"
          @clear="() => loadGroups(true)"
        >
          <template #append>
            <button class="btn-search" @click="loadGroups(true)">搜索</button>
          </template>
        </el-input>
      </div>
      <el-button type="primary" @click="showCreateDialog = true" class="btn-add">
        <el-icon><Plus /></el-icon>
        新建分组
      </el-button>
    </div>

    <!-- 表格 -->
    <div class="table-panel" v-loading="loading">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 70px">ID</th>
            <th>分组名称</th>
            <th>绑定模型</th>
            <th>成员数</th>
            <th style="width: 110px">状态</th>
            <th style="width: 180px">创建时间</th>
            <th style="width: 260px; text-align: right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(grp, idx) in groups" :key="grp.id" class="table-row" :style="{ animationDelay: idx * 0.04 + 's' }">
            <td><span class="cell-id">{{ grp.id }}</span></td>
            <td>
              <div class="cell-group-name">
                <div class="group-icon" :class="'group-color-' + (grp.id % 5)">{{ (grp.name || 'G').charAt(0).toUpperCase() }}</div>
                <span class="name-text">{{ grp.name }}</span>
              </div>
            </td>
            <td>
              <span class="cell-model-badge" v-if="grp.model_name">
                <el-icon class="model-badge-icon"><Cpu /></el-icon>
                {{ grp.model_name }}
              </span>
              <span class="cell-model-badge empty" v-else>未配置</span>
            </td>
            <td>
              <div class="cell-members">
                <span class="member-count">{{ grp.member_ids ? grp.member_ids.length : 0 }}/</span>
                <el-button @click="openGroupDetail(grp)" class="btn-member" size="small">
                  查看成员
                </el-button>
              </div>
            </td>
            <td>
              <span class="badge-status" :class="grp.member_ids && grp.member_ids.length > 0 ? 'status-active' : 'status-pending'">
                <span class="status-dot" />
                {{ grp.member_ids && grp.member_ids.length > 0 ? '已启用' : '待分配' }}
              </span>
            </td>
            <td><span class="cell-date">{{ formatDate(grp.created_at) }}</span></td>
            <td class="cell-actions">
              <el-button @click="openGroupDetail(grp)" class="btn-cell" size="small">
                <el-icon><Connection /></el-icon> 管理
              </el-button>
              <el-button @click="editGroup(grp)" class="btn-cell" size="small">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button @click="confirmDeleteGroup(grp)" class="btn-cell btn-danger" size="small">
                <el-icon><Delete /></el-icon>
              </el-button>
            </td>
          </tr>
          <tr v-if="!loading && groups.length === 0">
            <td colspan="7" class="empty-row">暂无分组，点击"新建分组"开始</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadGroups"
        />
      </div>
    </div>

    <!-- 新建分组对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建分组" width="560px" class="glass-dialog" :close-on-click-modal="false">
      <el-form :model="createForm" class="group-form">
        <div class="form-field">
          <label class="form-label">分组名称 <span class="required">*</span></label>
          <el-input v-model="createForm.name" placeholder="例：VIP用户组、测试组" class="form-input" />
        </div>
        <div class="form-field">
          <label class="form-label">绑定模型配置 <span class="required">*</span></label>
          <el-select v-model="createForm.model_id" placeholder="选择已配置的模型" class="form-input" clearable>
            <el-option
              v-for="m in availableModels"
              :key="m.id"
              :label="m.model_name"
              :value="m.id"
            >
              <span class="option-model-info">
                <span>{{ m.model_name }}</span>
                <span class="model-url-text">{{ m.api_url }}</span>
              </span>
            </el-option>
          </el-select>
          <span class="form-hint">模型需先在"模型管理"中配置，分组内所有成员将共享此模型</span>
        </div>
        <div class="form-section">
          <h4 class="section-title">分配用户（可选）</h4>
          <div class="user-chips">
            <div v-for="uid in createForm.user_ids" :key="uid" class="user-chip">
              <span class="chip-label">用户 #{{ uid }}</span>
              <el-icon class="chip-remove" @click="removeCreateUser(uid)"><Close /></el-icon>
            </div>
            <el-select
              v-if="allUsers.length > 0 && !createForm.user_ids.includes('__search')"
              v-model="createForm.user_ids"
              placeholder="选择要分配的用户"
              class="assign-user-select"
              multiple
              filterable
              clearable
              @change="(v) => { createForm.user_ids = v }"
            >
              <el-option
                v-for="u in unassignedCreateUsers"
                :key="u.id"
                :label="u.display_name || u.username"
                :value="u.id"
              />
            </el-select>
            <el-button
              v-if="allUsers.length > 0 && unassignedCreateUsers.length > 0"
              @click="createForm.user_ids.push('__search')"
              class="btn-add-user"
              size="small"
              type="primary"
              link
            >
              继续添加用户
            </el-button>
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

    <!-- 编辑分组对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑分组" width="520px" class="glass-dialog" :close-on-click-modal="false">
      <div class="form-field">
        <label class="form-label">分组名称</label>
        <el-input v-model="editForm.name" class="form-input" />
      </div>
      <div class="form-field">
        <label class="form-label">绑定模型</label>
        <el-select v-model="editForm.model_id" placeholder="选择模型" class="form-input" clearable>
          <el-option
            v-for="m in availableModels"
            :key="m.id"
            :label="m.model_name"
            :value="m.id"
          />
        </el-select>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleEdit" :loading="submitting" class="btn-primary">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 分组详情对话框：模型信息 + 成员列表 -->
    <el-dialog v-model="showDetailDialog" :title="`分组管理 — ${currentGroup?.name}`" width="720px" class="glass-dialog" :close-on-click-modal="false">
      <div class="detail-container">
        <!-- 模型信息 -->
        <div class="detail-section">
          <h3 class="detail-section-title">
            <el-icon><Cpu /></el-icon>
            模型绑定
          </h3>
          <div class="model-card" v-if="currentGroup?.model_name">
            <div class="model-info">
              <span class="model-name">{{ currentGroup.model_name }}</span>
              <span class="model-url">{{ currentGroup.model_url || '-' }}</span>
            </div>
            <el-button @click="changeGroupModel" class="btn-change-model" size="small" type="primary" link>
              更换模型
            </el-button>
          </div>
          <div class="model-empty" v-else>
            <el-icon class="empty-icon"><WarningFilled /></el-icon>
            <span>此分组未绑定任何模型，请先配置</span>
            <el-button @click="changeGroupModel" class="btn-change-model" size="small" type="primary" link>
              立即配置
            </el-button>
          </div>
        </div>

        <!-- 成员管理 -->
        <div class="detail-section">
          <div class="detail-section-header">
            <h3 class="detail-section-title">
              <el-icon><User /></el-icon>
              组成员（{{ groupMembers.length }}）
            </h3>
            <el-button @click="showMemberDialog = true" class="btn-add-member" size="small" type="primary">
              <el-icon><Plus /></el-icon>
              添加成员
            </el-button>
          </div>
          <div class="member-list" v-if="groupMembers.length > 0">
            <div v-for="m in groupMembers" :key="m.id" class="member-item">
              <div class="member-avatar" :class="'avatar-' + (m.id % 5)">{{ (m.display_name || m.username).charAt(0).toUpperCase() }}</div>
              <div class="member-main">
                <span class="member-name">{{ m.display_name || m.username }}</span>
                <span class="member-username">@{{ m.username }}</span>
              </div>
              <div class="member-actions">
                <el-button @click="viewMemberKeys(m)" class="btn-cell" size="small">
                  <el-icon><Key /></el-icon>
                </el-button>
                <el-button @click="removeMember(m.id)" class="btn-cell btn-danger" size="small">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
          <div class="empty-members" v-else>
            <span>暂无成员，点击"添加成员"分配用户到此分组</span>
          </div>
        </div>
      </div>

      <!-- Member Key Dialog -->
      <el-dialog v-model="showKeyDialog" :title="`API Key — ${currentMemberName}`" width="620px" class="glass-dialog" :close-on-click-modal="false">
        <div v-if="memberKeys.length > 0">
          <div v-for="key in memberKeys" :key="key.id" class="key-row">
            <div class="key-label">
              <span class="key-name">{{ key.name }}</span>
              <span class="key-status" :class="'status-' + key.status">{{ key.status }}</span>
            </div>
            <div class="key-value-wrap">
              <code class="key-value">{{ key.key }}</code>
              <el-button @click="copyText(key.key)" size="small" class="btn-copy">复制</el-button>
            </div>
          </div>
        </div>
        <div v-else class="empty-keys">暂无 API Key</div>
      </el-dialog>

      <!-- Add Member Dialog -->
      <el-dialog v-model="showMemberDialog" title="添加成员" width="500px" class="glass-dialog" :close-on-click-modal="false">
        <el-select
          v-model="memberForm.user_ids"
          placeholder="选择要添加的用户"
          class="full-size-select"
          multiple
          filterable
          :disabled="allUsers.length === 0"
        >
          <el-option
            v-for="u in unassignedMembers"
            :key="u.id"
            :label="u.display_name || u.username"
            :value="u.id"
          />
        </el-select>
        <div class="assign-hint">
          选择后将把用户添加到此分组，用户将共享分组绑定的模型并可使用其 API Key 访问。
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showMemberDialog = false">取消</el-button>
            <el-button type="primary" @click="handleAddMembers" :loading="submitting" class="btn-primary">添加</el-button>
          </div>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete, Connection, Cpu, Key, Close, WarningFilled } from '@element-plus/icons-vue'
import { getGroups, getGroup, createGroup, updateGroup, deleteGroup, assignGroupUser, removeGroupUser } from '@/api/groups.js'
import { getUsers, getApiKeys } from '@/api/user.js'
import { getGlobalModels, getGlobalModel } from '@/api/admin_models.js'

const groups = ref([])
const allUsers = ref([])
const availableModels = ref([])
const userMap = ref(new Map())
const loading = ref(false)
const searchQuery = ref('')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const showMemberDialog = ref(false)
const showKeyDialog = ref(false)
const submitting = ref(false)

const currentGroup = reactive({})
const groupMembers = ref([])
const currentMemberName = ref('')
const memberKeys = ref([])

const createForm = ref({
  name: '', model_id: '', user_ids: [],
})

const editForm = ref({
  id: null, name: '', model_id: null,
})

const memberForm = ref({
  user_ids: [],
})

const totalMembers = computed(() => groups.value.reduce((sum, g) => sum + (g.member_ids ? g.member_ids.length : 0), 0))
const totalModels = computed(() => groups.value.filter(g => g.model_name).length)
const pendingCount = computed(() => groups.value.filter(g => !g.member_ids || g.member_ids.length === 0).length)

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

const unassignedCreateUsers = computed(() => {
  if (createForm.value.user_ids.includes('__search')) return allUsers.value
  return allUsers.value.filter(u => !createForm.value.user_ids.includes(u.id))
})

const unassignedMembers = computed(() => {
  if (!currentGroup.member_ids) return allUsers.value
  return allUsers.value.filter(u => !currentGroup.member_ids.includes(u.id))
})

async function loadUsers() {
  try {
    const res = await getUsers({ page: 1, page_size: 500 })
    allUsers.value = res.items || []
    userMap.value = new Map()
    for (const u of allUsers.value) {
      userMap.value.set(u.id, u)
    }
  } catch {}
}

async function loadAvailableModels() {
  try {
    const res = await getGlobalModels({ page: 1, page_size: 500 })
    availableModels.value = res.items || []
  } catch {}
}

async function resolveModelInfo(modelId) {
  if (!modelId || !availableModels.value.length) return null
  return getGlobalModel(modelId)
}

async function loadGroups(resetPage = false) {
  if (resetPage) pagination.value.page = 1
  loading.value = true
  try {
    const res = await getGroups({ page: pagination.value.page, page_size: pagination.value.pageSize, search: searchQuery.value })
    groups.value = res.items || []
    pagination.value.total = res.total || 0
  } catch {
    groups.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

async function loadGroupMembers(grp) {
  try {
    groupMembers.value = []
    if (grp.member_ids && grp.member_ids.length > 0) {
      for (const uid of grp.member_ids) {
        const user = userMap.value.get(uid)
        if (user) {
          if (!groupMembers.value.find(m => m.id === uid)) {
            groupMembers.value.push(user)
          }
        } else {
          const res = await getUsers({ page: 1, page_size: 500 })
          const found = (res.items || []).find(u => u.id === uid)
          if (found) {
            groupMembers.value.push(found)
            userMap.value.set(found.id, found)
            allUsers.value.push(found)
          }
        }
      }
    }
  } catch {
    groupMembers.value = []
  }
}

function openGroupDetail(grp) {
  Object.assign(currentGroup, grp)
  showDetailDialog.value = true
  loadGroupMembers(grp)
}

async function editGroup(grp) {
  const detail = await getGroup(grp.id)
  Object.assign(editForm.value, {
    id: detail.id,
    name: detail.name,
    model_id: detail.model_id || null,
  })
  showEditDialog.value = true
}

async function handleEdit() {
  if (!editForm.value.name) {
    ElMessage.warning('请填写分组名称')
    return
  }
  submitting.value = true
  try {
    const updateData = { name: editForm.value.name }
    if (editForm.value.model_id) {
      const model = await resolveModelInfo(editForm.value.model_id)
      if (model) {
        updateData.model_name = model.model_name
        updateData.model_url = model.api_url
        if (model.api_key) updateData.model_api_key = model.api_key
      }
    }
    await updateGroup(editForm.value.id, updateData)
    ElMessage.success('分组已更新')
    showDetailDialog.value = false
    showEditDialog.value = false
    loadGroups()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally { submitting.value = false }
}

async function confirmDeleteGroup(grp) {
  await ElMessageBox.confirm(`确定删除分组 "${grp.name}"？组成员不会被移除。`, '确认删除', { type: 'warning' })
  await deleteGroup(grp.id)
  ElMessage.success('已删除')
  loadGroups()
}

async function handleCreate() {
  if (!createForm.value.name) {
    ElMessage.warning('请填写分组名称')
    return
  }
  submitting.value = true
  try {
    let groupData = { name: createForm.value.name }
    if (createForm.value.model_id) {
      const model = await resolveModelInfo(createForm.value.model_id)
      if (model) {
        groupData.model_name = model.model_name
        groupData.model_url = model.api_url
        if (model.api_key) groupData.model_api_key = model.api_key
      }
    }
    const created = await createGroup(groupData)
    const assignedIds = [...(createForm.value.user_ids || [])]
    if (assignedIds.length > 0) {
      created.member_ids = created.member_ids || []
      for (const uid of assignedIds) {
        try {
          await assignGroupUser(created.id, uid)
          created.member_ids.push(uid)
          const user = userMap.value.get(uid)
          if (user && !groupMembers.value.find(m => m.id === uid)) {
            groupMembers.value.push(user)
          }
        } catch (e) {
          ElMessage.warning(`用户 #${uid} 添加失败：${e.response?.data?.detail || '未知原因'}`)
        }
      }
    }
    ElMessage.success('分组创建成功')
    showCreateDialog.value = false
    Object.assign(createForm.value, { name: '', model_id: '', user_ids: [] })
    loadGroups()
  } finally { submitting.value = false }
}

function changeGroupModel() {
  Object.assign(editForm.value, {
    id: currentGroup.id,
    name: currentGroup.name,
    model_id: currentGroup.model_name ? (availableModels.value.find(m => m.model_name === currentGroup.model_name)?.id || null) : null,
  })
  showEditDialog.value = true
  showDetailDialog.value = false
}

async function handleAddMembers() {
  if (!memberForm.value.user_ids.length) {
    ElMessage.warning('请选择要添加的用户')
    return
  }
  submitting.value = true
  let successCount = 0
  let errors = []
  try {
    for (const uid of memberForm.value.user_ids) {
      try {
        await assignGroupUser(currentGroup.id, uid)
        successCount++
        if (currentGroup.member_ids) {
          currentGroup.member_ids.push(uid)
        }
        const user = userMap.value.get(uid)
        if (user && !groupMembers.value.find(m => m.id === uid)) {
          groupMembers.value.push(user)
        }
      } catch (e) {
        const msg = e.response?.data?.detail || '添加失败'
        errors.push(`${uid}: ${msg}`)
      }
    }
    if (successCount > 0) {
      ElMessage.success(`已添加 ${successCount} 个成员`)
      showMemberDialog.value = false
      Object.assign(memberForm.value, { user_ids: [] })
    } else {
      ElMessage.error('添加失败：' + (errors.length > 0 ? errors.join('; ') : '未知原因'))
    }
  } catch {
    ElMessage.error('添加成员失败')
  } finally { submitting.value = false }
}

async function removeMember(uid) {
  await ElMessageBox.confirm('确定从此分组移除此用户？', '确认移除', { type: 'warning' })
  try {
    await removeGroupUser(currentGroup.id, uid)
    groupMembers.value = groupMembers.value.filter(m => m.id !== uid)
    if (currentGroup) {
      const idx = currentGroup.member_ids.indexOf(uid)
      if (idx > -1) currentGroup.member_ids.splice(idx, 1)
    }
    ElMessage.success('已移除')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '移除失败')
  }
}

async function viewMemberKeys(member) {
  currentMemberName.value = member.display_name || member.username
  showKeyDialog.value = true
  try { memberKeys.value = await getApiKeys(member.id) } catch { memberKeys.value = [] }
}

function removeCreateUser(uid) {
  const idx = createForm.value.user_ids.indexOf(uid)
  if (idx > -1) createForm.value.user_ids.splice(idx, 1)
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制')).catch(() => ElMessage.error('复制失败'))
}

onMounted(() => { loadGroups(); loadUsers(); loadAvailableModels() })
</script>

<style scoped>
.cell-group-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #fff;
  flex-shrink: 0;
}

.group-color-0 { background: linear-gradient(135deg, #06d6a0, #0891b2); }
.group-color-1 { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.group-color-2 { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.group-color-3 { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.group-color-4 { background: linear-gradient(135deg, #14b8a6, #06b6d4); }

.name-text {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 13px;
}

.cell-model-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.06);
  padding: 4px 10px;
  border-radius: 6px;
}

.model-badge-icon {
  font-size: 14px;
}

.cell-model-badge.empty {
  color: #64748b;
  background: rgba(100, 116, 139, 0.08);
}

.cell-members {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-count {
  font-size: 13px;
  color: #06d6a0;
  font-weight: 600;
  font-family: 'SFMono-Regular', monospace;
}

.btn-member {
  background: rgba(6, 214, 160, 0.08);
  border: 1px solid rgba(6, 214, 160, 0.15);
  color: #06d6a0;
  border-radius: 6px;
  font-size: 12px;
  padding: 4px 12px;
}

.btn-member:hover {
  background: rgba(6, 214, 160, 0.15);
}

.status-pending .status-dot { background: #f59e0b; }

.group-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-hint {
  font-size: 11px;
  color: #475569;
  margin-top: -2px;
}

.form-section {
  margin-top: 4px;
  padding-top: 16px;
  border-top: 1px solid rgba(6, 214, 160, 0.06);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(6, 214, 160, 0.08);
  border: 1px solid rgba(6, 214, 160, 0.15);
  border-radius: 6px;
  padding: 4px 8px;
}

.chip-label {
  font-size: 12px;
  color: #06d6a0;
  font-weight: 500;
}

.chip-remove {
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.15s;
}

.chip-remove:hover { color: #f87171; }

.assign-user-select {
  width: 220px;
}

.assign-user-select :deep(.el-input__wrapper) {
  background: rgba(2, 8, 23, 0.6);
  border: 1px solid rgba(6, 214, 160, 0.1);
  border-radius: 8px;
  box-shadow: none;
  padding: 0 12px;
}

.assign-user-select :deep(.el-input__inner) {
  color: #e2e8f0;
}

.btn-add-user {
  font-size: 12px;
}

.option-model-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.model-url-text {
  font-size: 11px;
  color: #475569;
}

/* === Detail Container === */
.detail-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(6, 214, 160, 0.06);
  border-radius: 10px;
  padding: 16px 20px;
}

.detail-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-section-title .el-icon {
  color: #06d6a0;
}

.model-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 8px;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.model-url {
  font-size: 11px;
  color: #64748b;
  font-family: 'SFMono-Regular', monospace;
}

.model-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: #64748b;
  font-size: 13px;
}

.empty-icon {
  font-size: 20px;
  color: #f59e0b;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(2, 8, 23, 0.4);
  border: 1px solid rgba(6, 214, 160, 0.06);
  border-radius: 8px;
  transition: border-color 0.2s;
}

.member-item:hover {
  border-color: rgba(6, 214, 160, 0.15);
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  color: #fff;
  flex-shrink: 0;
}

.avatar-0 { background: linear-gradient(135deg, #06d6a0, #0891b2); }
.avatar-1 { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.avatar-2 { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.avatar-3 { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
.avatar-4 { background: linear-gradient(135deg, #14b8a6, #06b6d4); }

.member-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.member-name {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.member-username {
  font-size: 11px;
  color: #475569;
}

.member-actions {
  display: flex;
  gap: 4px;
}

.btn-add-member {
  background: rgba(6, 214, 160, 0.1);
  border: 1px solid rgba(6, 214, 160, 0.2);
  color: #06d6a0;
  border-radius: 6px;
  font-size: 12px;
  padding: 5px 12px;
}

.btn-add-member:hover {
  background: rgba(6, 214, 160, 0.18);
}

.empty-members {
  padding: 20px;
  text-align: center;
  color: #475569;
  font-size: 13px;
}

.btn-change-model {
  color: #06d6a0;
  font-size: 12px;
}

.assign-hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 12px;
  line-height: 1.6;
  padding: 10px 14px;
  background: rgba(148, 163, 184, 0.04);
  border-radius: 6px;
}

.full-size-select {
  width: 100%;
}

.full-size-select :deep(.el-input__wrapper) {
  background: rgba(2, 8, 23, 0.6);
  border: 1px solid rgba(6, 214, 160, 0.1);
  border-radius: 8px;
  box-shadow: none;
  padding: 0 12px;
}

.full-size-select :deep(.el-input__inner) {
  color: #e2e8f0;
}
</style>
