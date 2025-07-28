import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '../api/client'

export const useMatchingStore = defineStore('matching', () => {
  const isInQueue = ref(false)
  const joinedAt = ref(null)
  const matchingUsers = ref([])
  const loading = ref(false)
  const websocket = ref(null)
  const currentStatus = ref(null)
  const matchSessionId = ref(null)
  const showMatchConfirm = ref(false)
  const confirmTimeout = ref(null)
  const heartbeatInterval = ref(null)

  const queueCount = computed(() => matchingUsers.value.length)

  // 音效函数
  function playMatchFoundSound() {
    try {
      // 创建简单的提示音
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.value = 800
      oscillator.type = 'sine'

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 1)
    } catch (error) {
      console.log('无法播放音效:', error)
    }
  }

  function connectWebSocket(userId) {
    if (websocket.value) {
      websocket.value.close()
    }

    const wsUrl = `ws://localhost:8000/ws/${userId}`
    websocket.value = new WebSocket(wsUrl)

    websocket.value.onopen = () => {
      console.log('WebSocket连接成功')
      startHeartbeat()
    }

    websocket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (error) {
        console.error('WebSocket消息解析错误:', error)
      }
    }

    websocket.value.onclose = () => {
      console.log('WebSocket连接断开')
      stopHeartbeat()
      // 尝试重连
      setTimeout(() => {
        if (websocket.value?.readyState === WebSocket.CLOSED) {
          connectWebSocket(userId)
        }
      }, 5000)
    }

    websocket.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  }

  function handleWebSocketMessage(data) {
    switch (data.type) {
      case 'matching_update':
        matchingUsers.value = data.data
        break
      case 'match_found':
        handleMatchFound(data.data)
        break
      case 'game_ready':
        handleGameReady(data.data)
        break
      case 'heartbeat':
        // 心跳响应，不需要处理
        break
      default:
        console.log('未知消息类型:', data.type)
    }
  }

  function handleMatchFound(data) {
    matchSessionId.value = data.session_id
    showMatchConfirm.value = true

    // 播放音效
    playMatchFoundSound()

    // 显示浏览器通知
    if (Notification.permission === 'granted') {
      new Notification('找到匹配！', {
        body: '请在30秒内确认匹配',
        icon: '/favicon.ico'
      })
    }

    // 设置超时
    confirmTimeout.value = setTimeout(() => {
      if (showMatchConfirm.value) {
        showMatchConfirm.value = false
        matchSessionId.value = null
      }
    }, data.timeout * 1000)
  }

  function handleGameReady(data) {
    // 进入游戏准备界面
    window.location.href = `/game/${data.game_session_id}`
  }

  function startHeartbeat() {
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
    }

    heartbeatInterval.value = setInterval(() => {
      if (websocket.value?.readyState === WebSocket.OPEN) {
        websocket.value.send(JSON.stringify({ type: 'heartbeat' }))
      }
    }, 1000) // 每1秒发送一次心跳
  }

  function stopHeartbeat() {
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
      heartbeatInterval.value = null
    }
  }

  function disconnectWebSocket() {
    stopHeartbeat()
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
    }
  }

  async function joinQueue() {
    loading.value = true
    try {
      await apiClient.post('/matching/join')
      isInQueue.value = true
      joinedAt.value = new Date().toISOString()
      currentStatus.value = 'waiting'
      return { success: true }
    } catch (error) {
      console.error('Join queue failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '加入队列失败'
      }
    } finally {
      loading.value = false
    }
  }

  async function leaveQueue() {
    loading.value = true
    try {
      await apiClient.post('/matching/leave')
      isInQueue.value = false
      joinedAt.value = null
      currentStatus.value = null
      matchSessionId.value = null
      showMatchConfirm.value = false

      if (confirmTimeout.value) {
        clearTimeout(confirmTimeout.value)
        confirmTimeout.value = null
      }

      return { success: true }
    } catch (error) {
      console.error('Leave queue failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '离开队列失败'
      }
    } finally {
      loading.value = false
    }
  }

  async function confirmMatch(accept) {
    if (!matchSessionId.value) return { success: false, error: '无效的匹配会话' }

    loading.value = true
    try {
      const response = await apiClient.post('/matching/confirm', {
        session_id: matchSessionId.value,
        accept: accept
      })

      if (accept) {
        if (response.data.game_session_id) {
          // 匹配成功，准备进入游戏
          showMatchConfirm.value = false
          matchSessionId.value = null
          isInQueue.value = false

          if (confirmTimeout.value) {
            clearTimeout(confirmTimeout.value)
            confirmTimeout.value = null
          }
        }
      } else {
        // 拒绝匹配
        showMatchConfirm.value = false
        matchSessionId.value = null
        isInQueue.value = false

        if (confirmTimeout.value) {
          clearTimeout(confirmTimeout.value)
          confirmTimeout.value = null
        }
      }

      return { success: true, data: response.data }
    } catch (error) {
      console.error('Confirm match failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '确认匹配失败'
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchMatchingStatus() {
    try {
      const response = await apiClient.get('/matching/status')
      isInQueue.value = response.data.in_queue
      joinedAt.value = response.data.joined_at
      currentStatus.value = response.data.status
      matchSessionId.value = response.data.session_id
    } catch (error) {
      console.error('Fetch matching status failed:', error)
    }
  }

  async function fetchMatchingQueue() {
    try {
      const response = await apiClient.get('/matching/queue')
      matchingUsers.value = response.data
    } catch (error) {
      console.error('Fetch matching queue failed:', error)
    }
  }

  // 请求通知权限
  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission()
    }
  }

  return {
    isInQueue,
    joinedAt,
    matchingUsers,
    loading,
    currentStatus,
    matchSessionId,
    showMatchConfirm,
    queueCount,
    connectWebSocket,
    disconnectWebSocket,
    joinQueue,
    leaveQueue,
    confirmMatch,
    fetchMatchingStatus,
    fetchMatchingQueue,
    requestNotificationPermission
  }
})
