<template>
  <div class="users-section">
    <div class="users-card">
      <h3>已注册用户</h3>

      <div v-if="loading" class="loading">
        <p>加载中...</p>
      </div>

      <div v-else-if="users.length === 0" class="no-users">
        <p>暂无用户注册</p>
      </div>

      <div v-else class="users-list">
        <div
            v-for="user in users"
            :key="user.id"
            class="user-item"
        >
          <img
              :src="user.avatar"
              :alt="user.username"
              class="user-avatar"
              @error="handleAvatarError"
          >
          <div class="user-info">
            <h4>{{ user.username }}</h4>
            <p>Steam ID: {{ user.steam_id }}</p>
            <p>最后登录: {{ formatDate(user.last_login) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {apiClient} from '../api/client'

const users = ref([])
const loading = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const response = await apiClient.get('/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-section {
  margin-top: 2rem;
}

.users-card {
  background: white;
  border-radius: 10px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.users-card h3 {
  color: #2a5298;
  margin-bottom: 1rem;
  text-align: center;
}

.loading, .no-users {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.user-item:last-child {
  border-bottom: none;
}

.user-item:hover {
  background-color: #f8f9fa;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 1rem;
}

.user-info h4 {
  margin: 0 0 0.5rem 0;
  color: #2a5298;
}

.user-info p {
  margin: 0 0 0.25rem 0;
  color: #666;
  font-size: 0.9em;
}
</style>
