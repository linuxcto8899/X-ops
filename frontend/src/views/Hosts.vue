<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.hosts }}</h2>
      <a-space>
        <a-input-search v-model:value="searchText" placeholder="搜索名称/地址/用户" style="width:240px" @search="load" allow-clear />
        <a-upload :before-upload="importExcel" accept=".xlsx" :show-upload-list="false">
          <a-button>Excel 导入</a-button>
        </a-upload>
        <a-button @click="openGroups">分组管理</a-button>
        <a-button type="primary" @click="openAdd">+ {{ t.add }}</a-button>
      </a-space>
    </div>

    <!-- 分组筛选 -->
    <a-space class="mb16" wrap>
      <a-tag :color="!filterGroup ? 'blue' : ''" style="cursor:pointer" @click="filterGroup=null; load()">全部</a-tag>
      <a-tag v-for="g in groups" :key="g.id" :color="filterGroup===g.id ? 'blue' : ''" style="cursor:pointer" @click="filterGroup=g.id; load()">
        {{ g.name }} ({{ groupCount(g.id) }})
      </a-tag>
    </a-space>

    <a-table :data-source="hosts" row-key="id" :loading="loading" :scroll="{x:1100}">
      <a-table-column title="名称" data-index="name" />
      <a-table-column title="地域" width="90"><template #default="{record}">
        <a-tooltip :title="record.region || '未知地域'">
          <img v-if="flagImg(record)" :src="flagImg(record)" class="flag-img" alt="flag" />
          <span v-else style="color:#999">-</span>
        </a-tooltip>
      </template></a-table-column>
      <a-table-column title="云服务商" width="100"><template #default="{record}">
        {{ providerName(record.cloud_provider) }}
      </template></a-table-column>
      <a-table-column title="分组" width="120"><template #default="{record}">
        <a-space wrap>
          <a-tag v-for="g in record.groups" :key="g">{{ groupName(g) }}</a-tag>
        </a-space>
      </template></a-table-column>
      <a-table-column title="主机地址" data-index="hostname" />
      <a-table-column title="端口" data-index="port" width="70" />
      <a-table-column title="用户" data-index="username" width="100" />
      <a-table-column title="系统" width="180"><template #default="{record}">
        <div v-if="record.os_version">{{ record.os_version }}</div>
        <div v-else-if="record.os_name">{{ record.os_name }} {{ record.os_version }}</div>
        <span v-else style="color:#999">-</span>
      </template></a-table-column>
      <a-table-column title="到期时间" width="120"><template #default="{record}">
        <span :style="expireStyle(record.expire_at)">{{ fmtExpire(record.expire_at) }}</span>
      </template></a-table-column>
      <a-table-column title="状态" width="80"><template #default="{record}">
        <a-tag :color="{online:'green',offline:'red',error:'orange',unknown:'default'}[record.status]">{{ statusLabel(record.status) }}</a-tag>
      </template></a-table-column>
      <a-table-column title="操作" width="280"><template #default="{record}">
        <a-space>
          <a-button size="small" type="primary" ghost @click="openEdit(record)">编辑</a-button>
          <a-button size="small" @click="checkHost(record)">验证</a-button>
          <a-button size="small" @click="openTerminal(record.id)">终端</a-button>
          <a-button size="small" @click="openMonitor(record.id)">监控</a-button>
          <a-popconfirm title="确认删除？" @confirm="remove(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </a-space>
      </template></a-table-column>
    </a-table>

    <!-- 新增/编辑主机 -->
    <a-modal v-model:open="modalOpen" :title="editing ? t.edit : t.add" @ok="save" :confirm-loading="saving"
             :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="主机地址" required><a-input v-model:value="form.hostname" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="端口"><a-input-number v-model:value="form.port" :min="1" :max="65535" style="width:100%" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="用户名" required><a-input v-model:value="form.username" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="密码"><a-input-password v-model:value="form.password" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="私钥"><a-input-password v-model:value="form.private_key" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="分组">
              <a-select v-model:value="form.group_ids" mode="multiple" style="width:100%" placeholder="选择分组">
                <a-select-option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="云服务商">
              <a-select v-model:value="form.cloud_provider" allow-clear style="width:100%">
                <a-select-option v-for="(name, key) in CLOUD_PROVIDERS" :key="key" :value="key">{{ name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="地域">
              <a-input v-model:value="form.region" placeholder="如 cn-hangzhou / us-east-1" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="地域国旗代码">
              <a-space>
                <a-input v-model:value="form.region_code" maxlength="2" placeholder="ISO 国家代码" style="width:150px" />
                <span style="font-size:24px">{{ countryFlag(form.region_code) }}</span>
              </a-space>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="到期时间">
              <a-date-picker show-time v-model:value="form.expire_at" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 分组管理 -->
    <a-modal v-model:open="groupsModal" title="分组管理" :footer="null" width="480">
      <div class="mb16">
        <a-input-group compact>
          <a-input v-model:value="newGroup" placeholder="新分组名称" style="width:70%" />
          <a-button type="primary" @click="addGroup">新增</a-button>
        </a-input-group>
      </div>
      <a-table :data-source="groups" row-key="id" size="small" :pagination="false">
        <a-table-column title="名称" data-index="name" />
        <a-table-column title="主机数" width="80"><template #default="{record}">{{ groupCount(record.id) }}</template></a-table-column>
        <a-table-column title="操作" width="80"><template #default="{record}">
          <a-popconfirm title="确认删除分组？" @confirm="delGroup(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </template></a-table-column>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'
import { countryFlag, regionToFlag, regionFlagImg, CLOUD_PROVIDERS } from '../flags'

const store = useAppStore()
const router = useRouter()
const t = computed(() => locales[store.lang])
const hosts = ref([])
const groups = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const groupsModal = ref(false)
const newGroup = ref('')
const filterGroup = ref(null)
const searchText = ref('')
const form = ref({})

// 弹窗自适应宽度：跟随屏幕宽度，最大 720
const modalW = computed(() => {
  const w = window.innerWidth || 1024
  return Math.min(720, Math.max(420, w - 48))
})

function countryFlag2(c) { return countryFlag(c) }
function regionFlag(rec) { return regionToFlag(rec.region, rec.region_code) }
function flagImg(rec) { return regionFlagImg(rec.region, rec.region_code) }
function providerName(k) { return CLOUD_PROVIDERS[k] || k || '-' }
function groupName(id) { const g = groups.value.find(x => x.id === id); return g ? g.name : id }
function groupCount(id) { return hosts.value.filter(h => (h.groups || []).includes(id)).length }

function fmtExpire(v) { return v ? dayjs(v).format('YYYY-MM-DD') : '-' }
function expireStyle(v) {
  if (!v) return {}
  const days = dayjs(v).diff(dayjs(), 'day')
  if (days < 0) return { color: '#ff4d4f', fontWeight: 'bold' }
  if (days <= 7) return { color: '#faad14', fontWeight: 'bold' }
  return { color: '#52c41a' }
}

async function load() {
  loading.value = true
  try {
    let url = '/hosts/hosts/?page_size=200'
    if (filterGroup.value) url += `&groups=${filterGroup.value}`
    if (searchText.value) url += `&search=${encodeURIComponent(searchText.value)}`
    hosts.value = (await api.get(url)).results || []
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}
async function loadGroups() {
  try { groups.value = (await api.get('/hosts/groups/?page_size=200')).results || [] } catch (e) {}
}
onMounted(() => { load(); loadGroups() })

function statusLabel(s) { return { online: t.value.online, offline: t.value.offline, error: 'Error', unknown: t.value.unknown }[s] || s }

function openAdd() {
  editing.value = false
  form.value = { name: '', hostname: '', port: 22, username: '', password: '', private_key: '',
    group_ids: [], cloud_provider: '', region: '', region_code: '', expire_at: null }
  modalOpen.value = true
}
function openEdit(rec) {
  editing.value = true
  form.value = { ...rec, group_ids: rec.groups || [], expire_at: rec.expire_at ? dayjs(rec.expire_at) : null }
  modalOpen.value = true
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form.value, expire_at: form.value.expire_at ? dayjs(form.value.expire_at).format() : null }
    if (editing.value) await api.patch(`/hosts/hosts/${form.value.id}/`, payload)
    else await api.post('/hosts/hosts/', payload)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}

async function checkHost(record) {
  const r = await api.post(`/hosts/hosts/${record.id}/check/`)
  message[r.ok ? 'success' : 'error'](r.detail || r.status)
  load()
}

async function importExcel(file) {
  const fd = new FormData(); fd.append('file', file)
  const r = await api.post('/hosts/hosts/import_excel/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  message.success(`导入 ${r.created.length} 台`)
  load(); return false
}

async function remove(record) { await api.delete(`/hosts/hosts/${record.id}/`); message.success('OK'); load() }
function openTerminal(id) { router.push(`/terminal/${id}`) }
function openMonitor(id) { router.push(`/host-monitor/${id}`) }

function openGroups() { groupsModal.value = true }
async function addGroup() {
  if (!newGroup.value) return message.warning('请输入分组名称')
  await api.post('/hosts/groups/', { name: newGroup.value })
  newGroup.value = ''; loadGroups(); message.success('OK')
}
async function delGroup(g) { await api.delete(`/hosts/groups/${g.id}/`); loadGroups(); load(); message.success('OK') }
</script>

<style scoped>
.flag-img { width: 28px; height: 20px; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); vertical-align: middle; }
.mb16 { margin-bottom: 16px; }
</style>