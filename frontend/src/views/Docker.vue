<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.docker }}</h2>
      <a-space>
        <a-select v-model:value="selectedHost" style="width:220px" placeholder="选择主机" @change="loadAll">
          <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
        </a-select>
        <a-button @click="loadAll">刷新</a-button>
      </a-space>
    </div>

    <template v-if="selectedHost">
      <a-alert v-if="dockerErr" type="error" :message="dockerErr" show-icon style="margin-bottom:16px" />
      <a-tabs v-model:activeKey="tab">
        <!-- 概览 -->
        <a-tab-pane key="overview" :tab="'概览'">
          <a-spin :spinning="loading">
            <a-row :gutter="16" v-if="info?.ok">
              <a-col :span="6"><a-card size="small"><a-statistic title="Docker 版本" :value="info.version||'-'" /></a-card></a-col>
              <a-col :span="6"><a-card size="small"><a-statistic title="镜像" :value="info.images||0" /></a-card></a-col>
              <a-col :span="6"><a-card size="small"><a-statistic title="容器总数" :value="info.containers?.total||0" /></a-card></a-col>
              <a-col :span="6"><a-card size="small"><a-statistic title="运行中" :value="info.containers?.running||0" /></a-card></a-col>
              <a-col :span="6" style="margin-top:16px"><a-card size="small"><a-statistic title="网络" :value="info.networks||0" /></a-card></a-col>
              <a-col :span="6" style="margin-top:16px"><a-card size="small"><a-statistic title="卷" :value="info.volumes||0" /></a-card></a-col>
              <a-col :span="12" style="margin-top:16px">
                <a-card size="small" title="引擎信息">
                  <a-descriptions :column="1" size="small">
                    <a-descriptions-item label="系统">{{ info.engine?.OS||'-' }} / {{ info.engine?.ARCH||'-' }}</a-descriptions-item>
                    <a-descriptions-item label="CPU / 内存">{{ info.engine?.CPU||'-' }} 核 / {{ memGB(info.engine?.MEM) }}</a-descriptions-item>
                  </a-descriptions>
                </a-card>
              </a-col>
            </a-row>
            <a-empty v-else-if="!loading" description="该主机未安装 Docker 或 Docker 服务未运行" />
          </a-spin>
        </a-tab-pane>

        <!-- 容器 -->
        <a-tab-pane key="containers" :tab="'容器'">
          <div class="mb16">
            <a-radio-group v-model:value="containerFilter" @change="loadContainers" size="small">
              <a-radio-button value="all">全部</a-radio-button>
              <a-radio-button value="running">运行中</a-radio-button>
              <a-radio-button value="exited">已停止</a-radio-button>
            </a-radio-group>
          </div>
          <a-table :data-source="containers" row-key="ID" size="small" :loading="loading" :scroll="{x:900}">
            <a-table-column title="容器名" data-index="Names" width="180" />
            <a-table-column title="镜像" data-index="Image" width="200" />
            <a-table-column title="状态" width="110"><template #default="{record}">
              <a-tag :color="stateColor(record.State)">{{ record.Status }}</a-tag>
            </template></a-table-column>
            <a-table-column title="端口" data-index="Ports" ellipsis />
            <a-table-column title="操作" width="280"><template #default="{record}">
              <a-space wrap>
                <a-button v-if="record.State!=='running'" size="small" type="primary" ghost @click="containerAct(record,'start')">启动</a-button>
                <a-button v-if="record.State==='running'" size="small" danger @click="containerAct(record,'stop')">停止</a-button>
                <a-button v-if="record.State==='running'" size="small" @click="containerAct(record,'restart')">重启</a-button>
                <a-button v-if="record.State==='running'" size="small" @click="containerAct(record,'pause')">暂停</a-button>
                <a-button v-if="record.State==='paused'" size="small" @click="containerAct(record,'unpause')">恢复</a-button>
                <a-button size="small" @click="openLogs(record)">日志</a-button>
                <a-popconfirm title="确认删除容器？" @confirm="containerAct(record,'remove')"><a-button size="small" danger>删除</a-button></a-popconfirm>
              </a-space>
            </template></a-table-column>
          </a-table>
        </a-tab-pane>

        <!-- 镜像 -->
        <a-tab-pane key="images" :tab="'镜像'">
          <a-table :data-source="images" row-key="ID" size="small" :loading="loading" :scroll="{x:700}">
            <a-table-column title="仓库" data-index="Repository" width="240" />
            <a-table-column title="标签" data-index="Tag" width="120" />
            <a-table-column title="镜像 ID" data-index="ID" width="100" />
            <a-table-column title="大小" data-index="Size" width="100" />
            <a-table-column title="创建" data-index="CreatedSince" width="120" />
            <a-table-column title="操作" width="100"><template #default="{record}">
              <a-popconfirm title="确认删除镜像？" @confirm="delImage(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
            </template></a-table-column>
          </a-table>
        </a-tab-pane>

        <!-- 网络 -->
        <a-tab-pane key="networks" :tab="'网络'">
          <a-table :data-source="networks" row-key="ID" size="small" :loading="loading">
            <a-table-column title="名称" data-index="Name" />
            <a-table-column title="驱动" data-index="Driver" width="120" />
            <a-table-column title="作用域" data-index="Scope" width="120" />
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </template>
    <a-empty v-else description="请选择主机" />

    <!-- 容器日志弹窗 -->
    <a-modal v-model:open="logModal" :title="`容器日志 - ${logContainer?.Names||''}`" :footer="null" :width="modalW" centered>
      <a-spin :spinning="logLoading">
        <pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:4px;max-height:60vh;overflow:auto;font-size:12px;white-space:pre-wrap;word-break:break-all">{{ logs }}</pre>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'
import { useModalWidth } from '../useModalWidth'

const store = useAppStore()
const t = locales[store.lang]
const { modalW } = useModalWidth(480, 900)

const hosts = ref([])
const selectedHost = ref(null)
const loading = ref(false)
const dockerErr = ref('')
const tab = ref('overview')
const info = ref(null)
const containers = ref([])
const images = ref([])
const networks = ref([])
const containerFilter = ref('all')
const logModal = ref(false)
const logLoading = ref(false)
const logs = ref('')
const logContainer = ref(null)

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
})

function memGB(mem) { if (!mem) return '-'; return (mem / 1024 / 1024 / 1024).toFixed(1) + ' GB' }
function stateColor(s) { return { running: 'green', exited: 'default', paused: 'orange', created: 'blue', dead: 'red' }[s] || 'default' }

async function loadAll() {
  if (!selectedHost.value) return
  dockerErr.value = ''
  loading.value = true
  try {
    info.value = await api.get(`/docker/host/${selectedHost.value}/info/`)
    if (!info.value.ok) { dockerErr.value = info.value.detail || 'Docker 不可用'; loading.value = false; return }
    await Promise.all([loadContainers(), loadImages(), loadNetworks()])
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}
async function loadContainers() {
  if (!selectedHost.value) return
  const all = containerFilter.value !== 'running' && containerFilter.value !== 'exited'
  let list = await api.get(`/docker/host/${selectedHost.value}/containers/?all=${all ? 1 : 0}`)
  if (containerFilter.value === 'running') list = list.filter(c => c.State === 'running')
  if (containerFilter.value === 'exited') list = list.filter(c => c.State === 'exited')
  containers.value = list
}
async function loadImages() { images.value = await api.get(`/docker/host/${selectedHost.value}/images/`) }
async function loadNetworks() { networks.value = await api.get(`/docker/host/${selectedHost.value}/networks/`) }

async function containerAct(rec, action) {
  try {
    const r = await api.post(`/docker/host/${selectedHost.value}/containers/${rec.ID}/${action}/`)
    message.success(r.detail || 'OK')
    loadAll()
  } catch (e) { message.error(e.message) }
}
async function delImage(rec) {
  try {
    const ref = rec.Repository ? `${rec.Repository}${rec.Tag && rec.Tag !== 'latest' ? ':' + rec.Tag : rec.Tag === 'latest' ? ':latest' : ''}` : rec.ID
    const r = await api.post(`/docker/host/${selectedHost.value}/images/${encodeURIComponent(ref)}/remove/`)
    message.success(r.detail || 'OK')
    loadImages()
  } catch (e) { message.error(e.message) }
}
async function openLogs(rec) {
  logContainer.value = rec
  logModal.value = true
  logLoading.value = true
  logs.value = '加载中...'
  try { logs.value = await api.get(`/docker/host/${selectedHost.value}/containers/${rec.ID}/logs/?lines=300`) }
  catch (e) { logs.value = e.message } finally { logLoading.value = false }
}
</script>