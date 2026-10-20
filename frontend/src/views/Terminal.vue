<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.terminal }}</h2>
      <a-space>
        <a-select v-model:value="selectedHost" style="width:220px" placeholder="选择主机">
          <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }} ({{ h.hostname }})</a-select-option>
        </a-select>
        <a-button type="primary" @click="connect">连接</a-button>
        <a-button @click="disconnect">断开</a-button>
      </a-space>
    </div>
    <div class="metric-chart">
      <div ref="termEl" style="height:520px; background:#1e1e1e; border-radius:6px; padding:4px"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'

const store = useAppStore()
const t = computed(() => locales[store.lang])
const hosts = ref([])
const selectedHost = ref(null)
const termEl = ref(null)
let term = null
let fit = null
let ws = null

const wsUrl = () => {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/terminal/?token=${store.token}`
}

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  const routeId = window.location.pathname.split('/').pop()
  if (routeId && /^\d+$/.test(routeId)) { selectedHost.value = Number(routeId); connect() }
})

function connect() {
  if (!selectedHost.value) return message.warning('请选择主机')
  if (!term) {
    term = new Terminal({ cursorBlink: true, fontSize: 14, theme: { background: '#1e1e1e' } })
    fit = new FitAddon()
    term.loadAddon(fit)
    term.open(termEl.value)
    fit.fit()
    term.onData(d => ws && ws.send(JSON.stringify({ action: 'input', data: d })))
  }
  term.reset()
  term.writeln('\r\n\x1b[33mConnecting...\x1b[0m\r\n')
  ws = new WebSocket(wsUrl())
  ws.onopen = () => ws.send(JSON.stringify({ action: 'connect', host_id: selectedHost.value }))
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'data') term.write(msg.data)
    else if (msg.type === 'connected') term.writeln('\r\n\x1b[32mConnected.\x1b[0m\r\n')
    else if (msg.type === 'error') { term.writeln(`\r\n\x1b[31m${msg.data}\x1b[0m\r\n`); message.error(msg.data) }
    else if (msg.type === 'close') term.writeln('\r\n\x1b[33mConnection closed.\x1b[0m\r\n')
  }
  ws.onclose = () => term.writeln('\r\n\x1b[31mDisconnected.\x1b[0m\r\n')
}

function disconnect() { if (ws) { ws.send(JSON.stringify({ action: 'close' })); ws.close(); ws = null } }

onBeforeUnmount(() => { disconnect(); term?.dispose() })
</script>
