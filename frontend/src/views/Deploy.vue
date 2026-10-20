<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.deploy }}</h2>
      <a-button type="primary" @click="openAdd">+ 新建应用</a-button>
    </div>
    <a-tabs>
      <a-tab-pane key="apps" :tab="'应用'">
        <a-table :data-source="apps" row-key="id" :loading="loading">
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="模式" data-index="mode" width="100" />
          <a-table-column title="仓库" data-index="repo_url" />
          <a-table-column title="目标路径" data-index="target_path" />
          <a-table-column title="灰度" width="90"><template #default="{record}">{{ record.grayscale_enabled ? record.grayscale_percent + '%' : '-' }}</template></a-table-column>
          <a-table-column title="操作" width="160"><template #default="{record}">
            <a-space>
              <a-button size="small" @click="openRelease(record)">发布</a-button>
              <a-button size="small" @click="openEdit(record)">编辑</a-button>
            </a-space>
          </template></a-table-column>
        </a-table>
      </a-tab-pane>
      <a-tab-pane key="releases" :tab="'发布记录'">
        <a-table :data-source="releases" row-key="id" size="small" :pagination="{pageSize:10}">
          <a-table-column title="ID" data-index="id" width="60" />
          <a-table-column title="应用" data-index="app_name" />
          <a-table-column title="版本" data-index="version" />
          <a-table-column title="状态" width="130"><template #default="{record}">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template></a-table-column>
          <a-table-column title="时间" data-index="created_at" />
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑应用' : '新建应用'" @ok="saveApp" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="模式">
          <a-radio-group v-model:value="form.mode">
            <a-radio-button value="normal">常规（构建）</a-radio-button>
            <a-radio-button value="custom">自定义脚本</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <template v-if="form.mode==='normal'">
          <a-form-item label="Git 仓库"><a-input v-model:value="form.repo_url" placeholder="https://..." /></a-form-item>
          <a-form-item label="分支"><a-input v-model:value="form.repo_branch" /></a-form-item>
          <a-form-item label="构建命令"><a-input v-model:value="form.build_command" placeholder="如 npm run build" /></a-form-item>
          <a-form-item label="目标路径"><a-input v-model:value="form.target_path" placeholder="如 /opt/app" /></a-form-item>
        </template>
        <template v-else>
          <a-form-item label="部署脚本"><a-textarea v-model:value="form.deploy_script" :rows="6" /></a-form-item>
        </template>
        <a-form-item label="目标主机">
          <a-select v-model:value="form.host_ids" mode="multiple" style="width:100%">
            <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="灰度发布">
          <a-switch v-model:checked="form.grayscale_enabled" />
          <a-input-number v-if="form.grayscale_enabled" v-model:value="form.grayscale_percent" :min="1" :max="100" style="margin-left:8px" /> %
        </a-form-item>
        <a-form-item label="需要审批">
          <a-switch v-model:checked="form.approval_required" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="releaseModal" title="发起发布" @ok="doRelease" :confirm-loading="releasing" :width="modalW" centered>
      <a-form layout="vertical">
        <a-form-item label="版本"><a-input v-model:value="releaseForm.version" placeholder="如 v1.0.0" /></a-form-item>
        <a-form-item label="定时发布"><a-date-picker show-time v-model:value="releaseForm.schedule_at" style="width:100%" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'
import { useModalWidth } from '../useModalWidth'

const store = useAppStore()
const t = computed(() => locales[store.lang])
const { modalW } = useModalWidth()
const hosts = ref([])
const apps = ref([])
const releases = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const releaseModal = ref(false)
const releasing = ref(false)
const currentApp = ref(null)
const form = ref({})
const releaseForm = ref({})

function statusColor(s) { return { success:'green', failed:'red', running:'blue', pending:'orange', releasing:'blue', 'wait_approval':'purple', rolled_back:'default', cancelled:'default' }[s] || 'default' }

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  load()
})
async function load() {
  loading.value = true
  try {
    apps.value = (await api.get('/deploy/apps/?page_size=200')).results || []
    releases.value = (await api.get('/deploy/releases/?page_size=50')).results || []
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { name:'', mode:'normal', repo_url:'', repo_branch:'main', build_command:'', target_path:'', deploy_script:'', host_ids:[], grayscale_enabled:false, grayscale_percent:100, approval_required:false }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function saveApp() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/deploy/apps/${form.value.id}/`, form.value)
    else await api.post('/deploy/apps/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
function openRelease(rec) { currentApp.value = rec; releaseForm.value = { version:'', schedule_at:null }; releaseModal.value = true }
async function doRelease() {
  releasing.value = true
  try {
    await api.post('/deploy/releases/', {
      app: currentApp.value.id,
      version: releaseForm.value.version,
      schedule_at: releaseForm.value.schedule_at ? dayjs(releaseForm.value.schedule_at).format() : null,
    })
    message.success('已发起发布'); releaseModal.value = false; load()
  } catch (e) { message.error(e.message) } finally { releasing.value = false }
}
</script>
