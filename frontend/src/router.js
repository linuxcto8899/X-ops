import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/Login.vue') },
  { path: '/exec-stream/:executionId/:hostId', name: 'execStream', component: () => import('./views/ExecStream.vue') },
  {
    path: '/',
    component: () => import('./views/Layout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'dashboard', component: () => import('./views/Dashboard.vue') },
      { path: 'hosts', name: 'hosts', component: () => import('./views/Hosts.vue') },
      { path: 'host-monitor/:id?', name: 'hostMonitor', component: () => import('./views/HostMonitor.vue') },
      { path: 'exec', name: 'exec', component: () => import('./views/Exec.vue') },
      { path: 'terminal/:id?', name: 'terminal', component: () => import('./views/Terminal.vue') },
      { path: 'docker', name: 'docker', component: () => import('./views/Docker.vue') },
      { path: 'files', name: 'files', component: () => import('./views/Files.vue') },
      { path: 'transfer', name: 'transfer', component: () => import('./views/Transfer.vue') },
      { path: 'deploy', name: 'deploy', component: () => import('./views/Deploy.vue') },
      { path: 'pipeline', name: 'pipeline', component: () => import('./views/Pipeline.vue') },
      { path: 'scheduler', name: 'scheduler', component: () => import('./views/Scheduler.vue') },
      { path: 'config', name: 'config', component: () => import('./views/ConfigCenter.vue') },
      { path: 'monitor', name: 'monitor', component: () => import('./views/Monitor.vue') },
      { path: 'alarm', name: 'alarm', component: () => import('./views/Alarm.vue') },
      { path: 'credentials', name: 'credentials', component: () => import('./views/Credentials.vue') },
      { path: 'users', name: 'users', component: () => import('./views/Users.vue') },
      { path: 'roles', name: 'roles', component: () => import('./views/Roles.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('ops_token')
  if (to.name !== 'login' && !token) return { name: 'login' }
  if (to.name === 'login' && token) return { name: 'dashboard' }
  return true
})

export default router
