<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ t.dashboard }}</h2>
    </div>
    <div class="stat-grid">
      <div class="stat-card"><div class="label">{{ t.hosts }}</div><div class="value">{{ stats.hosts }}</div></div>
      <div class="stat-card"><div class="label">{{ t.online }}</div><div class="value" style="color:#52c41a">{{ stats.online }}</div></div>
      <div class="stat-card"><div class="label">{{ t.exec }}</div><div class="value">{{ stats.executions }}</div></div>
      <div class="stat-card"><div class="label">{{ t.deploy }}</div><div class="value">{{ stats.releases }}</div></div>
      <div class="stat-card"><div class="label">{{ t.monitor }}</div><div class="value">{{ stats.rules }}</div></div>
      <div class="stat-card"><div class="label">{{ t.alarm }}</div><div class="value" style="color:#ff4d4f">{{ stats.alerts }}</div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import { useAppStore } from '../store'
import locales from '../locales'

const store = useAppStore()
const t = computed(() => locales[store.lang])
const stats = ref({ hosts: 0, online: 0, executions: 0, releases: 0, rules: 0, alerts: 0 })

onMounted(async () => {
  try {
    const [hosts, execs, releases, rules, alerts] = await Promise.all([
      api.get('/hosts/hosts/'), api.get('/exec/executions/'),
      api.get('/deploy/releases/'), api.get('/monitor/rules/'), api.get('/monitor/alerts/'),
    ])
    stats.value.hosts = hosts.count || 0
    stats.value.online = (hosts.results || []).filter(h => h.status === 'online').length
    stats.value.executions = execs.count || 0
    stats.value.releases = releases.count || 0
    stats.value.rules = rules.count || 0
    stats.value.alerts = alerts.count || 0
  } catch (e) {}
})
</script>
