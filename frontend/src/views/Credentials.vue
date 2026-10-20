<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.credentials }}</h2>
      <a-button type="primary" @click="openAdd">+ 新增凭据</a-button>
    </div>
    <a-table :data-source="creds" row-key="id" :loading="loading">
      <a-table-column title="名称" data-index="name" />
      <a-table-column title="类型" data-index="type" width="100" />
      <a-table-column title="用户名" data-index="username" width="140" />
      <a-table-column title="创建时间" data-index="created_at" width="180" />
      <a-table-column title="操作" width="160"><template #default="{record}">
        <a-space>
          <a-button size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </a-space>
      </template></a-table-column>
    </a-table>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑凭据' : '新增凭据'" @ok="save" :confirm-loading="saving">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="类型">
          <a-radio-group v-model:value="form.type">
            <a-radio-button value="password">密码</a-radio-button>
            <a-radio-button value="key">私钥</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="用户名"><a-input v-model:value="form.username" /></a-form-item>
        <a-form-item v-if="form.type==='password'" label="密码"><a-input-password v-model:value="form.password" /></a-form-item>
        <template v-else>
          <a-form-item label="私钥"><a-textarea v-model:value="form.private_key" :rows="5" /></a-form-item>
          <a-form-item label="私钥密码"><a-input-password v-model:value="form.key_passphrase" /></a-form-item>
        </template>
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
const creds = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(load)
async function load() {
  loading.value = true
  try { creds.value = (await api.get('/hosts/credentials/?page_size=200')).results || [] }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { name:'', type:'password', username:'', password:'', private_key:'', key_passphrase:'' }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/hosts/credentials/${form.value.id}/`, form.value)
    else await api.post('/hosts/credentials/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function del(rec) { await api.delete(`/hosts/credentials/${rec.id}/`); message.success('OK'); load() }
</script>
