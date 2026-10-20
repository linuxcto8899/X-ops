<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" :width="220">
      <div class="logo">{{ t.appName }}</div>
      <a-menu theme="dark" mode="inline" :selectedKeys="[activeKey]" @click="onMenu">
        <a-menu-item key="dashboard"><template #icon><DashboardOutlined /></template>{{ t.dashboard }}</a-menu-item>
        <a-menu-item key="hosts"><template #icon><DesktopOutlined /></template>{{ t.hosts }}</a-menu-item>
        <a-menu-item key="host-monitor"><template #icon><LineChartOutlined /></template>{{ t.hostMonitor }}</a-menu-item>
        <a-menu-item key="exec"><template #icon><PlayCircleOutlined /></template>{{ t.exec }}</a-menu-item>
        <a-menu-item key="terminal"><template #icon><ConsoleSqlOutlined /></template>{{ t.terminal }}</a-menu-item>
        <a-menu-item key="docker"><template #icon><DeploymentUnitOutlined /></template>{{ t.docker }}</a-menu-item>
        <a-menu-item key="files"><template #icon><FolderOutlined /></template>{{ t.files }}</a-menu-item>
        <a-menu-item key="transfer"><template #icon><SendOutlined /></template>{{ t.transfer }}</a-menu-item>
        <a-menu-item key="deploy"><template #icon><RocketOutlined /></template>{{ t.deploy }}</a-menu-item>
        <a-menu-item key="pipeline"><template #icon><ApartmentOutlined /></template>{{ t.pipeline }}</a-menu-item>
        <a-menu-item key="scheduler"><template #icon><FieldTimeOutlined /></template>{{ t.scheduler }}</a-menu-item>
        <a-menu-item key="config"><template #icon><SettingOutlined /></template>{{ t.configCenter }}</a-menu-item>
        <a-menu-item key="monitor"><template #icon><AlertOutlined /></template>{{ t.monitor }}</a-menu-item>
        <a-menu-item key="alarm"><template #icon><BellOutlined /></template>{{ t.alarm }}</a-menu-item>
        <a-menu-item key="credentials"><template #icon><KeyOutlined /></template>{{ t.credentials }}</a-menu-item>
        <a-menu-item key="users"><template #icon><TeamOutlined /></template>{{ t.users }}</a-menu-item>
        <a-menu-item key="roles"><template #icon><SafetyOutlined /></template>{{ t.roles }}</a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="header">
        <div class="header-right">
          <a-space>
            <a-button size="small" @click="store.setLang('zh')" :type="store.lang==='zh'?'primary':'default'">中文</a-button>
            <a-button size="small" @click="store.setLang('en')" :type="store.lang==='en'?'primary':'default'">EN</a-button>
            <a-dropdown>
              <a-avatar style="background:#1677ff; cursor:pointer">{{ (store.user?.username||'U')[0].toUpperCase() }}</a-avatar>
              <template #overlay>
                <a-menu @click="onUserMenu">
                  <a-menu-item key="logout">{{ t.logout }}</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
      </a-layout-header>
      <a-layout-content style="margin:16px">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align:center; color:#999; font-size:13px; padding:12px">
        X-ops · t.me/@linuxcto998 · QQ:5609648
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DashboardOutlined, DesktopOutlined, LineChartOutlined, PlayCircleOutlined, ConsoleSqlOutlined, DeploymentUnitOutlined, FolderOutlined, SendOutlined, RocketOutlined, ApartmentOutlined, FieldTimeOutlined, SettingOutlined, AlertOutlined, BellOutlined, KeyOutlined, TeamOutlined, SafetyOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '../store'
import locales from '../locales'

const store = useAppStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const t = computed(() => locales[store.lang])
const activeKey = computed(() => route.name || 'dashboard')

onMounted(async () => {
  if (!store.user) {
    try { await store.fetchMe() } catch (e) { store.logout(); router.push('/login') }
  }
})

function onMenu({ key }) {
  if (key === 'host-monitor') router.push('/host-monitor')
  else router.push('/' + key)
}
function onUserMenu({ key }) {
  if (key === 'logout') { store.logout(); router.push('/login') }
}
</script>

<style scoped>
.logo { color: #fff; font-size: 18px; font-weight: 600; text-align: center; padding: 16px 0; }
.header { background: #fff; padding: 0 16px; display: flex; justify-content: flex-end; align-items: center; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.header-right { display: flex; align-items: center; }
</style>
