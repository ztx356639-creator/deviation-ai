<template>
  <div class="app">
    <header class="header">
      <div class="header-content">
        <h1>🏭 DeviationAI</h1>
        <div class="status">
          <span :class="['dot', health.ollama === 'connected' ? 'green' : 'red']"></span>
          <span>{{ health.ollama === 'connected' ? 'AI 已连接' : 'AI 未连接' }}</span>
          <span v-if="health.model" class="model">{{ health.model }}</span>
        </div>
      </div>
    </header>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const health = ref({ ollama: 'checking', model: null })

onMounted(async () => {
  try {
    const r = await axios.get('/api/health')
    health.value = r.data
  } catch { health.value.ollama = 'disconnected' }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; }
.app { min-height: 100vh; display: flex; flex-direction: column; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 24px; }
.header-content { max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 22px; font-weight: 700; }
.status { display: flex; align-items: center; gap: 8px; font-size: 13px; background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.green { background: #52c41a; } .dot.red { background: #ff4d4f; }
.model { font-size: 11px; opacity: 0.8; }
.main { flex: 1; padding: 24px; }
</style>