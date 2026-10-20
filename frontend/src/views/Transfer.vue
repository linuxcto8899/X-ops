<template>
  <div class="page">
    <div class="page-header"><h2>{{ t.transfer }}</h2></div>
    <a-row :gutter="16">
      <a-col :span="12">
        <div class="metric-chart">
          <h3>分发文件</h3>
          <a-form layout="vertical">
            <a-form-item label="类型">
              <a-radio-group v-model:value="form.kind">
                <a-radio-button value="upload">本地上传</a-radio-button>
                <a-radio-button value="remote">远程目录</a-radio-button>
              </a-radio-group>
            </a-form-item>
            <a-form-item v-if="form.kind==='upload'" label="上传文件">
              <a-upload :before-upload="handleUpload" :show-upload-list="false">
                <a-button>选择文件</a-button>
              </a-upload>
              <span v-if="form.uploaded_file">已选：{{ form.uploaded_file }}</span>
            </a-form-item>
            <a-form-item v-else label="源路径（源主机）">
              <a-input v-model:value="form.source_path" placeholder="如 /data/app" />
            </a-form-item>
            <a-form-item label="目标路径">
              <a-input v-model:value="form.target_path" placeholder="如 /opt/app" />
            </a-form-item>
            <a-form-item label="目标主机">
              <a-select v-model:value="form.host_ids" mode="multiple" style="width:100%" placeholder="选择目标主机">
                <a-select-option v-for="h in hosts" :key="h.id" :value="h.id">{{ h.name }}</a-select-option>
              </a-select>
            </a-form-item>
            <a-button type="primary" @click="submit" :loading="submitting">开始分发</a-button>
          </a-form>
        </div>
      </a-col>
      <a-col :span="12">
        <div class="metric-chart">
          <h3>分发记录</h3>
          <a-table :data-source="transfers" row-key="id" size="small" :pagination="{pageSize:8}">
            <a-table-column title="ID" data-index="id" width="60" />
            <a-table-column title="类型" data-index="kind" width="90" />
            <a-table-column title="目标" data-index="target_path" />
            <a-table-column title="状态" width="90"><template #default="{record}">
              <a-tag :color="{running:'blue',success:'green',partial:'orange',failed:'red'}[record.status]">{{ record.status }}</a-tag>
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
const transfers = ref([])
const submitting = ref(false)
const form = ref({ kind: 'upload', uploaded_file: null, source_path: '', target_path: '', host_ids: [] })

onMounted(async () => {
  try { hosts.value = (await api.get('/hosts/hosts/?page_size=200')).results || [] } catch (e) {}
  load()
})
async function load() { try { transfers.value = (await api.get('/files/transfers/')).results || [] } catch (e) {} }
async function handleUpload(file) {
  const fd = new FormData(); fd.append('file', file)
  const r = await api.post('/files/uploads/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  form.value.uploaded_file = r.name
  form.value.upload_id = r.id
  return false
}
async function submit() {
  if (!form.value.host_ids.length) return message.warning('请选择目标主机')
  if (form.value.kind === 'upload' && !form.value.upload_id) return message.warning('请上传文件')
  if (form.value.kind === 'remote' && !form.value.source_path) return message.warning('请输入源路径')
  submitting.value = true
  try {
    await api.post('/files/transfers/', {
      kind: form.value.kind,
      uploaded_file: form.value.upload_id,
      source_path: form.value.source_path,
      target_path: form.value.target_path,
      host_ids: form.value.host_ids,
    })
    message.success('已提交分发'); load()
  } catch (e) { message.error(e.message) } finally { submitting.value = false }
}
</script>
