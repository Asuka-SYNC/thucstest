import axios from 'axios'

export const apiClient = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 10000
})

// 响应拦截器
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token过期，清除本地存储
            localStorage.removeItem('steam_token')
            window.location.reload()
        }
        return Promise.reject(error)
    }
)
