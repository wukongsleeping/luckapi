<template>
  <el-container class="app-root">
    <div class="bg-grid" />

    <el-aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-icon">
            <rect x="2" y="2" width="20" height="20" rx="3" stroke="#06d6a0" stroke-width="1.5"/>
            <path d="M7 9h6M7 12h4M7 15h5" stroke="#06d6a0" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="brand-name">LuckApi</span>
        </div>
        <span class="brand-version">网关 v3.0</span>
      </div>

      <div class="sidebar-nav">
        <el-menu
          :default-active="$route.path"
          router
          class="nav-menu"
        >
          <div class="nav-section-label">管理</div>
          <el-menu-item index="/users" class="nav-item">
            <el-icon class="nav-icon"><User /></el-icon>
            <span class="nav-label">用户管理</span>
            <span class="nav-indicator" v-if="$route.path === '/users'" />
          </el-menu-item>
          <el-menu-item index="/models" class="nav-item">
            <el-icon class="nav-icon"><Cpu /></el-icon>
            <span class="nav-label">模型管理</span>
            <span class="nav-indicator" v-if="$route.path === '/models'" />
          </el-menu-item>
          <el-menu-item index="/groups" class="nav-item">
            <el-icon class="nav-icon"><Connection /></el-icon>
            <span class="nav-label">分组管理</span>
            <span class="nav-indicator" v-if="$route.path === '/groups'" />
          </el-menu-item>
          <el-menu-item index="/qa-records" class="nav-item">
            <el-icon class="nav-icon"><ChatLineSquare /></el-icon>
            <span class="nav-label">Q&A 记录</span>
            <span class="nav-indicator" v-if="$route.path === '/qa-records'" />
          </el-menu-item>
        </el-menu>
      </div>

      <div style="flex:1" />

      <div class="sidebar-status">
        <div class="status-dot active" />
        <span class="status-text">系统在线</span>
      </div>
    </el-aside>

    <el-container class="main-container">
      <el-header class="main-header">
        <div class="header-left">
          <h2 class="header-title">{{ pageTitle }}</h2>
          <el-text class="header-sub" type="info">管理面板</el-text>
        </div>
        <div class="header-right">
          <el-button @click="handleLogout" class="btn-logout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <div class="content-trim">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, SwitchButton, Cpu, Connection, ChatLineSquare } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const pageTitle = computed(() => {
  if (route.path === '/users') return '用户管理'
  if (route.path === '/models') return '模型管理'
  if (route.path === '/groups') return '分组管理'
  if (route.path === '/qa-records') return 'Q&A 记录'
  return '管理面板'
})

async function handleLogout() {
  try { await authApi.logout() }
  finally {
    authStore.clearUser()
    localStorage.removeItem('token')
    router.push({ name: 'Login' })
  }
}
</script>

<style scoped>
.app-root {
  height: 100vh;
  display: flex;
  position: relative;
  background: #04070f;
  overflow: hidden;
}

.bg-grid {
  position: fixed;
  inset: 0;
  background-image: radial-gradient(rgba(6, 214, 160, 0.06) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
  z-index: 0;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, rgba(20, 27, 63, 0.9) 0%, rgba(12, 18, 42, 0.95) 100%);
  border-right: 1px solid rgba(6, 214, 160, 0.08);
  display: flex;
  flex-direction: column;
  padding: 24px 0;
  z-index: 10;
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}

.sidebar-brand {
  padding: 0 24px 28px;
  border-bottom: 1px solid rgba(6, 214, 160, 0.06);
  margin-bottom: 8px;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: -0.02em;
}

.brand-version {
  display: block;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.4);
  margin-top: 6px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #334155;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  padding: 0 24px 8px;
}

.nav-menu {
  border: none !important;
  background: transparent !important;
}

.nav-item {
  border-radius: 0 !important;
  margin: 2px 12px;
  padding: 10px 16px !important;
  position: relative;
}

.nav-menu :deep(.nav-icon) {
  font-size: 18px;
  color: #64748b;
  transition: color 0.2s;
}

.nav-menu :deep(.nav-label) {
  font-size: 14px;
  color: #94a3b8;
  transition: color 0.2s;
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #06d6a0;
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 12px rgba(6, 214, 160, 0.4);
}

.nav-item:hover :deep(.nav-icon),
.nav-item:hover :deep(.nav-label) {
  color: #e2e8f0;
}
.nav-item:hover {
  background: rgba(6, 214, 160, 0.03) !important;
}

.el-menu-item.is-active :deep(.nav-icon),
.el-menu-item.is-active :deep(.nav-label) {
  color: #06d6a0;
}

.sidebar-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid rgba(6, 214, 160, 0.06);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #06d6a0;
}

.status-dot.active {
  box-shadow: 0 0 8px rgba(6, 214, 160, 0.6);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 0.05em;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.main-header {
  height: 64px;
  background: rgba(15, 23, 42, 0.5);
  border-bottom: 1px solid rgba(6, 214, 160, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.header-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #e2e8f0;
  letter-spacing: -0.01em;
}

.header-sub {
  margin-top: 0;
  font-size: 11px;
}

.btn-logout {
  border: 1px solid rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.06);
  color: #f87171;
  border-radius: 8px;
  font-size: 13px;
  padding: 8px 16px;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.35);
}

.btn-logout:active {
  background: rgba(239, 68, 68, 0.2);
}

.main-content {
  flex: 1;
  padding: 0;
  overflow: auto;
  background: transparent;
}

.content-trim {
  padding: 28px 32px;
  max-width: 1400px;
  width: 100%;
}
</style>
