<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.monitor }}</h2>
      <a-button type="primary" @click="openAdd">+ 新建规则</a-button>
    </div>
    <a-table :data-source="rules" row-key="id" :loading="loading">
      <a-table-column title="名称" data-index="name" />
      <a-table-column title="类型" data-index="type" width="100" />
      <a-table-column title="目标" data-index="target" />
      <a-table-column title="间隔(s)" data-index="interval" width="90" />
      <a-table-column title="通知组" width="120"><template #default="{record}">
        <span v-if="groupName(record.notify_group_id)">{{ groupName(record.notify_group_id) }}</span>
        <span v-else style="color:#999">-</span>
      </template></a-table-column>
      <a-table-column title="启用" width="80"><template #default="{record}"><a-tag :color="record.enabled?'green':'default'">{{ record.enabled?'是':'否' }}</a-tag></template></a-table-column>
      <a-table-column title="操作" width="200"><template #default="{record}">
        <a-space>
          <a-button size="small" @click="runRule(record)">测试</a-button>
          <a-button size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </a-space>
      </template></a-table-column>
    </a-table>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑规则' : '新建规则'" @ok="save" :confirm-loading="saving" width="560">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="类型">
          <a-radio-group v-model:value="form.type">
            <a-radio-button value="site">站点</a-radio-button>
            <a-radio-button value="port">端口</a-radio-button>
            <a-radio-button value="ping">Ping</a-radio-button>
            <a-radio-button value="process">进程</a-radio-button>
            <a-radio-button value="script">脚本</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="目标"><a-input v-model:value="form.target" placeholder="URL / 主机 / 进程名 / 命令" /></a-form-item>
        <a-form-item v-if="form.type==='port'" label="端口"><a-input-number v-model:value="form.port" :min="1" :max="65535" /></a-form-item>
        <a-form-item label="执行主机">
          <a-select v-model:value="form.host" allow-clear style="width:100%" placeholder="选择主机（脚本/进程/端口需要）">
            <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="间隔（秒）"><a-input-number v-model:value="form.interval" :min="10" /></a-form-item>
        <a-form-item label="通知组">
          <a-select v-model:value="form.notify_group_id" allow-clear style="width:100%" placeholder="选择报警时通知的通知组">
            <a-select-option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}（{{ (g.contacts||[]).length }} 人）</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="form.enabled" /></a-form-item>
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

const store = useAppStore()
const t = computed(() => locales[store.lang])
const hosts = ref([])
const groups = ref([])
const rules = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  try { groups.value = (await api.get('/monitor/groups/?page_size=200')).results || [] } catch (e) {}
  load()
})
async function load() {
  loading.value = true
  try { rules.value = (await api.get('/monitor/rules/?page_size=200')).results || [] }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function groupName(id) { if (!id) return ''; const g = groups.value.find(x => x.id === id); return g ? g.name : '' }
function openAdd() { editing.value = false; form.value = { name:'', type:'site', target:'', port:null, host:null, interval:60, notify_group_id:null, enabled:true }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/monitor/rules/${form.value.id}/`, form.value)
    else await api.post('/monitor/rules/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function runRule(rec) { const r = await api.post(`/monitor/rules/${rec.id}/run/`); message[r.ok?'success':'error'](r.detail) }
async function del(rec) { await api.delete(`/monitor/rules/${rec.id}/`); message.success('OK'); load() }
</script>
