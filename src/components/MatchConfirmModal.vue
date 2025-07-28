<template>
  <div v-if="matchingStore.showMatchConfirm" class="modal-overlay">
    <div class="match-confirm-modal">
      <div class="modal-header">
        <h2>🎮 找到匹配！</h2>
        <div class="countdown">
          <span class="countdown-number">{{ countdown }}</span>
          <span class="countdown-text">秒</span>
        </div>
      </div>

      <div class="modal-body">
        <div class="match-info">
          <div class="match-status">
            <div class="pulse-animation">
              <div class="pulse-circle"></div>
            </div>
            <p>系统为您找到了一场比赛</p>
            <p class="warning-text">请在倒计时结束前确认</p>
          </div>
        </div>

        <div class="modal-actions">
          <button
            @click="handleConfirm(true)"
            :disabled="loading"
            class="btn btn-accept"
          >
            ✓ 接受匹配
          </button>

          <button
            @click="handleConfirm(false)"
            :disabled="loading"
            class="btn btn-decline"
          >
            ✗ 拒绝
          </button>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useMatchingStore } from '../stores/matching'

const matchingStore = useMatchingStore()

const countdown = ref(30)
const loading = ref(false)
const error = ref('')
const countdownInterval = ref(null)

async function handleConfirm(accept) {
  loading.value = true
  error.value = ''

  try {
    const result = await matchingStore.confirmMatch(accept)

    if (!result.success) {
      error.value = result.error
    } else {
      if (accept) {
        if (result.data.game_session_id) {
          // 匹配成功，跳转到游戏页面
          window.location.href = `/game/${result.data.game_session_id}`
        } else {
          // 等待其他玩家确认
          error.value = `已确认，等待其他玩家 (${result.data.confirmed}/10)`
        }
      }
    }
  } catch (err) {
    error.value = '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

function startCountdown() {
  countdown.value = 30
  countdownInterval.value = setInterval(() => {
    countdown.value--

    if (countdown.value <= 0) {
      // 自动拒绝匹配
      handleConfirm(false)
      stopCountdown()
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value)
    countdownInterval.value = null
  }
}

// 监听匹配确认状态的变化
watch(() => matchingStore.showMatchConfirm, (show) => {
  if (show) {
    startCountdown()
  } else {
    stopCountdown()
  }
})

onMounted(() => {
  if (matchingStore.showMatchConfirm) {
    startCountdown()
  }
})

onUnmounted(() => {
  stopCountdown()
})
</script>

<style scoped>
.match-confirm-modal {
  background: white;
  border-radius: 20px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
  overflow: hidden;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(-50px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  padding: 2rem;
  text-align: center;
  position: relative;
}

.modal-header h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.countdown {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

.countdown-number {
  font-size: 3rem;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 10px;
  min-width: 80px;
  animation: countdownPulse 1s infinite;
}

.countdown-text {
  font-size: 1.2rem;
  opacity: 0.9;
}

@keyframes countdownPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.modal-body {
  padding: 2rem;
}

.match-info {
  text-align: center;
  margin-bottom: 2rem;
}

.match-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.pulse-animation {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pulse-circle {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #28a745, #20c997);
  border-radius: 50%;
  position: relative;
  animation: pulse 2s infinite;
}

.pulse-circle::before,
.pulse-circle::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: inherit;
  opacity: 0.6;
  animation: pulse-ring 2s infinite;
}

.pulse-circle::after {
  animation-delay: 1s;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes pulse-ring {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.6;
  }
  100% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}

.match-status p {
  margin: 0;
  font-size: 1.1rem;
}

.warning-text {
  color: #dc3545;
  font-weight: 600;
  font-size: 1rem !important;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn {
  padding: 1rem 2rem;
  font-size: 1.2rem;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 140px;
}

.btn-accept {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
}

.btn-accept:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
}

.btn-decline {
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
  box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
}

.btn-decline:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  text-align: center;
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  color: #721c24;
}

@media (max-width: 768px) {
  .match-confirm-modal {
    width: 95%;
    margin: 1rem;
  }

  .modal-header h2 {
    font-size: 1.5rem;
  }

  .countdown-number {
    font-size: 2rem;
    min-width: 60px;
  }

  .modal-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
