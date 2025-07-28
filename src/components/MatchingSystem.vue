<template>
  <div class="matching-system card">
    <h3>匹配系统</h3>

    <div class="matching-controls">
      <div class="status-info">
        <span v-if="!matchingStore.isInQueue" class="status-badge waiting">
          未在队列中
        </span>
        <span v-else class="status-badge active">
          正在匹配中...
        </span>
      </div>

      <div class="control-buttons">
        <button
          v-if="!matchingStore.isInQueue"
          @click="joinQueue"
          :disabled="matchingStore.loading"
          class="btn btn-success"
        >
          {{ matchingStore.loading ? '加入中...' : '开始匹配' }}
        </button>

        <button
          v-else
          @click="leaveQueue"
          :disabled="matchingStore.loading"
          class="btn btn-danger"
        >
          {{ matchingStore.loading ? '退出中...' : '停止匹配' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="success" class="success-message">
      {{ success }}
    </div>

    <div class="queue-info">
      <h4>
        当前队列
        <span class="queue-count">({{ matchingStore.queueCount }}人)</span>
      </h4>

      <div v-if="matchingStore.matchingUsers.length === 0" class="empty-queue">
        当前没有人在匹配队列中
      </div>

      <div v-else class="queue-list">
        <div
          v-for="user in matchingStore.matchingUsers"
          :key="user.user_id"
          class="queue-item"
        >
          <img
            :src="user.avatar"
            :alt="user.display_name"
            class="user-avatar"
            @error="handleAvatarError"
          >
          <div class="user-info">
            <h5>{{ user.display_name }}</h5>
            <p class="education-info" v-if="user.education_level">
              {{ user.education_level }}
              <span v-if="user.school_name"> - {{ user.school_name }}</span>
            </p>
            <p class="join-time">
              {{ formatJoinTime(user.joined_at) }}
            </p>
          </div>
          <div class="status-indicator">
            <span class="status-dot"></span>
            {{ user.status === 'waiting' ? '等待中' : user.status }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useMatchingStore } from '../stores/matching'
import { useAuthStore } from '../stores/auth'

const matchingStore = useMatchingStore()
const authStore = useAuthStore()

const error = ref('')
const success = ref('')

async function joinQueue() {
  error.value = ''
  success.value = ''

  const result = await matchingStore.joinQueue()
  if (result.success) {
    success.value = '已加入匹配队列'
    setTimeout(() => success.value = '', 3000)
  } else {
    error.value = result.error
  }
}

async function leaveQueue() {
  error.value = ''
  success.value = ''

  const result = await matchingStore.leaveQueue()
  if (result.success) {
    success.value = '已离开匹配队列'
    setTimeout(() => success.value = '', 3000)
  } else {
    error.value = result.error
  }
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}

function formatJoinTime(joinTime) {
  const now = new Date()
  const joined = new Date(joinTime)
  const diff = Math.floor((now - joined) / 1000)

  if (diff < 60) {
    return `${diff}秒前加入`
  } else if (diff < 3600) {
    return `${Math.floor(diff / 60)}分钟前加入`
  } else {
    return `${Math.floor(diff / 3600)}小时前加入`
  }
}

onMounted(() => {
  matchingStore.fetchMatchingStatus()
  matchingStore.fetchMatchingQueue()
  // 定时更新队列信息
  const interval = setInterval(() => {
    matchingStore.fetchMatchingQueue()
  }, 30000) // 每30秒更新一次

  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.matching-system {
  margin-bottom: 2rem;
}

.matching-system h3 {
  color: #2a5298;
  margin-bottom: 1.5rem;
}

.matching-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-badge.waiting {
  background-color: #ffc107;
  color: #212529;
}

.status-badge.active {
  background-color: #28a745;
  color: white;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}

.queue-info h4 {
  color: #2a5298;
  margin-bottom: 1rem;
}

.queue-count {
  color: #666;
  font-weight: normal;
}

.empty-queue {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-style: italic;
}

.queue-list {
  max-height: 400px;
  overflow-y: auto;
}

.queue-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.queue-item:hover {
  background-color: #f8f9fa;
}

.queue-item:last-child {
  border-bottom: none;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 1rem;
}

.user-info {
  flex-grow: 1;
}

.user-info h5 {
  margin: 0 0 0.25rem 0;
  color: #2a5298;
}

.education-info {
  color: #666;
  font-size: 0.9rem;
  margin: 0.25rem 0;
}

.join-time {
  color: #999;
  font-size: 0.8rem;
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  color: #28a745;
  font-size: 0.9rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  background-color: #28a745;
  border-radius: 50%;
  margin-right: 0.5rem;
  animation: pulse 2s infinite;
}

@media (max-width: 768px) {
  .matching-controls {
    flex-direction: column;
    gap: 1rem;
  }

  .queue-item {
    flex-direction: column;
    align-items: flex-start;
    text-align: center;
  }

  .user-avatar {
    margin-bottom: 1rem;
  }
}
</style>
