<template>
  <div class="login-section">
    <div class="login-card">
      <h2>欢迎登录</h2>
      <p>请使用您的Steam账号登录</p>

      <a
          :href="steamAuthUrl"
          class="steam-login-btn"
      >
        <img
            src="https://steamcommunity-a.akamaihd.net/public/images/signinthroughsteam/sits_01.png"
            alt="通过Steam登录"
        >
      </a>
    </div>
  </div>
</template>

<script setup>
import { STEAM_AUTH_URL as steamAuthUrl } from '../config'
</script>

<style scoped>
.login-section {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.login-card {
  background: white;
  border-radius: 10px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
}

.login-card h2 {
  color: #2a5298;
  margin-bottom: 1rem;
}

.login-card p {
  margin-bottom: 2rem;
  color: #666;
}

.steam-login-btn {
  display: inline-block;
  transition: transform 0.2s;
}

.steam-login-btn:hover {
  transform: scale(1.05);
}

.steam-login-btn img {
  max-width: 100%;
  height: auto;
}
</style>
