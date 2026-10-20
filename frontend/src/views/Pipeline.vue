<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.pipeline }}</h2>
      <a-button type="primary" @click="openAdd">+ 新建流水线</a-button>
    </div>
    <a-tabs>
      <a-tab-pane key="pipelines" :tab="'流水线'">
        <a-table :data-source="pipelines" row-key="id" :loading="loading">
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="描述" data-index="description" />
          <a-table-column title="节点数" width="100"><template #default="{record}">{{ (record.nodes||[]).length }}</template></a-table-column>
          <a-table-column title="启用" width="80"><template #default="{record}"><a-tag :color="record.enabled?'green':'default'">{{ record.enabled?'是':'否' }}</a-tag></template></a-table-column>
          <a-table-column title="操作" width="160"><template #default="{record}">
            <a-space>
              <a-button size="small" type="primary" @click="runPipeline(record)">运行</a-button>
              <a-button size="small" @click="openEdit(record)">编辑</a-button>
            </a-space>
          </template></a-table-column>
        </a-table>
      </a-tab-pane>
      <a-tab-pane key="runs" :tab="'运行记录'">
        <a-table :data-source="runs" row-key="id" size="small" :pagination="{pageSize:10}">
          <a-table-column title="ID" data-index="id" width="60" />
          <a-table-column title="流水线" data-index="pipeline_name" />
          <a-table-column title="状态" width="100"><template #default="{record}">
            <a-tag :color="{running:'blue',success:'green',failed:'red',cancelled:'default'}[record.status]">{{ record.status }}</a-tag>
          </template></a-table-column>
          <a-table-column title="当前节点" data-index="current_node" />
          <a-table-column title="时间" data-index="created_at" />
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑流水线' : '新建流水线'" @ok="save" :confirm-loading="saving" width="720">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="描述"><a-input v-model:value="form.description" /></a-form-item>
        <a-form-item label="节点编排">
          <div v-for="(node, i) in form.nodes" :key="i" style="border:1px solid #eee; border-radius:6px; padding:12px; margin-bottom:8px">
            <div style="display:flex; gap:8px; margin-bottom:8px">
              <a-select v-model:value="node.type" style="width:120px" @change="onTypeChange(node)">
                <a-select-option value="param">参数</a-select-option>
                <a-select-option value="build">构建</a-select-option>
                <a-select-option value="exec">执行</a-select-option>
                <a-select-option value="transfer">传输</a-select-option>
                <a-select-option value="upload">上传</a-select-option>
                <a-select-option value="notify">通知</a-select-option>
              </a-select>
              <a-input v-model:value="node.name" placeholder="节点名称" />
              <a-button size="small" danger @click="form.nodes.splice(i,1)">删除</a-button>
            </div>
            <a-input v-if="node.type==='exec'" v-model:value="node.command" placeholder="命令" />
            <a-input v-if="node.type==='build'" v-model:value="node.command" placeholder="构建命令" />
            <a-input v-if="node.type==='transfer'" v-model:value="node.source" placeholder="源路径" style="margin-bottom:4px" />
            <a-input v-if="node.type==='transfer'" v-model:value="node.target" placeholder="目标路径" />
            <a-input v-if="node.type==='upload'" v-model:value="node.local_path" placeholder="本地文件路径" style="margin-bottom:4px" />
            <a-input v-if="node.type==='upload'" v-model:value="node.target" placeholder="目标路径" />
            <a-input v-if="node.type==='notify'" v-model:value="node.webhook" placeholder="Webhook URL" style="margin-bottom:4px" />
            <a-input v-if="node.type==='notify'" v-model:value="node.content" placeholder="通知内容" />
            <div v-if="node.type==='param'" style="color:#888" v-text="paramHint"></div>
            <div v-if="['exec','transfer','upload'].includes(node.type)" style="margin-top:4px">
              <a-select v-model:value="node.host_ids" mode="multiple" placeholder="目标主机" style="width:100%">
                <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
              </a-select>
            </div>
          </div>
          <a-button block dashed @click="addNode">+ 添加节点</a-button>
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
const pipelines = ref([])
const runs = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})
const paramHint = '参数节点：在运行时注入 {{key}} 占位符'

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  load()
})
async function load() {
  loading.value = true
  try {
    pipelines.value = (await api.get('/pipeline/pipelines/?page_size=200')).results || []
    runs.value = (await api.get('/pipeline/runs/?page_size=50')).results || []
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}
function addNode() { form.value.nodes.push({ type:'exec', name:'', command:'', host_ids:[] }) }
function onTypeChange(node) { node.command = node.source = node.target = node.webhook = node.content = node.local_path = '' }
function openAdd() { editing.value = false; form.value = { name:'', description:'', nodes:[], enabled:true }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = JSON.parse(JSON.stringify(rec)); modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/pipeline/pipelines/${form.value.id}/`, form.value)
    else await api.post('/pipeline/pipelines/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function runPipeline(rec) {
  try {
    const r = await api.post(`/pipeline/pipelines/${rec.id}/run/`, {})
    message.success(r.status === 'success' ? '运行成功' : '运行失败')
    load()
  } catch (e) { message.error(e.message) }
}
</script>
