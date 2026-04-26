<template>
  <el-container class="app-root">
    <div class="bg-grid" />

    <!-- Mobile overlay -->
    <div v-if="isMobile && showSidebar" class="sidebar-overlay" @click="closeSidebar" />

    <el-aside :class="['sidebar', { 'sidebar-collapsed': !showSidebar && !isMobile }]" :width="isMobile ? '240px' : ''">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="brand-icon">
            <rect x="2" y="2" width="20" height="20" rx="3" stroke="#8b5cf6" stroke-width="1.5"/>
            <path d="M7 9h6M7 12h4M7 15h5" stroke="#8b5cf6" stroke-width="1.5" stroke-linecap="round"/>
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
          :collapse="!showSidebar && !isMobile"
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
          <el-menu-item index="/concurrency" class="nav-item">
            <el-icon class="nav-icon"><DataAnalysis /></el-icon>
            <span class="nav-label">并发监控</span>
            <span class="nav-indicator" v-if="$route.path === '/concurrency'" />
          </el-menu-item>
        </el-menu>
      </div>

      <div style="flex:1" />

      <div class="sidebar-status">
        <div class="status-dot active" />
        <span class="status-text">系统在线</span>
      </div>
    </el-aside>

    <!-- Mobile toggle -->
    <div class="mobile-toggle" @click="toggleSidebar" v-if="isMobile">
      <el-icon><Fold v-if="showSidebar" /><Expand v-else /></el-icon>
    </div>

    <el-container class="main-container">
      <el-header class="main-header">
        <div class="header-left">
          <div class="header-breadcrumb" v-if="!isMobile">
            <span class="breadcrumb-text">{{ pageTitle }}</span>
            <span class="breadcrumb-sep">/</span>
            <span class="breadcrumb-current">管理面板</span>
          </div>
          <h2 class="header-title" v-if="isMobile">{{ pageTitle }}</h2>
        </div>
        <div class="header-right">
          <el-button @click="handleLogout" class="btn-logout">
            <el-icon><SwitchButton /></el-icon>
            <span class="btn-text">退出</span>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { User, SwitchButton, Cpu, Connection, ChatLineSquare, DataAnalysis, Fold, Expand } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const showSidebar = ref(true)
const isMobile = ref(false)

const pageTitle = computed(() => {
  if (route.path === '/users') return '用户管理'
  if (route.path === '/models') return '模型管理'
  if (route.path === '/groups') return '分组管理'
  if (route.path === '/qa-records') return 'Q&A 记录'
  if (route.path === '/concurrency') return '并发监控'
  return '管理面板'
})

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) showSidebar.value = false
  else showSidebar.value = true
}

function toggleSidebar() {
  showSidebar.value = !showSidebar.value
}

function closeSidebar() {
  showSidebar.value = false
}

async function handleLogout() {
  try { await authApi.logout() }
  finally {
    authStore.clearUser()
    localStorage.removeItem('token')
    router.push({ name: 'Login' })
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.app-root {
  height: 100vh;
  display: flex;
  position: relative;
  background: #0a0816;
  overflow: hidden;
}

.bg-grid {
  position: fixed;
  inset: 0;
  background-image: radial-gradient(rgba(139, 92, 246, 0.06) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
  z-index: 0;
}

/* ==================== MOBILE TOGGLE ==================== */
.mobile-toggle {
  display: none;
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 50;
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  border-radius: 50%;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3);
  cursor: pointer;
  transition: transform 0.2s;
}

.mobile-toggle:hover {
  transform: scale(1.05);
}

.mobile-toggle:active {
  transform: scale(0.95);
}

.mobile-toggle :deep(.el-icon) {
  color: #0a0816;
  font-size: 20px;
}

@media (max-width: 768px) {
  .mobile-toggle { display: flex; }
}

/* ==================== SIDEBAR ==================== */
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, rgba(42, 28, 72, 0.95) 0%, rgba(20, 14, 50, 0.98) 100%);
  border-right: 1px solid rgba(139, 92, 246, 0.08);
  display: flex;
  flex-direction: column;
  padding: 24px 0;
  z-index: 10;
  backdrop-filter: blur(12px);
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.sidebar-collapsed {
  width: 64px;
}

.sidebar-collapsed .brand-name,
.sidebar-collapsed .brand-version,
.sidebar-collapsed .nav-label,
.sidebar-collapsed .nav-section-label,
.sidebar-collapsed .sidebar-status {
  display: none;
}

.sidebar-collapsed .brand-logo {
  justify-content: center;
}

/* Mobile sidebar overlay */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 5;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 15;
  }
  
  .sidebar-overlay {
    display: block;
  }
  
  .sidebar-collapsed {
    transform: translateX(-100%);
  }
}

/* ==================== BRAND ==================== */
.sidebar-brand {
  padding: 0 24px 28px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.06);
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
  color: #f1edf7;
  letter-spacing: -0.02em;
}

.brand-version {
  display: block;
  font-size: 10px;
  color: rgba(196, 181, 208, 0.4);
  margin-top: 6px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

/* ==================== NAV ==================== */
.sidebar-nav {
  flex: 1;
  padding: 8px 0;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #524a75;
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
  color: #a899c0;
  transition: color 0.2s;
}

.nav-menu :deep(.nav-label) {
  font-size: 14px;
  color: #c4b5d0;
  transition: color 0.2s;
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #8b5cf6;
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
}

.nav-item:hover :deep(.nav-icon),
.nav-item:hover :deep(.nav-label) {
  color: #f1edf7;
}

.nav-item:hover {
  background: rgba(139, 92, 246, 0.03) !important;
}

.el-menu-item.is-active :deep(.nav-icon),
.el-menu-item.is-active :deep(.nav-label) {
  color: #8b5cf6;
}

/* ==================== STATUS ==================== */
.sidebar-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid rgba(139, 92, 246, 0.06);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8b5cf6;
}

.status-dot.active {
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 11px;
  color: #a899c0;
  letter-spacing: 0.05em;
}

/* ==================== MAIN CONTENT ==================== */
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
  background: rgba(24, 18, 44, 0.5);
  border-bottom: 1px solid rgba(139, 92, 246, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.breadcrumb-text {
  color: #f1edf7;
  font-weight: 600;
}

.breadcrumb-sep {
  color: #8a7daa;
}

.breadcrumb-current {
  color: #c4b5d0;
}

.header-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #f1edf7;
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

.btn-text {
  display: inline;
}

@media (max-width: 768px) {
  .btn-text { display: none; }
  
  .main-header {
    padding: 0 16px;
    height: 56px;
  }
  
  .header-breadcrumb { display: none; }
  .header-title { font-size: 15px; }
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

@media (max-width: 768px) {
  .content-trim {
    padding: 16px;
  }
}
</style>
