<template>
  <div class="admin-panel card">
    <h3>管理员面板</h3>

    <div class="admin-tabs">
      <button
        @click="activeTab = 'users'"
        :class="{ active: activeTab === 'users' }"
        class="tab-btn"
      >
        用户管理
      </button>
      <button
        @click="activeTab = 'permissions'"
        :class="{ active: activeTab === 'permissions' }"
        class="tab-btn"
      >
        权限管理
      </button>
    </div>

    <!-- 用户列表标签页 -->
    <div v-if="activeTab === 'users'" class="tab-content">
      <div class="users-header">
        <h4>所有用户</h4>
        <button @click="loadUsers" :disabled="adminStore.loading" class="btn btn-secondary">
          {{ adminStore.loading ? '刷新中...' : '刷新列表' }}
        </button>
      </div>

      <div v-if="adminStore.loading && adminStore.users.length === 0" class="loading">
        加载中...
      </div>

      <div v-else-if="adminStore.users.length === 0" class="empty-state">
        没有找到用户
      </div>

      <div v-else class="users-table">
        <table>
          <thead>
            <tr>
              <th>用户</th>
              <th>权限状态</th>
              <th>最后登录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in adminStore.users" :key="user.id">
              <td class="user-cell">
                <img
                  :src="user.avatar"
                  :alt="user.username"
                  class="user-avatar"
                  @error="handleAvatarError"
                >
                <div class="user-names">
                  <div class="display-name">{{ user.display_name || user.username }}</div>
                  <div class="steam-id">{{ user.steam_id }}</div>
                </div>
              </td>
              <td class="permission-cell">
                <div class="permission-badges">
                  <span v-if="user.permission?.is_super_admin" class="badge admin">管理员</span>
                  <span v-if="user.permission?.is_banned" class="badge banned">已封禁</span>
                  <span v-if="!user.permission?.can_participate_match" class="badge no-match">禁止匹配</span>
                  <span v-if="!user.permission?.is_banned && user.permission?.can_participate_match" class="badge normal">正常</span>
                </div>
              </td>
              <td class="time-cell">
                {{ formatDate(user.last_login) }}
              </td>
              <td class="action-cell">
                <button
                  @click="selectUser(user)"
                  class="btn btn-primary btn-sm"
                  :disabled="user.id === authStore.user?.id"
                >
                  {{ user.id === authStore.user?.id ? '自己' : '管理' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 权限管理标签页 -->
    <div v-if="activeTab === 'permissions'" class="tab-content">
      <div v-if="!selectedUserForPermission" class="select-user-prompt">
        <p>请从用户管理页面选择一个用户来管理权限</p>
      </div>

      <div v-else class="permission-management">
        <div class="selected-user-info">
          <img
            :src="selectedUserForPermission.avatar"
            :alt="selectedUserForPermission.username"
            class="user-avatar-large"
            @error="handleAvatarError"
          >
          <div class="user-details">
            <h4>{{ selectedUserForPermission.display_name || selectedUserForPermission.username }}</h4>
            <p>Steam ID: {{ selectedUserForPermission.steam_id }}</p>
            <p v-if="selectedUserForPermission.is_education_verified">
              学历: {{ selectedUserForPermission.education_level }} - {{ selectedUserForPermission.school_name }}
            </p>
          </div>
        </div>

        <form @submit.prevent="updatePermissions" class="permission-form">
          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="permissionForm.is_banned"
                type="checkbox"
                :disabled="permissionLoading"
              >
              <span class="checkmark"></span>
              封禁用户
            </label>
          </div>

          <div v-if="permissionForm.is_banned" class="ban-details">
            <div class="form-group">
              <label for="ban_reason">封禁原因</label>
              <textarea
                id="ban_reason"
                v-model="permissionForm.banned_reason"
                :disabled="permissionLoading"
                placeholder="请输入封禁原因..."
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="ban_until">封禁到期时间（可选，留空为永久封禁）</label>
              <input
                id="ban_until"
                v-model="permissionForm.banned_until"
                type="datetime-local"
                :disabled="permissionLoading"
              >
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="permissionForm.can_participate_match"
                type="checkbox"
                :disabled="permissionLoading"
              >
              <span class="checkmark"></span>
              允许参加匹配
            </label>
          </div>

          <div v-if="permissionError" class="error-message">
            {{ permissionError }}
          </div>

          <div v-if="permissionSuccess" class="success-message">
            {{ permissionSuccess }}
          </div>

          <div class="form-actions">
            <button
              type="submit"
              :disabled="permissionLoading"
              class="btn btn-primary"
            >
              {{ permissionLoading ? '更新中...' : '更新权限' }}
            </button>
            <button
              type="button"
              @click="resetPermissionForm"
              :disabled="permissionLoading"
              class="btn btn-secondary"
            >
              重置
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useAdminStore } from '../stores/admin'
import { useAuthStore } from '../stores/auth'

const adminStore = useAdminStore()
const authStore = useAuthStore()

const activeTab = ref('users')
const selectedUserForPermission = ref(null)
const permissionLoading = ref(false)
const permissionError = ref('')
const permissionSuccess = ref('')

const permissionForm = reactive({
  is_banned: false,
  banned_reason: '',
  banned_until: '',
  can_participate_match: true
})

async function loadUsers() {
  const result = await adminStore.fetchAllUsers()
  if (!result.success) {
    alert(result.error)
  }
}

function selectUser(user) {
  if (user.id === authStore.user?.id) {
    return
  }

  selectedUserForPermission.value = user
  activeTab.value = 'permissions'
  resetPermissionForm()
}

function resetPermissionForm() {
  if (selectedUserForPermission.value?.permission) {
    const perm = selectedUserForPermission.value.permission
    permissionForm.is_banned = perm.is_banned || false
    permissionForm.banned_reason = perm.banned_reason || ''
    permissionForm.banned_until = perm.banned_until ?
      new Date(perm.banned_until).toISOString().slice(0, 16) : ''
    permissionForm.can_participate_match = perm.can_participate_match !== false
  } else {
    permissionForm.is_banned = false
    permissionForm.banned_reason = ''
    permissionForm.banned_until = ''
    permissionForm.can_participate_match = true
  }

  permissionError.value = ''
  permissionSuccess.value = ''
}

async function updatePermissions() {
  if (!selectedUserForPermission.value) return

  permissionLoading.value = true
  permissionError.value = ''
  permissionSuccess.value = ''

  const updateData = {
    is_banned: permissionForm.is_banned,
    can_participate_match: permissionForm.can_participate_match
  }

  if (permissionForm.is_banned) {
    updateData.banned_reason = permissionForm.banned_reason
    if (permissionForm.banned_until) {
      updateData.banned_until = new Date(permissionForm.banned_until).toISOString()
    }
  }

  try {
    const result = await adminStore.updateUserPermissions(
      selectedUserForPermission.value.id,
      updateData
    )

    if (result.success) {
      permissionSuccess.value = '权限更新成功'
      // 更新本地选中用户信息
      selectedUserForPermission.value = adminStore.selectedUser
      setTimeout(() => permissionSuccess.value = '', 3000)
    } else {
      permissionError.value = result.error
    }
  } catch (error) {
    permissionError.value = '更新失败，请重试'
  } finally {
    permissionLoading.value = false
  }
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}

function formatDate(dateString) {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听封禁状态变化
watch(() => permissionForm.is_banned, (isBanned) => {
  if (!isBanned) {
    permissionForm.banned_reason = ''
    permissionForm.banned_until = ''
  }
})

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-panel {
  margin-bottom: 2rem;
}

.admin-panel h3 {
  color: #2a5298;
  margin-bottom: 2rem;
}

.admin-tabs {
  display: flex;
  border-bottom: 2px solid #e9ecef;
  margin-bottom: 2rem;
}

.tab-btn {
  padding: 1rem 2rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.tab-btn:hover {
  background-color: #f8f9fa;
}

.tab-btn.active {
  color: #2a5298;
  border-bottom-color: #2a5298;
  background-color: #f8f9fa;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.users-header h4 {
  color: #2a5298;
}

.users-table {
  overflow-x: auto;
}

.users-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.users-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #2a5298;
}

.user-cell {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 1rem;
}

.user-names .display-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.user-names .steam-id {
  font-size: 0.8rem;
  color: #666;
}

.education-cell .verified-badge {
  background-color: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
  display: inline-block;
}

.education-detail {
  font-size: 0.9rem;
  color: #666;
}

.not-verified {
  color: #6c757d;
  font-style: italic;
}

.permission-badges {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  text-align: center;
}

.badge.admin {
  background-color: #dc3545;
  color: white;
}

.badge.banned {
  background-color: #6c757d;
  color: white;
}

.badge.no-match {
  background-color: #ffc107;
  color: #212529;
}

.badge.normal {
  background-color: #28a745;
  color: white;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.select-user-prompt {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-style: italic;
}

.selected-user-info {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.user-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-right: 1.5rem;
}

.user-details h4 {
  color: #2a5298;
  margin-bottom: 0.5rem;
}

.user-details p {
  margin: 0.25rem 0;
  color: #666;
}

.permission-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #2a5298;
}

.form-group input:disabled,
.form-group textarea:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.ban-details {
  margin-left: 2rem;
  padding: 1rem;
  background-color: #fff3cd;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.form-actions {
  display: flex;
  gap: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-style: italic;
}

@media (max-width: 768px) {
  .admin-tabs {
    flex-direction: column;
  }

  .tab-btn {
    border-bottom: none;
    border-right: 3px solid transparent;
  }

  .tab-btn.active {
    border-right-color: #2a5298;
    border-bottom-color: transparent;
  }

  .users-header {
    flex-direction: column;
    gap: 1rem;
  }

  .users-table {
    font-size: 0.9rem;
  }

  .user-cell {
    flex-direction: column;
    text-align: center;
  }

  .selected-user-info {
    flex-direction: column;
    text-align: center;
  }

  .user-avatar-large {
    margin-bottom: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
