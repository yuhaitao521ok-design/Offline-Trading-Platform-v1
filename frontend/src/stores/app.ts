import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type NoticeLevel = 'success' | 'warning' | 'error' | 'info'

export interface AppNotice {
  id: string
  level: NoticeLevel
  title: string
  message: string
  createdAtUtc: string
  read: boolean
}

export const useAppStore = defineStore('app', () => {
  const globalLoadingCount = ref(0)
  const notices = ref<AppNotice[]>([])

  const isGlobalLoading = computed(() => globalLoadingCount.value > 0)
  const unreadNoticeCount = computed(() => notices.value.filter((notice) => !notice.read).length)

  function startGlobalLoading(): void {
    globalLoadingCount.value += 1
  }

  function stopGlobalLoading(): void {
    globalLoadingCount.value = Math.max(0, globalLoadingCount.value - 1)
  }

  function pushNotice(payload: Omit<AppNotice, 'id' | 'createdAtUtc' | 'read'>): AppNotice {
    const notice: AppNotice = {
      ...payload,
      id: crypto.randomUUID(),
      createdAtUtc: new Date().toISOString(),
      read: false,
    }

    notices.value.unshift(notice)
    notices.value = notices.value.slice(0, 50)
    return notice
  }

  function markNoticeRead(id: string): void {
    const notice = notices.value.find((item) => item.id === id)
    if (notice) {
      notice.read = true
    }
  }

  function clearNotices(): void {
    notices.value = []
  }

  return {
    globalLoadingCount,
    isGlobalLoading,
    notices,
    unreadNoticeCount,
    startGlobalLoading,
    stopGlobalLoading,
    pushNotice,
    markNoticeRead,
    clearNotices,
  }
})
