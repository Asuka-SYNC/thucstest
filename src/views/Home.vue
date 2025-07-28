<template>
  <div class="home-container">
    <LoginPage v-if="!authStore.isAuthenticated" />
    <FirstTimeSetup v-else-if="authStore.needsFirstTimeSetup" />

    <div v-else class="main-layout">
      <!-- 侧边栏 -->
      <nav class="sidebar">
        <div class="sidebar-header">
          <div class="user-info">
            <img
              :src="authStore.user?.avatar"
              :alt="authStore.user?.username"
              class="user-avatar"
              @error="handleAvatarError"
            >
            <div class="user-details">
              <h3>{{ authStore.user?.display_name || authStore.user?.username }}</h3>
              <p>{{ authStore.user?.steam_id }}</p>
            </div>
          </div>
        </div>

        <div class="sidebar-menu">
          <button
            @click="activeTab = 'matching'"
            :class="{ active: activeTab === 'matching' }"
            class="menu-item"
          >
            <i class="icon">🎮</i>
            <span>匹配系统</span>
            <span v-if="matchingStore.isInQueue" class="status-badge">匹配中</span>
          </button>

          <button
            @click="activeTab = 'profile'"
            :class="{ active: activeTab === 'profile' }"
            class="menu-item"
          >
            <i class="icon">👤</i>
            <span>我的资料</span>
          </button>

          <button
            v-if="authStore.isSuperAdmin"
            @click="activeTab = 'admin'"
            :class="{ active: activeTab === 'admin' }"
            class="menu-item"
          >
            <i class="icon">⚙️</i>
            <span>管理员</span>
          </button>

          <button
            @click="activeTab = 'users'"
            :class="{ active: activeTab === 'users' }"
            class="menu-item"
          >
            <i class="icon">👥</i>
            <span>用户列表</span>
          </button>
        </div>

        <div class="sidebar-footer">
          <button @click="logout" class="logout-btn">
            <i class="icon">🚪</i>
            <span>退出登录</span>
          </button>
        </div>
      </nav>

      <!-- 主要内容区域 -->
      <main class="main-content">
        <div class="content-header">
          <h2>{{ getTabTitle() }}</h2>
          <div class="content-actions">
            <!-- 匹配状态指示器 -->
            <div v-if="matchingStore.isInQueue" class="matching-indicator">
              <div class="pulse-dot"></div>
              <span>正在匹配 ({{ matchingStore.queueCount }}人)</span>
            </div>
          </div>
        </div>

        <div class="content-body">
          <!-- 我的资料 -->
          <div v-if="activeTab === 'profile'" class="tab-content">
            <ProfilePage />
          </div>

          <!-- 匹配系统 -->
          <div v-if="activeTab === 'matching' && authStore.canParticipateMatch" class="tab-content">
            <MatchingSystem />
          </div>

          <!-- 管理员面板 -->
          <div v-if="activeTab === 'admin' && authStore.isSuperAdmin" class="tab-content">
            <AdminPanel />
          </div>

          <!-- 用户列表 -->
          <div v-if="activeTab === 'users'" class="tab-content">
            <UsersList />
          </div>
        </div>
      </main>
    </div>

    <!-- 匹配确认弹窗 -->
    <MatchConfirmModal />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useMatchingStore } from '../stores/matching'
import LoginPage from '../components/LoginPage.vue'
import FirstTimeSetup from '../components/FirstTimeSetup.vue'
import ProfilePage from '../components/ProfilePage.vue'
import MatchingSystem from '../components/MatchingSystem.vue'
import AdminPanel from '../components/AdminPanel.vue'
import UsersList from '../components/UsersList.vue'
import MatchConfirmModal from '../components/MatchConfirmModal.vue'

const authStore = useAuthStore()
const matchingStore = useMatchingStore()

const activeTab = ref('matching')

function getTabTitle() {
  switch (activeTab.value) {
    case 'profile':
      return '我的资料'
    case 'matching':
      return '匹配系统'
    case 'admin':
      return '管理员面板'
    case 'users':
      return '用户列表'
    default:
      return '首页'
  }
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}

function logout() {
  if (confirm('确定要退出登录吗？')) {
    authStore.logout()
  }
}

onMounted(() => {
  // 检查URL中的token参数
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')
  const error = urlParams.get('error')

  if (token) {
    authStore.setToken(token)
    authStore.fetchProfile().then(() => {
      if (authStore.user?.id) {
        matchingStore.connectWebSocket(authStore.user.id)
        matchingStore.fetchMatchingStatus()
        matchingStore.fetchMatchingQueue()
        matchingStore.requestNotificationPermission()
      }
    })
    // 清理URL
    window.history.replaceState({}, document.title, window.location.pathname)
  } else if (error) {
    console.error('Auth error:', error)
    alert('登录失败，请重试')
    // 清理URL
    window.history.replaceState({}, document.title, window.location.pathname)
  } else {
    // 尝试从localStorage加载token
    authStore.loadToken()
    if (authStore.user?.id) {
      matchingStore.connectWebSocket(authStore.user.id)
      matchingStore.fetchMatchingStatus()
      matchingStore.fetchMatchingQueue()
      matchingStore.requestNotificationPermission()
    }
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.main-layout {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.2);
}

.user-details h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.user-details p {
  margin: 0;
  opacity: 0.8;
  font-size: 0.9rem;
}

.sidebar-menu {
  flex: 1;
  padding: 1rem 0;
}

.menu-item {
  width: 100%;
  padding: 1rem 2rem;
  background: none;
  border: none;
  color: white;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.menu-item.active {
  background: rgba(255, 255, 255, 0.2);
}

.menu-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: white;
}

.menu-item .icon {
  font-size: 1.2rem;
}

.menu-item span {
  font-size: 1rem;
  font-weight: 500;
}

.status-badge {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  animation: pulse 2s infinite;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.logout-btn {
  width: 100%;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 主要内容区域样式 */
.main-content {
  flex: 1;
  margin-left: 280px;
  background: white;
  min-height: 100vh;
}

.content-header {
  background: white;
  padding: 2rem;
  border-bottom: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-header h2 {
  margin: 0;
  color: #4c63d2;
  font-size: 1.8rem;
  font-weight: 600;
}

.content-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.matching-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #28a745;
  font-weight: 500;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #28a745;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.content-body {
  padding: 2rem;
  min-height: calc(100vh - 120px);
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    position: relative;
    height: auto;
  }

  .main-content {
    margin-left: 0;
  }

  .main-layout {
    flex-direction: column;
  }

  .sidebar-header {
    padding: 1rem;
  }

  .user-avatar {
    width: 50px;
    height: 50px;
  }

  .content-header {
    padding: 1rem;
  }

  .content-body {
    padding: 1rem;
  }

  .content-header h2 {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .sidebar-menu {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.5rem;
    padding: 1rem;
  }

  .menu-item {
    padding: 1rem;
    text-align: center;
    flex-direction: column;
    gap: 0.5rem;
    border-radius: 8px;
  }

  .menu-item span {
    font-size: 0.9rem;
  }
}
</style>
