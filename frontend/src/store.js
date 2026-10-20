import { defineStore } from 'pinia'
import api from './api'

export const useAppStore = defineStore('app', {
  state: () => ({
    token: localStorage.getItem('ops_token') || '',
    user: null,
    lang: localStorage.getItem('ops_lang') || 'zh',
  }),
  getters: {
    isAuthed: (s) => !!s.token,
  },
  actions: {
    async login(username, password) {
      const data = await api.post('/auth/token/', { username, password })
      this.token = data.access
      localStorage.setItem('ops_token', data.access)
      await this.fetchMe()
    },
    async fetchMe() {
      this.user = await api.get('/accounts/me/')
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('ops_token')
    },
    setLang(lang) {
      this.lang = lang
      localStorage.setItem('ops_lang', lang)
    },
  },
})
