<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.files }}</h2>
      <a-space>
        <a-select v-model:value="selectedHost" style="width:220px" placeholder="选择主机" @change="loadDir">
          <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
        </a-select>
        <a-button @click="goUp">上级</a-button>
        <a-upload :before-upload="upload" :show-upload-list="false"><a-button type="primary">上传</a-button></a-upload>
      </a-space>
    </div>
    <div class="metric-chart">
      <div class="mb16">
        <a-breadcrumb>
          <a-breadcrumb-item><a @click="jumpTo('')">📁 根目录</a></a-breadcrumb-item>
          <a-breadcrumb-item v-for="(seg, i) in pathSegments" :key="i">
            <a @click="jumpTo(seg.fullPath)">{{ seg.name }}</a>
          </a-breadcrumb-item>
        </a-breadcrumb>
      </div>
      <a-table :data-source="items" row-key="name" size="small" :loading="loading">
        <a-table-column title="名称"><template #default="{record}">
          <a @click="openItem(record)">{{ record.is_dir ? '📁 ' : '📄 ' }}{{ record.name }}</a>
        </template></a-table-column>
        <a-table-column title="大小" data-index="size" width="120"><template #default="{record}">{{ record.is_dir ? '-' : fmtSize(record.size) }}</template></a-table-column>
        <a-table-column title="操作" width="160"><template #default="{record}">
          <a-space>
            <a-button v-if="!record.is_dir" size="small" @click="download(record)">下载</a-button>
            <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
          </a-space>
        </template></a-table-column>
      </a-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'

const store = useAppStore()
const t = computed(() => locales[store.lang])
const hosts = ref([])
const selectedHost = ref(null)
const items = ref([])
const currentPath = ref('.')
const loading = ref(false)

function fmtSize(b) { if (b == null) return '-'; const u=['B','KB','MB','GB']; let i=0,v=b; while(v>1024&&i<3){v/=1024;i++} return v.toFixed(1)+' '+u[i] }

// 面包屑路径段：[{name, fullPath}]
const pathSegments = computed(() => {
  if (!currentPath.value || currentPath.value === '/') return []
  const parts = currentPath.value.split('/').filter(Boolean)
  let acc = ''
  return parts.map(p => { acc += '/' + p; return { name: p, fullPath: acc } })
})

function jumpTo(path) {
  currentPath.value = path || '/'
  loadDir()
}

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
})

async function loadDir() {
  if (!selectedHost.value) return
  loading.value = true
  try { items.value = await api.get(`/files/host/${selectedHost.value}/list/?path=${encodeURIComponent(currentPath.value)}`) }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function goUp() { if (currentPath.value !== '/') { currentPath.value = currentPath.value.split('/').slice(0,-1).join('/') || '/'; loadDir() } }
function openItem(rec) { if (rec.is_dir) { currentPath.value = currentPath.value === '/' ? '/' + rec.name : currentPath.value + '/' + rec.name; loadDir() } }
async function download(rec) {
  const url = `/api/files/host/${selectedHost.value}/download/?path=${encodeURIComponent((currentPath.value==='/'?'':currentPath.value)+'/'+rec.name)}`
  const blob = await (await fetch(url, { headers: { Authorization: `Bearer ${store.token}` } })).blob()
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = rec.name; a.click()
}
async function upload(file) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('path', (currentPath.value==='/'?'':currentPath.value)+'/'+file.name)
  await api.post(`/files/host/${selectedHost.value}/upload/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  message.success('上传成功'); loadDir(); return false
}
async function del(rec) {
  const path = (currentPath.value==='/'?'':currentPath.value)+'/'+rec.name
  await api.post(`/files/host/${selectedHost.value}/delete/`, { path })
  message.success('已删除'); loadDir()
}
</script>
