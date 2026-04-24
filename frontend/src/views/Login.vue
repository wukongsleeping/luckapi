<template>
  <div class="login-page">
    <!-- Left panel: animated brand / circuit board -->
    <div class="panel-brand">
      <div class="brand-inner">
        <div class="brand-content">
          <svg class="logo-icon" viewBox="0 0 64 64" fill="none">
            <rect x="4" y="4" width="56" height="56" rx="6" stroke="url(#logoGrad)" stroke-width="2"/>
            <path d="M18 22h28M18 32h20M18 42h24" stroke="url(#logoGrad)" stroke-width="2" stroke-linecap="round"/>
            <circle cx="50" cy="22" r="3" fill="#06d6a0"/>
            <circle cx="38" cy="32" r="3" fill="#118ab2"/>
            <path d="M30 40l8 8M30 48l16-16" stroke="#06d6a0" stroke-width="2" stroke-linecap="round"/>
            <defs>
              <linearGradient id="logoGrad" x1="4" y1="4" x2="60" y2="60">
                <stop offset="0%" stop-color="#00f5d4"/>
                <stop offset="100%" stop-color="#118ab2"/>
              </linearGradient>
            </defs>
          </svg>

          <h1 class="brand-title">LuckApi</h1>
          <p class="brand-subtitle">OpenAI 代理网关</p>

          <div class="status-metrics">
            <div class="metric">
              <span class="metric-label">认证</span>
              <span class="metric-value offline">已断开</span>
            </div>
            <div class="metric">
              <span class="metric-label">令牌</span>
              <span class="metric-value">JWT 2D</span>
            </div>
            <div class="metric">
              <span class="metric-label">会话</span>
              <span class="metric-value">单设备</span>
            </div>
          </div>

          <div class="scan-h"></div>
        </div>
      </div>
      <div class="grid-overlay"></div>
      <!-- Animated nodes for circuit-board effect -->
      <svg class="circuit-bg" viewBox="0 0 800 600" preserveAspectRatio="none">
        <line class="circuit-line" x1="100" y1="100" x2="300" y2="180" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="300" cy="180" r="3" fill="rgba(0,245,212,0.15)"/>
        <line class="circuit-line" x1="300" y1="180" x2="450" y2="120" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="450" cy="120" r="3" fill="rgba(17,138,178,0.15)"/>
        <line class="circuit-line" x1="300" y1="180" x2="350" y2="300" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="350" cy="300" r="3" fill="rgba(0,245,212,0.1)"/>
        <line class="circuit-line" x1="350" y1="300" x2="550" y2="350" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="550" cy="350" r="3" fill="rgba(17,138,178,0.1)"/>
        <line class="circuit-line" x1="100" y1="100" x2="80" y2="250" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="80" cy="250" r="3" fill="rgba(0,245,212,0.12)"/>
        <line class="circuit-line" x1="80" y1="250" x2="150" y2="380" stroke="rgba(0,245,212,0.06)" stroke-width="1"/>
        <circle cx="150" cy="380" r="3" fill="rgba(0,245,212,0.1)"/>
        <line class="circuit-line" x1="600" y1="500" x2="550" y2="350" stroke="rgba(17,138,178,0.06)" stroke-width="1"/>
        <line class="circuit-line" x1="600" y1="500" x2="700" y2="450" stroke="rgba(17,138,178,0.06)" stroke-width="1"/>
        <circle cx="700" cy="450" r="3" fill="rgba(17,138,178,0.1)"/>
        <line class="circuit-line" x1="700" y1="450" x2="720" y2="300" stroke="rgba(17,138,178,0.06)" stroke-width="1"/>
        <circle cx="720" cy="300" r="3" fill="rgba(17,138,178,0.12)"/>
        <circle class="pulse-node" cx="100" cy="100" r="4" fill="#06d6a0" opacity="0.3"/>
        <circle class="pulse-node2" cx="600" cy="500" r="3" fill="#118ab2" opacity="0.2"/>
      </svg>
    </div>

    <!-- Right: login form -->
    <div class="panel-login">
      <div class="form-container">
        <div class="form-header">
          <h2 class="form-title">登录</h2>
          <p class="form-desc">统一模型访问网关</p>
        </div>

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
                  placeholder="用户名"
              class="input-glow"
              size="large"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
                  placeholder="密码"
              class="input-glow"
              size="large"
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <button
              class="btn-login"
              :disabled="loading"
              @click="handleLogin"
            >
              <span v-if="loading" class="spinner"></span>
              <span v-else>登录</span>
            </button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <span class="footer-text">HTTP/1.1 200 OK</span>
          <span class="footer-meta">LuckApi Proxy v3.0</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth.js'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules = {
  username: [{ required: true, message: '必填', trigger: 'blur' }],
  password: [{ required: true, message: '必填', trigger: 'blur' }],
}

const handleLogin = () => {
  formRef.value.validate(valid => {
    if (valid) {
      loading.value = true
      authApi.login(loginForm.username, loginForm.password)
        .then((res) => {
          authStore.setUser(res.user)
          const query = router.currentRoute.value.query
          router.replace(query.redirect || '/users')
        })
        .catch(() => {
          loading.value = false
        })
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #020617;
  position: relative;
}

/* ==================== LEFT PANEL ==================== */
.panel-brand {
  width: 56%;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}

.brand-inner {
  position: relative;
  z-index: 2;
  padding: 4rem;
  text-align: center;
}

.brand-content {
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.logo-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 2rem;
  animation: float 6s ease-in-out infinite;
  filter: drop-shadow(0 0 24px rgba(0, 245, 212, 0.25));
}

.brand-title {
  font-family: 'Söhne', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 4rem;
  font-weight: 800;
  color: #f0fdfa;
  letter-spacing: -0.03em;
  margin: 0 0 0.5rem;
}

.brand-subtitle {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  color: rgba(6, 214, 160, 0.6);
  font-size: 0.85rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin: 0;
}

.status-metrics {
  margin-top: 4rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
  padding-left: 2.5rem;
  width: 100%;
  max-width: 300px;
  position: relative;
}

.status-metrics::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: linear-gradient(180deg, #06d6a0 0%, rgba(6, 214, 160, 0) 100%);
  border-radius: 1px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
  padding: 0.35rem 0;
}

.metric-label {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.6rem;
  color: rgba(14, 116, 144, 0.6);
  letter-spacing: 0.12em;
  width: 52px;
  text-align: right;
}

.metric-value {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: #06d6a0;
}

.metric-value.offline {
  color: #f59e0b;
}

/* Grid overlay */
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 245, 212, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 245, 212, 0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  animation: gridShift 24s linear infinite;
}

/* Scan line horizontal at bottom of brand panel */
.scan-h {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0, 245, 212, 0.12) 20%,
    rgba(0, 245, 212, 0.35) 50%,
    rgba(0, 245, 212, 0.12) 80%,
    transparent 100%
  );
  animation: scanLineH 4s ease-in-out infinite;
}

/* Circuit background SVG */
.circuit-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.pulse-node {
  animation: nodePulse 4s ease-in-out infinite;
}

.pulse-node2 {
  animation: nodePulse 5s ease-in-out 1s infinite;
}

/* ==================== RIGHT PANEL ==================== */
.panel-login {
  width: 44%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #020813;
}

/* Vertical divider */
.panel-login::before {
  content: '';
  position: absolute;
  top: 0;
  left: -32px;
  width: 1px;
  height: 80%;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(0, 245, 212, 0.15) 15%,
    rgba(0, 245, 212, 0.35) 50%,
    rgba(0, 245, 212, 0.15) 85%,
    transparent 100%
  );
}

.form-container {
  width: 100%;
  max-width: 380px;
  padding: 3rem 2.5rem;
  animation: fadeInUp 0.6s 0.2s cubic-bezier(0.16, 1, 0.3, 1) both;
  position: relative;
  z-index: 2;
}

.form-header {
  margin-bottom: 2.5rem;
}

.form-title {
  font-family: 'Söhne', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #f0fdfa;
  margin: 0 0 0.5rem;
}

.form-desc {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.72rem;
  color: rgba(6, 214, 160, 0.35);
  letter-spacing: 0.05em;
  margin: 0;
}

/* ==================== FORM ==================== */
.login-form {
  margin-top: 1rem;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 1.25rem;
}

.input-glow :deep(.el-input__wrapper) {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(6, 214, 160, 0.08);
  border-radius: 10px;
  padding: 0 1rem;
  box-shadow: none;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.input-glow :deep(.el-input__wrapper:hover) {
  border-color: rgba(6, 214, 160, 0.2);
  background: rgba(15, 23, 42, 0.7);
}

.input-glow :deep(.el-input__wrapper.is-focus) {
  border-color: #06d6a0;
  background: rgba(15, 23, 42, 0.85);
  box-shadow:
    0 0 0 2px rgba(6, 214, 160, 0.15),
    0 0 24px rgba(6, 245, 212, 0.04);
}

.input-glow :deep(.el-input__inner) {
  color: #f0fdfa;
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.88rem;
  caret-color: #06d6a0;
}

.input-glow :deep(.el-input__inner::placeholder) {
  color: rgba(148, 163, 184, 0.25);
}

.input-glow :deep(.el-input__prefix .el-icon) {
  color: rgba(6, 214, 160, 0.35);
  font-size: 1rem;
}

/* Login button: native HTML for full control over hover/glow */
.btn-login {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%);
  border: none;
  border-radius: 10px;
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  color: #020813;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
  margin-top: 0.5rem;
}

.btn-login:not(:disabled):hover {
  background: linear-gradient(135deg, #00f5d4 0%, #1db8ce 100%);
  box-shadow: 0 0 40px rgba(0, 245, 212, 0.15), 0 0 80px rgba(6, 214, 160, 0.06);
  transform: translateY(-1px);
}

.btn-login:not(:disabled):active {
  transform: translateY(0);
  box-shadow: none;
}

.btn-login:disabled {
  background: linear-gradient(135deg, rgba(6, 214, 160, 0.15) 0%, rgba(17, 138, 178, 0.15) 100%);
  cursor: wait;
}

/* Spinner */
.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(2, 8, 19, 0.3);
  border-top-color: #020813;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* Footer */
.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(6, 214, 160, 0.06);
}

.footer-text {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.55rem;
  color: rgba(148, 163, 184, 0.2);
  letter-spacing: 0.05em;
}

.footer-meta {
  font-family: 'Söhne Mono', 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.55rem;
  color: rgba(6, 214, 160, 0.15);
  letter-spacing: 0.05em;
}

/* ==================== KEYFRAMES ==================== */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-8px); }
}

@keyframes gridShift {
  0%   { background-position: 0 0; }
  100% { background-position: 48px 48px; }
}

@keyframes scanLineH {
  0%, 100% { opacity: 0; }
  50%      { opacity: 1; }
}

@keyframes nodePulse {
  0%, 100% { opacity: 0.3; filter: blur(0px); }
  50%      { opacity: 0.8; filter: blur(1px); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
