import { onMounted, ref } from 'vue'
import axios from 'axios'

export function useBackendBoot(apiBase) {
  const booting = ref(true)
  const bootError = ref('')

  function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  async function waitForBackendReady() {
    booting.value = true
    bootError.value = ''

    for (let attempt = 0; attempt < 60; attempt++) {
      try {
        const response = await axios.get(`${apiBase}/health`, {
          timeout: 1500,
        })

        if (response.data?.ok) {
          booting.value = false
          return true
        }
      } catch (_error) {
        // 继续轮询
      }

      await wait(800)
    }

    booting.value = false
    bootError.value = '服务启动超时，请确认后端服务已经启动'
    return false
  }

  async function retryBoot() {
    await waitForBackendReady()
  }

  onMounted(async () => {
    await waitForBackendReady()
  })

  return {
    booting,
    bootError,
    retryBoot,
    waitForBackendReady,
  }
}