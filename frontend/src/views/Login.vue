<template>
  <div class="login-wrap">
    <div class="login-card">
      <h1>{{ t.appName }}</h1>
      <a-form layout="vertical" @submit.prevent="onLogin">
        <a-form-item :label="t.username">
          <a-input v-model:value="username" size="large" autocomplete="username" />
        </a-form-item>
        <a-form-item :label="t.password">
          <a-input-password v-model:value="password" size="large" autocomplete="current-password" />
        </a-form-item>
        <a-button type="primary" html-type="submit" block size="large" :loading="loading">
          {{ t.login }}
        </a-button>
      </a-form>
      <a-space class="lang-switch">
        <a-button size="small" @click="store.setLang('zh')">中文</a-button>
        <a-button size="small" @click="store.setLang('en')">English</a-button>
      </a-space>
      <div class="copyright">t.me/@linuxcto998 · QQ:5609648</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAppStore } from '../store'
import locales from '../locales'

const store = useAppStore()
const router = useRouter()
const username = ref('admin')
const password = ref('')
const loading = ref(false)
const t = computed(() => locales[store.lang])

async function onLogin() {
  loading.value = true
  try {
    await store.login(username.value, password.value)
    message.success(t.value.login)
    router.push('/dashboard')
  } catch (e) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1677ff 0%, #0b3a8f 100%); }
.login-card { background: #fff; border-radius: 12px; padding: 40px; width: 360px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
.login-card h1 { text-align: center; margin-bottom: 24px; }
.lang-switch { display: flex; justify-content: center; margin-top: 16px; }
.copyright { text-align: center; color: #999; font-size: 12px; margin-top: 16px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
</style>
