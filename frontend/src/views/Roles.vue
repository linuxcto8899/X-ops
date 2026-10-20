<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.roles }}</h2>
      <a-button type="primary" @click="openAdd">+ 新增角色</a-button>
    </div>
    <a-table :data-source="roles" row-key="id" :loading="loading">
      <a-table-column title="名称" data-index="name" />
      <a-table-column title="权限" data-index="perms"><template #default="{record}">
        <a-space wrap>
          <a-tag v-for="p in (record.perms||[])" :key="p">{{ p }}</a-tag>
        </a-space>
      </template></a-table-column>
      <a-table-column title="操作" width="160"><template #default="{record}">
        <a-space>
          <a-button size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm title="确认删除？" @confirm="del(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </a-space>
      </template></a-table-column>
    </a-table>

    <a-modal v-model:open="modalOpen" :title="editing ? '编辑角色' : '新增角色'" @ok="save" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="权限">
          <a-checkbox-group v-model:value="form.perms">
            <a-checkbox value="hosts">主机</a-checkbox>
            <a-checkbox value="exec">批量执行</a-checkbox>
            <a-checkbox value="terminal">终端</a-checkbox>
            <a-checkbox value="files">文件</a-checkbox>
            <a-checkbox value="deploy">发布</a-checkbox>
            <a-checkbox value="pipeline">流水线</a-checkbox>
            <a-checkbox value="monitor">监控</a-checkbox>
            <a-checkbox value="scheduler">任务计划</a-checkbox>
            <a-checkbox value="config">配置中心</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
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
const roles = ref([])
const loading = ref(false)
const modalOpen = ref(false)
const editing = ref(false)
const saving = ref(false)
const form = ref({})

onMounted(load)
async function load() {
  loading.value = true
  try { roles.value = (await api.get('/accounts/roles/?page_size=200')).results || [] }
  catch (e) { message.error(e.message) } finally { loading.value = false }
}
function openAdd() { editing.value = false; form.value = { name:'', perms:[] }; modalOpen.value = true }
function openEdit(rec) { editing.value = true; form.value = { ...rec }; modalOpen.value = true }
async function save() {
  saving.value = true
  try {
    if (editing.value) await api.patch(`/accounts/roles/${form.value.id}/`, form.value)
    else await api.post('/accounts/roles/', form.value)
    message.success('OK'); modalOpen.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function del(rec) { await api.delete(`/accounts/roles/${rec.id}/`); message.success('OK'); load() }
</script>
