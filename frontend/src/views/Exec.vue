<template>
  <div class="page">
    <div class="page-header"><h2>{{ t.exec }}</h2></div>
    <a-row :gutter="16">
      <a-col :span="14">
        <div class="metric-chart">
          <h3>执行命令</h3>
          <a-form layout="vertical">
            <a-form-item label="语言">
              <a-radio-group v-model:value="form.language">
                <a-radio-button value="shell">Shell</a-radio-button>
                <a-radio-button value="python">Python</a-radio-button>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="选择主机">
              <a-select v-model:value="form.host_ids" mode="multiple" placeholder="选择主机" style="width:100%">
                <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }} ({{ h.hostname }})</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="命令内容">
              <a-textarea v-model:value="form.command" :rows="8" placeholder="输入要执行的命令" />
            </a-form-item>
            <a-button type="primary" @click="run" :loading="running">执行</a-button>
            <span class="hint">执行后每台主机将弹出一个实时回显窗口</span>
          </a-form>
        </div>
      </a-col>
      <a-col :span="10">
        <div class="metric-chart">
          <h3>执行历史</h3>
          <a-table :data-source="history" row-key="id" size="small" :pagination="{pageSize:8}">
            <a-table-column title="ID" data-index="id" width="60" />
            <a-table-column title="语言" data-index="language" width="80" />
            <a-table-column title="状态" width="90"><template #default="{record}">
              <a-tag :color="{running:'blue',success:'green',partial:'orange',failed:'red'}[record.status]">{{ record.status }}</a-tag>
            </template></a-table-column>
            <a-table-column title="时间" data-index="created_at" />
            <a-table-column title="操作" width="90"><template #default="{record}">
              <a-button size="small" @click="openStreams(record)">回显</a-button>
            </template></a-table-column>
          </a-table>
        </div>
      </a-col>
    </a-row>
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
const history = ref([])
const running = ref(false)
const form = ref({ language: 'shell', host_ids: [], command: '' })

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  loadHistory()
})
async function loadHistory() {
  try { history.value = (await api.get('/exec/executions/')).results || [] } catch (e) {}
}
async function run() {
  if (!form.value.command) return message.warning('请输入命令')
  if (!form.value.host_ids.length) return message.warning('请选择主机')
  running.value = true
  try {
    const ex = await api.post('/exec/executions/', form.value)
    message.success('已提交执行')
    // 为每台主机弹出一个实时回显窗口
    openStreams(ex)
    form.value.command = ''
    loadHistory()
  } catch (e) { message.error(e.message) } finally { running.value = false }
}

function openStreams(execution) {
  const hostIds = execution.host_ids || []
  hostIds.forEach((hostId, i) => {
    const url = `/exec-stream/${execution.id}/${hostId}`
    // 延迟打开，避免浏览器拦截多个弹窗
    setTimeout(() => window.open(url, `_blank`), i * 300)
  })
}
</script>

<style scoped>
.hint { margin-left: 12px; color: #999; font-size: 13px; }
</style>