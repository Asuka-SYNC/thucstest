<template>
  <div class="game-room">
    <header class="game-header">
      <h1>🎮 游戏准备中</h1>
      <div class="session-info">
        <span class="session-id">房间ID: {{ sessionId }}</span>
        <span class="game-status" :class="gameStatus">{{ statusText }}</span>
      </div>
    </header>

    <div class="game-container">
      <div v-if="loading" class="loading-section">
        <div class="loader"></div>
        <p>正在加载游戏信息...</p>
      </div>

      <div v-else-if="error" class="error-section">
        <div class="error-icon">⚠️</div>
        <h3>加载失败</h3>
        <p>{{ error }}</p>
        <button @click="loadGameData" class="btn btn-primary">重新加载</button>
        <router-link to="/" class="btn btn-secondary">返回首页</router-link>
      </div>

      <div v-else class="game-content">
        <!-- 玩家列表 -->
        <div class="players-section card">
          <h3>玩家列表 ({{ players.length }}/10)</h3>
          <div class="players-grid">
            <div
                v-for="player in players"
                :key="player.id"
                class="player-card"
                :class="{ 'current-player': player.id === authStore.user?.id }"
            >
              <img
                  :src="player.avatar"
                  :alt="player.display_name"
                  class="player-avatar"
                  @error="handleAvatarError"
              >
              <div class="player-info">
                <div class="player-name">{{ player.display_name }}</div>
                <div class="player-steam-id">{{ player.steam_id }}</div>
              </div>
              <div class="player-status">
                <span class="status-dot ready"></span>
                <span class="status-text">就绪</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 游戏设置区域 -->
        <div class="game-settings card">
          <h3>游戏设置</h3>
          <div class="settings-content">
            <div class="setting-item">
              <label>游戏模式</label>
              <div class="setting-value">经典模式</div>
            </div>
            <div class="setting-item">
              <label>地图</label>
              <div class="setting-value">随机地图</div>
            </div>
            <div class="setting-item">
              <label>游戏时长</label>
              <div class="setting-value">30分钟</div>
            </div>
          </div>
        </div>

        <!-- 聊天区域 -->
        <div class="chat-section card">
          <h3>房间聊天</h3>
          <div class="chat-messages">
            <div class="chat-message system">
              <span class="message-time">{{ formatTime(new Date()) }}</span>
              <span class="message-content">所有玩家已就绪，游戏即将开始...</span>
            </div>
          </div>
          <div class="chat-input">
            <input
                v-model="chatMessage"
                @keyup.enter="sendMessage"
                type="text"
                placeholder="输入消息..."
                class="chat-input-field"
            >
            <button @click="sendMessage" class="btn btn-primary btn-sm">发送</button>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="game-controls">
          <div class="ready-section">
            <div class="ready-status">
              <span class="ready-text">所有玩家已准备就绪</span>
              <div class="ready-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: '100%' }"></div>
                </div>
                <span class="progress-text">10/10</span>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <button
                @click="startGame"
                :disabled="!canStart || starting"
                class="btn btn-success btn-large"
            >
              {{ starting ? '启动中...' : '开始游戏' }}
            </button>

            <button
                @click="leaveRoom"
                :disabled="starting"
                class="btn btn-danger"
            >
              离开房间
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useAuthStore} from '../stores/auth'
import {apiClient} from '../api/client'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref('')
const gameData = ref(null)
const players = ref([])
const gameStatus = ref('preparing')
const chatMessage = ref('')
const chatMessages = ref([])
const canStart = ref(true)
const starting = ref(false)

const statusText = computed(() => {
  switch (gameStatus.value) {
    case 'preparing':
      return '准备中'
    case 'ready':
      return '就绪'
    case 'starting':
      return '启动中'
    case 'in_progress':
      return '进行中'
    default:
      return '未知状态'
  }
})

async function loadGameData() {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get(`/game/${props.sessionId}`)
    gameData.value = response.data
    players.value = response.data.players
    gameStatus.value = response.data.status
  } catch (err) {
    console.error('Load game data failed:', err)
    if (err.response?.status === 404) {
      error.value = '游戏房间不存在'
    } else if (err.response?.status === 403) {
      error.value = '您没有权限访问此房间'
    } else {
      error.value = '加载游戏信息失败，请重试'
    }
  } finally {
    loading.value = false
  }
}

async function startGame() {
  starting.value = true
  try {
    // 这里可以添加开始游戏的API调用
    await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟启动过程

    // 游戏开始后的逻辑
    alert('游戏即将开始！')
  } catch (err) {
    console.error('Start game failed:', err)
    alert('启动游戏失败')
  } finally {
    starting.value = false
  }
}

function leaveRoom() {
  if (confirm('确定要离开游戏房间吗？')) {
    router.push('/')
  }
}

function sendMessage() {
  if (!chatMessage.value.trim()) return

  // 这里可以添加发送消息的逻辑
  const message = {
    id: Date.now(),
    player: authStore.user?.display_name || authStore.user?.username,
    content: chatMessage.value.trim(),
    time: new Date()
  }

  chatMessages.value.push(message)
  chatMessage.value = ''
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}

function formatTime(date) {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push('/')
    return
  }

  loadGameData()
})

onUnmounted(() => {
  // 清理资源
})
</script>

<style scoped>
.game-room {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: #333;
}

.game-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 2rem 0;
  text-align: center;
  color: white;
  margin-bottom: 2rem;
}

.game-header h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.session-info {
  display: flex;
  justify-content: center;
  gap: 2rem;
  font-size: 1.1rem;
}

.session-id {
  opacity: 0.9;
}

.game-status {
  padding: 0.25rem 1rem;
  border-radius: 20px;
  font-weight: 600;
}

.game-status.preparing {
  background: rgba(255, 193, 7, 0.8);
  color: #212529;
}

.game-status.ready {
  background: rgba(40, 167, 69, 0.8);
  color: white;
}

.game-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem 2rem;
}

.loading-section,
.error-section {
  text-align: center;
  padding: 4rem 2rem;
}

.loader {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #2a5298;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 2rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-section {
  color: white;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.game-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.card {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.players-section {
  grid-column: span 2;
}

.players-section h3 {
  color: #2a5298;
  margin-bottom: 1.5rem;
  text-align: center;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.player-card {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 10px;
  border: 2px solid transparent;
  transition: all 0.3s;
}

.player-card.current-player {
  border-color: #2a5298;
  background: #e3f2fd;
}

.player-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.player-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 1rem;
}

.player-info {
  flex-grow: 1;
}

.player-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.player-steam-id {
  font-size: 0.8rem;
  color: #666;
}

.player-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.ready {
  background: #28a745;
  animation: pulse 2s infinite;
}

.status-text {
  font-size: 0.9rem;
  color: #28a745;
  font-weight: 600;
}

.game-settings h3,
.chat-section h3 {
  color: #2a5298;
  margin-bottom: 1.5rem;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.setting-item label {
  font-weight: 600;
  color: #495057;
}

.setting-value {
  color: #2a5298;
  font-weight: 500;
}

.chat-messages {
  height: 200px;
  overflow-y: auto;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.chat-message {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border-radius: 6px;
}

.chat-message.system {
  background: #e3f2fd;
  color: #1976d2;
}

.message-time {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-right: 0.5rem;
}

.chat-input {
  display: flex;
  gap: 0.5rem;
}

.chat-input-field {
  flex-grow: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.game-controls {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.ready-section {
  margin-bottom: 2rem;
}

.ready-text {
  font-size: 1.2rem;
  color: #28a745;
  font-weight: 600;
  display: block;
  margin-bottom: 1rem;
}

.ready-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: center;
}

.progress-bar {
  width: 200px;
  height: 10px;
  background: #e9ecef;
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s;
}

.progress-text {
  font-weight: 600;
  color: #28a745;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.2rem;
  font-weight: 600;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .game-content {
    grid-template-columns: 1fr;
  }

  .session-info {
    flex-direction: column;
    gap: 1rem;
  }

  .players-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
