<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.hostMonitor }}</h2>
      <a-space>
        <a-button type="primary" @click="loadAll" :loading="loading">刷新</a-button>
        <a-switch v-model:checked="autoRefresh" checked-children="自动" un-checked-children="手动" @change="toggleAuto" />
      </a-space>
    </div>

    <!-- 所有已加入主机，卡片式显示 -->
    <div class="host-card-grid">
      <a-card v-for="h in hosts" :key="h.id" class="host-card" :bordered="false" hoverable>
        <template #title>
          <div class="card-title">
            <img v-if="regionFlag(h)" :src="regionFlag(h)" class="flag-img" alt="flag" />
            <span class="hname">{{ h.name }}</span>
            <a-tag :color="{online:'green',offline:'red',error:'orange',unknown:'default'}[h.status]" size="small">{{ statusLabel(h.status) }}</a-tag>
          </div>
        </template>
        <template #extra>
          <a-space>
            <a-button size="small" type="link" @click="openDetail(h)">详情</a-button>
            <a-button size="small" type="link" @click="openTerminal(h.id)">终端</a-button>
          </a-space>
        </template>

        <div class="host-info">
          <div class="info-line"><span class="lbl">地址</span>{{ h.hostname }}:{{ h.port }}</div>
          <div class="info-line"><span class="lbl">系统</span>{{ h.os_name }} {{ h.os_version }}</div>
          <div class="info-line"><span class="lbl">云商</span>{{ providerName(h.cloud_provider) }}</div>
          <div class="info-line"><span class="lbl">地域</span>{{ h.region || '-' }} <img v-if="regionFlag(h)" :src="regionFlag(h)" class="flag-img" alt="flag" /></div>
          <div class="info-line"><span class="lbl">到期</span><span :style="expireStyle(h.expire_at)">{{ fmtExpire(h.expire_at) }}</span></div>
        </div>

        <!-- 实时指标小卡片 -->
        <div class="mini-grid">
          <div class="mini-card">
            <div class="mini-label">CPU</div>
            <div class="mini-value" :style="pctColor(metric(h.id,'cpu_percent'))">{{ metric(h.id,'cpu_percent') ?? '-' }}<span class="u">%</span></div>
          </div>
          <div class="mini-card">
            <div class="mini-label">内存</div>
            <div class="mini-value" :style="pctColor(metric(h.id,'memory_percent'))">{{ metric(h.id,'memory_percent') ?? '-' }}<span class="u">%</span></div>
            <div class="mini-sub">{{ fmt(metric(h.id,'memory_used_mb')) }}/{{ fmt(metric(h.id,'memory_total_mb')) }}MB</div>
          </div>
          <div class="mini-card">
            <div class="mini-label">磁盘</div>
            <div class="mini-value" :style="pctColor(metric(h.id,'disk_percent'))">{{ metric(h.id,'disk_percent') ?? '-' }}<span class="u">%</span></div>
            <div class="mini-sub">{{ fmt(metric(h.id,'disk_used_gb')) }}/{{ fmt(metric(h.id,'disk_total_gb')) }}GB</div>
          </div>
          <div class="mini-card">
            <div class="mini-label">负载</div>
            <div class="mini-value" style="font-size:16px">{{ metric(h.id,'load_1m') ?? '-' }}</div>
          </div>
          <div class="mini-card">
            <div class="mini-label">网络↓</div>
            <div class="mini-value" style="font-size:16px; color:#1677ff">{{ fmtBytes(metric(h.id,'network_rx_bytes')) }}</div>
          </div>
          <div class="mini-card">
            <div class="mini-label">网络↑</div>
            <div class="mini-value" style="font-size:16px; color:#52c41a">{{ fmtBytes(metric(h.id,'network_tx_bytes')) }}</div>
          </div>
        </div>
      </a-card>
    </div>

    <a-empty v-if="!loading && !hosts.length" description="暂无已加入的主机" />

    <!-- 详情抽屉：历史曲线 + 进程 -->
    <a-drawer v-model:open="detailOpen" :title="detailHost ? detailHost.name : ''" width="720">
      <template v-if="detailHost">
        <div class="metric-chart"><h3>CPU / 内存 / 磁盘 (%)</h3><div ref="usageChart" style="height:280px"></div></div>
        <div class="metric-chart"><h3>网络流量 (Bytes)</h3><div ref="netChart" style="height:240px"></div></div>
        <div class="metric-chart">
          <h3>{{ t.process }}</h3>
          <a-table :data-source="processes" row-key="pid" size="small" :pagination="{pageSize:15}">
            <a-table-column title="PID" data-index="pid" width="70" />
            <a-table-column title="用户" data-index="user" width="90" />
            <a-table-column title="内存(KB)" data-index="mem_kb" width="100" />
            <a-table-column title="命令" data-index="command" />
          </a-table>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'
import { regionFlagImg, CLOUD_PROVIDERS } from '../flags'

const store = useAppStore()
const router = useRouter()
const t = computed(() => locales[store.lang])
const hosts = ref([])
const metricsMap = ref({})   // hostId -> latest metrics
const loading = ref(false)
const autoRefresh = ref(true)
const detailOpen = ref(false)
const detailHost = ref(null)
const processes = ref([])
const history = ref([])
const usageChart = ref(null)
const netChart = ref(null)
let usageInstance = null
let netInstance = null
let timer = null

function fmt(v) { return v == null ? '-' : Number(v).toFixed(0) }
function fmtBytes(b) { if (b == null) return '-'; const u = ['B','KB','MB','GB','TB']; let i = 0, v = b; while (v > 1024 && i < 4) { v /= 1024; i++ } return v.toFixed(1) + ' ' + u[i] }
function metric(id, key) { return metricsMap.value[id] ? metricsMap.value[id][key] : null }
function pctColor(v) { if (v == null) return {}; if (v > 85) return { color: '#ff4d4f' }; if (v > 60) return { color: '#faad14' }; return { color: '#52c41a' } }
function regionFlag(h) { return regionFlagImg(h.region, h.region_code) }
function providerName(k) { return CLOUD_PROVIDERS[k] || k || '-' }
function statusLabel(s) { return { online: t.value.online, offline: t.value.offline, error: 'Error', unknown: t.value.unknown }[s] || s }
function fmtExpire(v) { return v ? dayjs(v).format('YYYY-MM-DD') : '-' }
function expireStyle(v) {
  if (!v) return {}
  const days = dayjs(v).diff(dayjs(), 'day')
  if (days < 0) return { color: '#ff4d4f', fontWeight: 'bold' }
  if (days <= 7) return { color: '#faad14', fontWeight: 'bold' }
  return { color: '#52c41a' }
}

onMounted(async () => {
  await loadAll()
  timer = setInterval(() => { if (autoRefresh.value) loadAll() }, 30000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer); usageInstance?.dispose(); netInstance?.dispose() })

async function loadAll() {
  loading.value = true
  try {
    hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || []
    // 并行拉取每个主机的实时指标
    const results = await Promise.allSettled(
      hosts.value.map(h => api.get(`/monitor/host/${h.id}/live/`))
    )
    metricsMap.value = {}
    hosts.value.forEach((h, i) => {
      if (results[i].status === 'fulfilled') metricsMap.value[h.id] = results[i].value
    })
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}

function toggleAuto() { if (!autoRefresh.value && timer) clearInterval(timer) }

async function openDetail(h) {
  detailHost.value = h
  detailOpen.value = true
  processes.value = []
  history.value = []
  try {
    const [hist, procs] = await Promise.all([
      api.get(`/monitor/host/${h.id}/history/?limit=60`),
      api.get(`/monitor/host/${h.id}/processes/`),
    ])
    history.value = hist
    processes.value = procs
    renderCharts()
  } catch (e) { message.error(e.message) }
}

function renderCharts() {
  nextTick(() => {
    const times = history.value.map(x => x.time)
    if (usageChart.value) {
      usageInstance = usageInstance || echarts.init(usageChart.value)
      usageInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['CPU','内存','磁盘'] },
        xAxis: { type: 'category', data: times },
        yAxis: { type: 'value', max: 100 },
        series: [
          { name: 'CPU', type: 'line', smooth: true, data: history.value.map(x => x.cpu_percent) },
          { name: '内存', type: 'line', smooth: true, data: history.value.map(x => x.memory_percent) },
          { name: '磁盘', type: 'line', smooth: true, data: history.value.map(x => x.disk_percent) },
        ],
      })
    }
    if (netChart.value) {
      netInstance = netInstance || echarts.init(netChart.value)
      netInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['RX','TX'] },
        xAxis: { type: 'category', data: times },
        yAxis: { type: 'value' },
        series: [
          { name: 'RX', type: 'line', smooth: true, data: history.value.map(x => x.network_rx_bytes) },
          { name: 'TX', type: 'line', smooth: true, data: history.value.map(x => x.network_tx_bytes) },
        ],
      })
    }
  })
}

function openTerminal(id) { router.push(`/terminal/${id}`) }
</script>

<style scoped>
.host-card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.host-card { border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-title { display: flex; align-items: center; gap: 8px; }
.flag-img { width: 28px; height: 20px; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); vertical-align: middle; }
.card-title .hname { font-weight: 600; }
.host-info { margin-bottom: 12px; }
.info-line { font-size: 13px; color: #555; padding: 2px 0; }
.info-line .lbl { display: inline-block; width: 48px; color: #999; }
.mini-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.mini-card { background: #f7f8fa; border-radius: 8px; padding: 10px; text-align: center; }
.mini-label { font-size: 12px; color: #999; }
.mini-value { font-size: 20px; font-weight: 600; }
.mini-value .u { font-size: 12px; color: #999; font-weight: 400; }
.mini-sub { font-size: 11px; color: #aaa; }
</style>