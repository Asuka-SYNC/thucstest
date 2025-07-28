import {defineStore} from 'pinia'
import {ref} from 'vue'
import {apiClient} from '../api/client'

export const useAdminStore = defineStore('admin', () => {
    const users = ref([])
    const selectedUser = ref(null)
    const loading = ref(false)

    async function fetchAllUsers() {
        loading.value = true
        try {
            const response = await apiClient.get('/admin/users')
            users.value = response.data
            return {success: true}
        } catch (error) {
            console.error('Fetch all users failed:', error)
            return {
                success: false,
                error: error.response?.data?.detail || '获取用户列表失败'
            }
        } finally {
            loading.value = false
        }
    }

    async function fetchUser(userId) {
        loading.value = true
        try {
            const response = await apiClient.get(`/admin/users/${userId}`)
            selectedUser.value = response.data
            return {success: true}
        } catch (error) {
            console.error('Fetch user failed:', error)
            return {
                success: false,
                error: error.response?.data?.detail || '获取用户信息失败'
            }
        } finally {
            loading.value = false
        }
    }

    async function updateUserPermissions(userId, permissions) {
        loading.value = true
        try {
            const response = await apiClient.put(`/admin/users/${userId}/permissions`, permissions)

            // 更新本地数据
            const userIndex = users.value.findIndex(u => u.id === userId)
            if (userIndex !== -1) {
                users.value[userIndex] = response.data.user
            }

            if (selectedUser.value?.id === userId) {
                selectedUser.value = response.data.user
            }

            return {success: true}
        } catch (error) {
            console.error('Update permissions failed:', error)
            return {
                success: false,
                error: error.response?.data?.detail || '更新权限失败'
            }
        } finally {
            loading.value = false
        }
    }

    return {
        users,
        selectedUser,
        loading,
        fetchAllUsers,
        fetchUser,
        updateUserPermissions
    }
})
