<template>
  <div class="first-time-setup">
    <div class="setup-card">
      <div class="welcome-section">
        <img
          :src="authStore.user?.avatar"
          :alt="authStore.user?.username"
          class="user-avatar"
          @error="handleAvatarError"
        >
        <h2>欢迎, {{ authStore.user?.username }}!</h2>
        <p>首次登录需要完善一些个人信息</p>
      </div>

      <form @submit.prevent="handleSubmit" class="setup-form">
        <div class="form-group">
          <label for="display_name">显示名称 *</label>
          <input
            id="display_name"
            v-model="formData.display_name"
            type="text"
            required
            :class="{ 'error': errors.display_name }"
            placeholder="输入您的显示名称"
          >
          <span v-if="errors.display_name" class="error-message">
            {{ errors.display_name }}
          </span>
        </div>

        <div class="form-group">
          <label for="bio">个人简介</label>
          <textarea
            id="bio"
            v-model="formData.bio"
            :class="{ 'error': errors.bio }"
            placeholder="简单介绍一下自己..."
            rows="4"
            maxlength="500"
          ></textarea>
          <div class="char-count">{{ bioCharCount }}/500</div>
          <span v-if="errors.bio" class="error-message">
            {{ errors.bio }}
          </span>
        </div>

        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input
              v-model="formData.is_profile_public"
              type="checkbox"
            >
            <span class="checkmark"></span>
            公开我的资料信息
          </label>
          <p class="checkbox-description">
            勾选后，其他用户可以在用户列表中看到您的信息
          </p>
        </div>

        <div v-if="submitError" class="error-message global-error">
          {{ submitError }}
        </div>

        <div class="form-actions">
          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary"
          >
            {{ loading ? '保存中...' : '完成设置' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const formData = reactive({
  display_name: authStore.user?.username || '',
  bio: '',
  location: '',
  website: '',
  is_profile_public: true
})

const errors = reactive({})
const loading = ref(false)
const submitError = ref('')

const bioCharCount = computed(() => formData.bio?.length || 0)

function validateForm() {
  const newErrors = {}

  // 验证显示名称
  if (!formData.display_name.trim()) {
    newErrors.display_name = '显示名称不能为空'
  } else if (formData.display_name.trim().length < 2) {
    newErrors.display_name = '显示名称至少需要2个字符'
  } else if (formData.display_name.trim().length > 50) {
    newErrors.display_name = '显示名称不能超过50个字符'
  }

  // 验证个人简介
  if (formData.bio && formData.bio.trim().length > 500) {
    newErrors.bio = '个人简介不能超过500个字符'
  }

  // 验证网站URL
  if (formData.website && formData.website.trim()) {
    const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/i
    let url = formData.website.trim()
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url
    }
    if (!urlPattern.test(url)) {
      newErrors.website = '请输入有效的网址'
    }
  }

  // 清除之前的错误
  Object.keys(errors).forEach(key => delete errors[key])

  // 设置新错误
  Object.assign(errors, newErrors)

  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  if (!validateForm()) return

  loading.value = true
  submitError.value = ''

  try {
    const result = await authStore.completeFirstTimeSetup({
      display_name: formData.display_name.trim(),
      bio: formData.bio?.trim() || null,
      website: formData.website?.trim() || null,
      is_profile_public: formData.is_profile_public
    })

    if (!result.success) {
      submitError.value = result.error
    }
  } catch (error) {
    submitError.value = '设置失败，请重试'
  } finally {
    loading.value = false
  }
}

function handleAvatarError(event) {
  event.target.src = 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
}
</script>

<style scoped>
.first-time-setup {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.setup-card {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
}

.welcome-section {
  text-align: center;
  margin-bottom: 2rem;
}

.user-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-bottom: 1rem;
  border: 3px solid #2a5298;
}

.welcome-section h2 {
  color: #2a5298;
  margin-bottom: 0.5rem;
}

.welcome-section p {
  color: #666;
  margin-bottom: 1rem;
}

.setup-form {
  text-align: left;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
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

.form-group input.error,
.form-group textarea.error {
  border-color: #e74c3c;
}

.char-count {
  text-align: right;
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.25rem;
}

.checkbox-group {
  margin-bottom: 2rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0.5rem;
  font-weight: normal;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

.checkbox-description {
  color: #666;
  font-size: 0.9rem;
  margin-left: 1.5rem;
}

.info-note {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
  padding: 1rem;
  margin-bottom: 2rem;
  border-radius: 4px;
}

.info-note p {
  margin: 0;
  color: #1976d2;
}

.error-message {
  color: #e74c3c;
  font-size: 0.9rem;
  margin-top: 0.25rem;
  display: block;
}

.global-error {
  text-align: center;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background-color: #fee;
  border-radius: 8px;
  border: 1px solid #fcc;
}

.form-actions {
  text-align: center;
}

.btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background-color: #2a5298;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1e3c72;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .setup-card {
    padding: 1.5rem;
    margin: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .user-avatar {
    width: 60px;
    height: 60px;
  }
}
</style>
