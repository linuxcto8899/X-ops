<template>
  <div class="page">
    <div class="page-header"><h2>{{ t.alarm }}</h2></div>
    <a-tabs>
      <a-tab-pane key="channels" :tab="'发信配置'">
        <div class="mb16"><a-button type="primary" @click="openChannel">+ 新增发信配置</a-button></div>
        <a-table :data-source="channels" row-key="id" :loading="loading">
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="类型" data-index="kind_name" width="140" />
          <a-table-column title="启用" width="80"><template #default="{record}">
            <a-tag :color="record.enabled?'green':'default'">{{ record.enabled?'是':'否' }}</a-tag>
          </template></a-table-column>
          <a-table-column title="配置摘要" width="240"><template #default="{record}">
            <span style="font-size:12px;color:#888">{{ configSummary(record) }}</span>
          </template></a-table-column>
          <a-table-column title="操作" width="220"><template #default="{record}">
            <a-space>
              <a-button size="small" type="primary" ghost @click="openTest(record)">测试发送</a-button>
              <a-button size="small" @click="openChannel(record)">编辑</a-button>
              <a-popconfirm title="确认删除？" @confirm="delChannel(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
            </a-space>
          </template></a-table-column>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="alerts" :tab="'告警记录'">
        <a-table :data-source="alerts" row-key="id" :loading="loading">
          <a-table-column title="标题" data-index="title" />
          <a-table-column title="级别" data-index="level" width="100"><template #default="{record}">
            <a-tag :color="{warning:'orange',critical:'red',info:'blue'}[record.level]">{{ record.level }}</a-tag>
          </template></a-table-column>
          <a-table-column title="状态" data-index="status" width="100"><template #default="{record}">
            <a-tag :color="record.status==='firing'?'red':'green'">{{ record.status }}</a-tag>
          </template></a-table-column>
          <a-table-column title="内容" data-index="content" />
          <a-table-column title="时间" data-index="created_at" width="170" />
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="contacts" :tab="'联系人'">
        <div class="mb16"><a-button type="primary" @click="openContact">+ 新增联系人</a-button></div>
        <a-table :data-source="contacts" row-key="id">
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="渠道" data-index="channels"><template #default="{record}">
            <a-space wrap>
              <a-tag v-for="(v,k) in record.channels||{}" :key="k" color="blue">{{ channelLabel(k, v) }}</a-tag>
            </a-space>
          </template></a-table-column>
          <a-table-column title="操作" width="120"><template #default="{record}">
            <a-space>
              <a-button size="small" @click="openContact(record)">编辑</a-button>
              <a-popconfirm title="确认删除？" @confirm="delContact(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
            </a-space>
          </template></a-table-column>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="groups" :tab="'通知组'">
        <div class="mb16"><a-button type="primary" @click="openGroup">+ 新增通知组</a-button></div>
        <a-table :data-source="groups" row-key="id">
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="联系人" data-index="contacts"><template #default="{record}">{{ (record.contacts||[]).length }} 人</template></a-table-column>
          <a-table-column title="操作" width="120"><template #default="{record}">
            <a-space>
              <a-button size="small" @click="openGroup(record)">编辑</a-button>
              <a-popconfirm title="确认删除？" @confirm="delGroup(record)"><a-button size="small" danger>删除</a-button></a-popconfirm>
            </a-space>
          </template></a-table-column>
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <!-- 发信配置弹窗 -->
    <a-modal v-model:open="channelModal" :title="channelForm.id ? '编辑发信配置' : '新增发信配置'" @ok="saveChannel" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="channelForm.name" /></a-form-item>
        <a-form-item label="渠道类型" required>
          <a-select v-model:value="channelForm.kind" style="width:100%">
            <a-select-option v-for="(n, k) in KINDS" :key="k" :value="k">{{ n }}</a-select-option>
          </a-select>
        </a-form-item>

        <!-- SMTP -->
        <template v-if="channelForm.kind==='smtp'">
          <a-form-item label="SMTP 服务器" required><a-input v-model:value="channelForm.config.host" placeholder="如 smtp.qq.com" /></a-form-item>
          <a-row :gutter="12">
            <a-col :span="12"><a-form-item label="端口" required><a-input-number v-model:value="channelForm.config.port" :min="1" :max="65535" style="width:100%" /></a-form-item></a-col>
            <a-col :span="12"><a-form-item label="加密"><a-radio-group v-model:value="channelForm.config.use_ssl"><a-radio-button :value="true">SSL</a-radio-button><a-radio-button :value="false">无/STARTTLS</a-radio-button></a-radio-group></a-form-item></a-col>
          </a-row>
          <a-form-item label="用户名" required><a-input v-model:value="channelForm.config.username" /></a-form-item>
          <a-form-item label="密码/授权码" required><a-input-password v-model:value="channelForm.config.password" /></a-form-item>
          <a-form-item label="发件邮箱" required><a-input v-model:value="channelForm.config.from_email" placeholder="如 ops@qq.com" /></a-form-item>
        </template>

        <!-- Webhook 类 -->
        <template v-if="channelForm.kind==='dingtalk'||channelForm.kind==='qywx'||channelForm.kind==='feishu'">
          <a-form-item :label="kindWebhookLabel" required><a-input v-model:value="channelForm.config.webhook_url" placeholder="机器人 Webhook 地址" /></a-form-item>
        </template>

        <!-- Server酱 -->
        <template v-if="channelForm.kind==='serverchan'">
          <a-form-item label="SendKey" required><a-input v-model:value="channelForm.config.send_key" placeholder="Server酱 SendKey" /></a-form-item>
        </template>

        <a-form-item label="启用"><a-switch v-model:checked="channelForm.enabled" /></a-form-item>
      </a-form>
    </a-modal>

    <!-- 测试发送弹窗 -->
    <a-modal v-model:open="testModal" :title="`测试发送 - ${testChannel?.name||''}`" @ok="doTest" :confirm-loading="testing" :width="modalW" centered>
      <a-form layout="vertical">
        <a-form-item label="标题"><a-input v-model:value="testForm.title" /></a-form-item>
        <a-form-item label="内容"><a-textarea v-model:value="testForm.content" :rows="4" /></a-form-item>
        <a-form-item v-if="testChannel?.kind==='smtp'" label="收件邮箱" required><a-input v-model:value="testForm.target" placeholder="接收测试邮件的邮箱" /></a-form-item>
        <div v-else style="color:#888;font-size:13px">将向该渠道的默认目标（Webhook / SendKey）发送测试消息</div>
      </a-form>
    </a-modal>

    <!-- 联系人弹窗 -->
    <a-modal v-model:open="contactModal" :title="contactForm.id ? '编辑联系人' : '新增联系人'" @ok="saveContact" :confirm-loading="saving" :width="modalW" centered :body-style="{maxHeight:'75vh', overflowY:'auto'}">
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="contactForm.name" /></a-form-item>
        <a-form-item label="邮箱"><a-input v-model:value="contactForm.channels.email" placeholder="接收报警邮件" /></a-form-item>
        <a-form-item label="钉钉">
          <a-select v-model:value="contactForm.channels.dingtalk" allow-clear style="width:100%" placeholder="选择钉钉发信配置">
            <a-select-option v-for="c in channelsOf('dingtalk')" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="企业微信">
          <a-select v-model:value="contactForm.channels.qywx" allow-clear style="width:100%" placeholder="选择企业微信发信配置">
            <a-select-option v-for="c in channelsOf('qywx')" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="飞书">
          <a-select v-model:value="contactForm.channels.feishu" allow-clear style="width:100%" placeholder="选择飞书发信配置">
            <a-select-option v-for="c in channelsOf('feishu')" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Server酱">
          <a-select v-model:value="contactForm.channels.serverchan" allow-clear style="width:100%" placeholder="选择 Server酱 发信配置">
            <a-select-option v-for="c in channelsOf('serverchan')" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="groupModal" :title="groupForm.id ? '编辑通知组' : '新增通知组'" @ok="saveGroup" :confirm-loading="saving" :width="modalW" centered>
      <a-form layout="vertical">
        <a-form-item label="名称" required><a-input v-model:value="groupForm.name" /></a-form-item>
        <a-form-item label="联系人">
          <a-select v-model:value="groupForm.contacts" mode="multiple" style="width:100%">
            <a-select-option v-for="c in contacts" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
          </a-select>
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
const alerts = ref([])
const contacts = ref([])
const groups = ref([])
const channels = ref([])
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const channelModal = ref(false)
const testModal = ref(false)
const contactModal = ref(false)
const groupModal = ref(false)
const channelForm = ref({})
const testForm = ref({})
const testChannel = ref(null)
const contactForm = ref({})
const groupForm = ref({})

const KINDS = { smtp: 'SMTP 邮件', dingtalk: '钉钉机器人', qywx: '企业微信机器人', feishu: '飞书机器人', serverchan: 'Server酱' }
const kindWebhookLabel = computed(() => ({ dingtalk: '钉钉 Webhook', qywx: '企业微信 Webhook', feishu: '飞书 Webhook' }[channelForm.value.kind] || 'Webhook'))

onMounted(load)
async function load() {
  loading.value = true
  try {
    alerts.value = (await api.get('/monitor/alerts/?page_size=200')).results || []
    contacts.value = (await api.get('/monitor/contacts/?page_size=200')).results || []
    groups.value = (await api.get('/monitor/groups/?page_size=200')).results || []
    channels.value = (await api.get('/monitor/channels/?page_size=200')).results || []
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}

function channelsOf(kind) { return channels.value.filter(c => c.kind === kind && c.enabled) }
function configSummary(rec) {
  const c = rec.config || {}
  if (rec.kind === 'smtp') return `${c.host||'-'}:${c.port||''} → ${c.from_email||''}`
  if (rec.kind === 'serverchan') return `SendKey: ${(c.send_key||'').slice(0,6)}***`
  return (c.webhook_url||'-').slice(0, 50)
}
function channelLabel(k, v) {
  const labels = { email: '邮箱', smtp: 'SMTP', dingtalk: '钉钉', qywx: '企业微信', feishu: '飞书', serverchan: 'Server酱' }
  const name = labels[k] || k
  const ch = channels.value.find(c => c.id === Number(v))
  return `${name}${ch ? ': ' + ch.name : ''}`
}

function openChannel(rec) {
  if (rec) channelForm.value = { ...rec, config: { ...(rec.config||{}) } }
  else channelForm.value = { name: '', kind: 'smtp', config: {}, enabled: true }
  channelModal.value = true
}
async function saveChannel() {
  saving.value = true
  try {
    if (channelForm.value.id) await api.patch(`/monitor/channels/${channelForm.value.id}/`, channelForm.value)
    else await api.post('/monitor/channels/', channelForm.value)
    message.success('OK'); channelModal.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function delChannel(rec) { await api.delete(`/monitor/channels/${rec.id}/`); message.success('OK'); load() }

function openTest(rec) {
  testChannel.value = rec
  testForm.value = { title: 'X-ops 测试通知', content: '这是一条来自 X-ops 报警中心的测试消息。', target: '' }
  testModal.value = true
}
async function doTest() {
  testing.value = true
  try {
    const r = await api.post(`/monitor/channels/${testChannel.value.id}/test/`, testForm.value)
    if (r.ok) message.success(r.detail || '发送成功')
    else message.error(r.detail || '发送失败')
    testModal.value = false
  } catch (e) { message.error(e.message) } finally { testing.value = false }
}

function openContact(rec) {
  if (rec) contactForm.value = { ...rec, channels: { ...(rec.channels||{}) } }
  else contactForm.value = { name: '', channels: {} }
  contactModal.value = true
}
async function saveContact() {
  saving.value = true
  try {
    if (contactForm.value.id) await api.patch(`/monitor/contacts/${contactForm.value.id}/`, contactForm.value)
    else await api.post('/monitor/contacts/', contactForm.value)
    message.success('OK'); contactModal.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function delContact(rec) { await api.delete(`/monitor/contacts/${rec.id}/`); message.success('OK'); load() }
function openGroup(rec) {
  if (rec) groupForm.value = { ...rec, contacts: rec.contacts || [] }
  else groupForm.value = { name: '', contacts: [] }
  groupModal.value = true
}
async function saveGroup() {
  saving.value = true
  try {
    if (groupForm.value.id) await api.patch(`/monitor/groups/${groupForm.value.id}/`, groupForm.value)
    else await api.post('/monitor/groups/', groupForm.value)
    message.success('OK'); groupModal.value = false; load()
  } catch (e) { message.error(e.message) } finally { saving.value = false }
}
async function delGroup(rec) { await api.delete(`/monitor/groups/${rec.id}/`); message.success('OK'); load() }
</script>