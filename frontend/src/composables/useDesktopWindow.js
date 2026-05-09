import { onBeforeUnmount, onMounted, ref } from 'vue'

export function useDesktopWindow() {
  const isDesktopShell =
    typeof window !== 'undefined' && !!window.desktopAPI

  const shellMenuOpen = ref(false)
  const isMaximized = ref(false)

  let removeWindowStateListener = null

  function openShellMenu() {
    shellMenuOpen.value = true
  }

  function closeShellMenu() {
    shellMenuOpen.value = false
  }

  function toggleShellMenu() {
    shellMenuOpen.value = !shellMenuOpen.value
  }

  async function syncWindowState() {
    if (!window.desktopAPI?.getWindowState) return
    try {
      const state = await window.desktopAPI.getWindowState()
      isMaximized.value = !!state?.isMaximized
    } catch (error) {
      console.error(error)
    }
  }

  async function handleCloseApp() {
    shellMenuOpen.value = false
    if (window.desktopAPI?.closeApp) {
      await window.desktopAPI.closeApp()
    }
  }

  async function handleMinimizeToTray() {
    shellMenuOpen.value = false
    if (window.desktopAPI?.minimizeToTray) {
      await window.desktopAPI.minimizeToTray()
    }
  }

  async function handleMinimizeWindow() {
    shellMenuOpen.value = false
    if (window.desktopAPI?.minimizeWindow) {
      await window.desktopAPI.minimizeWindow()
    }
  }

  async function handleToggleMaximize() {
    shellMenuOpen.value = false
    if (window.desktopAPI?.toggleMaximize) {
      const state = await window.desktopAPI.toggleMaximize()
      isMaximized.value = !!state?.isMaximized
    }
  }

  onMounted(async () => {
    if (!isDesktopShell) return

    document.body.classList.add('desktop-shell')
    await syncWindowState()

    if (window.desktopAPI?.onWindowState) {
      removeWindowStateListener = window.desktopAPI.onWindowState((payload) => {
        isMaximized.value = !!payload?.isMaximized
      })
    }
  })

  onBeforeUnmount(() => {
    if (typeof removeWindowStateListener === 'function') {
      removeWindowStateListener()
    }

    if (isDesktopShell) {
      document.body.classList.remove('desktop-shell')
    }
  })

  return {
    isDesktopShell,
    shellMenuOpen,
    isMaximized,
    openShellMenu,
    closeShellMenu,
    toggleShellMenu,
    handleCloseApp,
    handleMinimizeToTray,
    handleMinimizeWindow,
    handleToggleMaximize,
  }
}