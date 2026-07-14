import { defineStore } from 'pinia'

export const useLogsStore = defineStore('logs', {
  state: () => ({
    logsList: []
  }),
  getters: {
    logsLen: (state) => state.logsList.length || 0,
    logsFlag: (state) => state.logsList.length === 0
  },
  actions: {
    addLog(log) {
      this.logsList.push(log)
    },
    clearLogs() {
      this.logsList = []
    }
  }
})
