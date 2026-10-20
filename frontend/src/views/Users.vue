<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.users }}</h2>
      <a-button type="primary" @click="openAdd">+ 新增用户</a-button>
    </div>
    <a-table :data-source="users" row-key="id" :loading="loading">
      <a-table-column title="用户名" data-index="username" />
      <a-table-column title="角色" data-index="role" width="100" />
      <a-table-column title="邮箱" data-index="email" />
      <a-table-column title="手机" data-index="phone" width="130" />
      <a-table-column title="启用" width="80"><template #default="{record}"><a-tag :color="record.is_active?'green':'default'">{{ record.is_active?'是':'否' }}</a-tag></template></a-table-column>
      <a-table-column title="操作" width="160"><template #default="{record}">
        <a-space>
          <a-button size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </a-space>
      </template></a-table-column>
    </a-table>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑用户' : '新增用户'" @ok="save" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="用户名" required><a-input v-model:value="form.username" /></a-form-item>
        <a-form-item v-if="!editing" label="密码"><a-input-password v-model:value="form.password" /></a-form-item>
        <a-form-item label="邮箱"><a-input v-model:value="form.email" /></a-form-item>
        <a-form-item label="手机"><a-input v-model:value="form.phone" /></a-form-item>
        <a-form-item label="角色">
          <a-radio-group v-model:value="form.role">
            <a-radio-button value="admin">管理员</a-radio-button>
            <a-radio-button value="user">普通用户</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="form.is_active" /></a-form-item>
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
const users = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(load)
async function load() {
  loading.value = true
  try { users.value = (await api.get('/accounts/users/?page_size=200')).results || [] }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { username:'', password:'', email:'', phone:'', role:'user', is_active:true }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/accounts/users/${form.value.id}/`, form.value)
    else await api.post('/accounts/users/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function del(rec) { await api.delete(`/accounts/users/${rec.id}/`); message.success('OK'); load() }
</script>
