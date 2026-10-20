<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.configCenter }}</h2>
      <a-button type="primary" @click="openAdd">+ 新增配置</a-button>
    </div>
    <a-row :gutter="16" class="mb16">
      <a-col :span="8"><a-select v-model:value="filterService" placeholder="选择服务" allow-clear style="width:100%" @change="load">
        <a-select-option v-for="s in services" :key="s.id" :value="s.id">{{ s.name }}</a-select-option>
      </a-select></a-col>
      <a-col :span="8"><a-select v-model:value="filterEnv" placeholder="选择环境" allow-clear style="width:100%" @change="load">
        <a-select-option v-for="e in envs" :key="e.id" :value="e.id">{{ e.name }}</a-select-option>
      </a-select></a-col>
    </a-row>
    <div class="metric-chart">
      <a-table :data-source="configs" row-key="id" :loading="loading">
        <a-table-column title="服务" data-index="service_name" width="140" />
        <a-table-column title="环境" data-index="env_name" width="100" />
        <a-table-column title="Key" data-index="key" width="200" />
        <a-table-column title="值" data-index="value" />
        <a-table-column title="视图" data-index="view" width="80" />
        <a-table-column title="操作" width="120"><template #default="{record}">
          <a-space>
            <a-button size="small" @click="openEdit(record)">编辑</a-button>
            <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
          </a-space>
        </template></a-table-column>
      </a-table>
    </div>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑配置' : '新增配置'" @ok="save" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="服务" required>
          <a-select v-model:value="form.service" style="width:100%"><a-select-option v-for="s in services" :key="s.id" :value="s.id">{{ s.name }}</a-select-option></a-select>
        </a-form-item>
        <a-form-item label="环境" required>
          <a-select v-model:value="form.env" style="width:100%"><a-select-option v-for="e in envs" :key="e.id" :value="e.id">{{ e.name }}</a-select-option></a-select>
        </a-form-item>
        <a-form-item label="Key" required><a-input v-model:value="form.key" /></a-form-item>
        <a-form-item label="视图">
          <a-radio-group v-model:value="form.view">
            <a-radio-button value="kv">KV</a-radio-button>
            <a-radio-button value="text">文本</a-radio-button>
            <a-radio-button value="json">JSON</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="值"><a-textarea v-model:value="form.value" :rows="4" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'
import { useModalWidth } from '../useModalWidth'

const store = useAppStore()
const t = computed(() => locales[store.lang])
const { modalW } = useModalWidth()
const services = ref([])
const envs = ref([])
const configs = ref([])
const filterService = ref(null)
const filterEnv = ref(null)
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(async () => {
  try {
    services.value = (await api.get('/config/services/?page_size=200')).results || []
    envs.value = (await api.get('/config/envs/?page_size=200')).results || []
  } catch (e) {}
  load()
})
async function load() {
  loading.value = true
  try {
    let url = '/config/configs/?page_size=200'
    if (filterService.value) url += `&service=${filterService.value}`
    if (filterEnv.value) url += `&env=${filterEnv.value}`
    configs.value = (await api.get(url)).results || []
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { service:null, env:null, key:'', value:'', view:'kv' }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/config/configs/${form.value.id}/`, form.value)
    else await api.post('/config/configs/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function del(rec) { await api.delete(`/config/configs/${rec.id}/`); message.success('OK'); load() }
</script>
