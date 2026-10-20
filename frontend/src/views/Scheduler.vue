<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.scheduler }}</h2>
      <a-button type="primary" @click="openAdd">+ 新建任务</a-button>
    </div>
    <a-table :data-source="tasks" row-key="id" :loading="loading">
      <a-table-column title="名称" data-index="name" />
      <a-table-column title="触发方式" data-index="trigger" width="100" />
      <a-table-column title="Cron/间隔" width="120"><template #default="{record}">{{ record.trigger==='cron'?record.cron:(record.trigger==='interval'?record.interval+'s':(record.trigger==='once'?(record.run_at||'').slice(0,16):'监控')) }}</template></a-table-column>
      <a-table-column title="下次执行" data-index="next_run_at" width="170" />
      <a-table-column title="启用" width="80"><template #default="{record}"><a-tag :color="record.enabled?'green':'default'">{{ record.enabled?'是':'否' }}</a-tag></template></a-table-column>
      <a-table-column title="操作" width="200"><template #default="{record}">
        <a-space>
          <a-button size="small" @click="runNow(record)">立即执行</a-button>
          <a-button size="small" @click="openEdit(record)">编辑</a-button>
        </a-space>
      </template></a-table-column>
    </a-table>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑任务' : '新建任务'" @ok="save" :confirm-loading="saving"
             :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item label="任务名称" required><a-input v-model:value="form.name" placeholder="给任务起个名字" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="触发方式" required>
              <a-select v-model:value="form.trigger" style="width:100%">
                <a-select-option value="once">一次性</a-select-option>
                <a-select-option value="cron">Cron 表达式</a-select-option>
                <a-select-option value="interval">固定间隔</a-select-option>
                <a-select-option value="monitor">报警触发</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col v-if="form.trigger==='cron'" :xs="24" :sm="12">
            <a-form-item label="Cron 表达式" required><a-input v-model:value="form.cron" placeholder="分 时 日 月 周，如 0 3 * * *" /></a-form-item>
          </a-col>
          <a-col v-if="form.trigger==='interval'" :xs="24" :sm="12">
            <a-form-item label="间隔（秒）" required><a-input-number v-model:value="form.interval" :min="60" style="width:100%" /></a-form-item>
          </a-col>
          <a-col v-if="form.trigger==='once'" :xs="24" :sm="12">
            <a-form-item label="执行时间" required><a-date-picker show-time v-model:value="form.run_at" style="width:100%" /></a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="执行方式">
              <a-radio-group v-model:value="form.run_local">
                <a-radio-button :value="true">本地</a-radio-button>
                <a-radio-button :value="false">主机</a-radio-button>
              </a-radio-group>
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="启用"><a-switch v-model:checked="form.enabled" checked-children="是" un-checked-children="否" /></a-form-item>
          </a-col>
          <a-col v-if="!form.run_local" :span="24">
            <a-form-item label="目标主机" required>
              <a-select v-model:value="form.host_ids" mode="multiple" style="width:100%" placeholder="选择要执行的主机">
                <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }} ({{ h.hostname }})</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="执行命令" required>
              <a-textarea v-model:value="form.command" :rows="6" placeholder="输入要执行的命令" />
            </a-form-item>
          </a-col>
        </a-row>
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
const tasks = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  load()
})
async function load() {
  loading.value = true
  try { tasks.value = (await api.get('/scheduler/tasks/?page_size=200')).results || [] }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { name:'', trigger:'cron', cron:'', interval:null, run_at:null, command:'', host_ids:[], run_local:false, enabled:true }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec, run_at: rec.run_at ? dayjs(rec.run_at) : null }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    const payload = { ...form.value, run_at: form.value.run_at ? dayjs(form.value.run_at).format() : null }
    if (editing.value) await api.patch(`/scheduler/tasks/${form.value.id}/`, payload)
    else await api.post('/scheduler/tasks/', payload)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function runNow(rec) { await api.post(`/scheduler/tasks/${rec.id}/run_now/`); message.success('已触发') }
</script>
