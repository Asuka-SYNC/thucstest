<template>
  <div class="profile-page">
    <div class="profile-header card">
      <div class="profile-info">
        <img
          :src="authStore.user?.avatar"
          :alt="authStore.user?.username"
          class="profile-avatar"
          @error="handleAvatarError"
        >
        <div class="profile-details">
          <h2>{{ authStore.user?.display_name || authStore.user?.username }}</h2>
          <p class="steam-name" v-if="authStore.user?.display_name !== authStore.user?.username">
            Steam: {{ authStore.user?.username }}
          </p>
          <div class="profile-badges">
            <span v-if="authStore.isSuperAdmin" class="badge badge-danger">超级管理员</span>
            <span v-if="!authStore.user?.permission?.is_banned" class="badge badge-success">正常</span>
            <span v-if="authStore.user?.permission?.is_banned" class="badge badge-warning">已封禁</span>
          </div>
        </div>
      </div>

      <div class="profile-stats">
        <div class="stat-item">
          <span class="stat-label">注册时间</span>
          <span class="stat-value">{{ formatDate(authStore.user?.created_at) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最后登录</span>
          <span class="stat-value">{{ formatDate(authStore.user?.last_login) }}</span>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <div class="info-section card">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>Steam ID</label>
            <span>{{ authStore.user?.steam_id }}</span>
          </div>
          <div class="info-item" v-if="authStore.user?.location">
            <label>地理位置</label>
            <span>{{ authStore.user?.location }}</span>
          </div>
          <div class="info-item" v-if="authStore.user?.website">
            <label>个人网站</label>
            <a :href="authStore.user?.website" target="_blank" class="link">访问网站</a>
          </div>
        </div>
      </div>

      <div v-if="authStore.user?.bio" class="bio-section card">
        <h3>个人简介</h3>
        <p class="bio-text">{{ authStore.user?.bio }}</p>
      </div>

      <div class="actions-section card">
        <h3>快速操作</h3>
        <div class="action-buttons">
          <a
            v-if="authStore.user?.profile_url"
            :href="authStore.user?.profile_url"
            target="_blank"
            class="btn btn-primary"
          >
            查看Steam资料
          </a>
          <a
            v-if="authStore.user?.website"
            :href="authStore.user?.website"
            target="_blank"
            class="btn btn-secondary"
          >
            访问个人网站
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

function formatDate(dateString) {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}
</script>

<style scoped>
.profile-page {
  max-width: 1000px;
  margin: 0 auto;
}

.profile-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-bottom: 2rem;
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.profile-details h2 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 600;
  color: white;
}

.steam-name {
  margin: 0 0 1rem 0;
  opacity: 0.8;
  font-size: 1rem;
}

.profile-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.stat-label {
  display: block;
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: 0.5rem;
}

.stat-value {
  display: block;
  font-size: 1.1rem;
  font-weight: 600;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.info-section {
  grid-column: span 2;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item span {
  font-size: 1rem;
  color: #333;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

.bio-section {
  grid-column: span 2;
}

.bio-text {
  line-height: 1.6;
  color: #555;
  font-size: 1.1rem;
}

.actions-section {
  grid-column: span 2;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .profile-info {
    flex-direction: column;
    text-align: center;
  }

  .profile-content {
    grid-template-columns: 1fr;
  }

  .info-section,
  .bio-section,
  .actions-section {
    grid-column: span 1;
  }

  .profile-stats {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
