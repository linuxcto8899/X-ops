<template>
  <div class="stream-page">
    <div class="stream-header">
      <div class="title">
        <img v-if="regionFlag(hostInfo)" :src="regionFlag(hostInfo)" class="flag-img" alt="flag" />
        <span class="hname">{{ hostName }}</span>
        <a-tag :color="connColor" size="small">{{ connText }}</a-tag>
      </div>
      <div class="cmd" v-if="command">$ {{ command }}</div>
    </div>

    <!-- 终端回显区 -->
    <div class="term" ref="termEl" @click="focusInput">
      <div class="term-line" v-for="(line, i) in lines" :key="i">{{ line }}</div>
      <span v-if="connected" class="cursor"></span>
    </div>

    <!-- 交互输入区 -->
    <div class="input-row" v-if="connected">
      <span class="prompt">$</span>
      <input
        ref="inputEl"
        class="cmd-input"
        v-model="inputText"
        placeholder="输入命令，回车执行"
        @keyup.enter="sendCommand"
        @keyup.up="historyUp"
        @keyup.down="historyDown"
      />
      <a-button size="small" type="primary" @click="sendCommand">发送</a-button>
      <a-button size="small" @click="disconnect" danger>断开</a-button>
    </div>

    <div class="stream-footer">
      <span v-if="!connected" style="color:#8b949e">{{ connText }}</span>
      <span v-else style="color:#52c41a">● 已连接，可输入命令交互</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { useAppStore } from '../store'
import { regionFlagImg } from '../flags'

const store = useAppStore()
const route = useRoute()
const executionId = route.params.executionId
const hostId = route.params.hostId

const hostInfo = ref({})
const command = ref('')
const lines = ref([])
const connected = ref(false)
const inputText = ref('')
const inputEl = ref(null)
const termEl = ref(null)
const cmdHistory = ref([])
const histIdx = ref(-1)
let ws = null

const hostName = computed(() => hostInfo.value.name || `主机 ${hostId}`)
const connText = computed(() => connected.value ? '已连接' : '未连接')
const connColor = computed(() => connected.value ? 'green' : 'default')

function regionFlag(h) { return regionFlagImg(h.region, h.region_code) }

const wsUrl = () => {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/terminal/?token=${store.token}`
}

onMounted(async () => {
  // 加载主机信息和执行命令
  try {
    const hosts = (await api.get('/hosts/hosts/?page_size=200')).results || []
    hostInfo.value = hosts.find(h => h.id === Number(hostId)) || {}
    const ex = await api.get(`/exec/executions/${executionId}/`)
    command.value = ex.command
  } catch (e) {}
  connect()
})

onBeforeUnmount(() => { if (ws) ws.close() })

function connect() {
  ws = new WebSocket(wsUrl())
  ws.onopen = () => ws.send(JSON.stringify({ action: 'connect', host_id: Number(hostId) }))
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'connected') {
      connected.value = true
      // 自动执行原始命令
      if (command.value) sendCommand(command.value)
    } else if (msg.type === 'data') {
      appendOutput(msg.data)
    } else if (msg.type === 'error') {
      appendOutput(`\r\n[错误] ${msg.data}`)
    } else if (msg.type === 'close') {
      connected.value = false
    }
  }
  ws.onclose = () => { connected.value = false }
  ws.onerror = () => { connected.value = false }
}

function appendOutput(text) {
  // 追加输出，按行拆分
  const combined = (lines.value.length ? lines.value.join('\n') : '') + text
  lines.value = combined.split('\n')
  scrollToBottom()
}

function sendCommand(cmd) {
  const text = (cmd ?? inputText.value).trim()
  if (!text || !ws || !connected.value) return
  // 回显输入的命令
  appendOutput(`\r\n$ ${text}\r\n`)
  ws.send(JSON.stringify({ action: 'input', data: text + '\r' }))
  if (cmd === undefined) {
    cmdHistory.value.push(text)
    histIdx.value = -1
    inputText.value = ''
  }
  scrollToBottom()
}

function historyUp() {
  if (!cmdHistory.value.length) return
  histIdx.value = histIdx.value < 0 ? cmdHistory.value.length - 1 : Math.max(0, histIdx.value - 1)
  inputText.value = cmdHistory.value[histIdx.value]
}
function historyDown() {
  if (histIdx.value < 0) return
  histIdx.value = Math.min(cmdHistory.value.length - 1, histIdx.value + 1)
  inputText.value = cmdHistory.value[histIdx.value] || ''
}

function focusInput() { inputEl.value?.focus() }
function scrollToBottom() {
  setTimeout(() => { if (termEl.value) termEl.value.scrollTop = termEl.value.scrollHeight }, 50)
}
function disconnect() { if (ws) { ws.send(JSON.stringify({ action: 'close' })); ws.close(); ws = null; connected.value = false } }
</script>

<style scoped>
.stream-page { height: 100vh; display: flex; flex-direction: column; background: #0d1117; color: #e6edf3; }
.stream-header { padding: 12px 16px; border-bottom: 1px solid #30363d; }
.title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
.flag-img { width: 28px; height: 20px; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); vertical-align: middle; }
.cmd { margin-top: 6px; font-family: monospace; font-size: 13px; color: #8b949e; word-break: break-all; }
.term { flex: 1; overflow-y: auto; padding: 12px 16px; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; line-height: 1.5; cursor: text; }
.term-line { white-space: pre-wrap; word-break: break-all; }
.cursor { display: inline-block; width: 8px; height: 16px; background: #58a6ff; animation: blink 1s step-end infinite; vertical-align: text-bottom; }
@keyframes blink { 50% { opacity: 0; } }
.input-row { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-top: 1px solid #30363d; background: #161b22; }
.prompt { color: #52c41a; font-weight: 700; font-family: monospace; }
.cmd-input { flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; padding: 8px 12px; font-family: monospace; outline: none; }
.cmd-input:focus { border-color: #58a6ff; }
.stream-footer { padding: 8px 16px; border-top: 1px solid #30363d; font-size: 13px; }
</style>