<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  isMaximized: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'mouseenter',
  'mouseleave',
  'close-app',
  'minimize-to-tray',
  'minimize-window',
  'toggle-maximize',
])
</script>

<template>
  <div class="window-chrome">
    <div class="window-drag-region"></div>

    <div
      class="shell-hover-zone"
      @mouseenter="emit('mouseenter')"
      @mouseleave="emit('mouseleave')"
    >
      <div class="shell-stack" :class="{ expanded: visible }">
        <!-- 关闭 -->
        <button
          class="shell-stack-btn shell-close-btn"
          data-tip="关闭应用"
          @click="emit('close-app')"
        >
          <svg
            class="shell-icon shell-icon-close"
            :class="{ rotated: visible }"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M6 6L18 18" />
            <path d="M18 6L6 18" />
          </svg>
        </button>

        <!-- 最小化到托盘 -->
        <button
          class="shell-stack-btn"
          data-tip="最小化到托盘"
          @click="emit('minimize-to-tray')"
        >
          <svg class="shell-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 18H19" />
            <path d="M12 5V14" />
            <path d="M8.5 10.5L12 14L15.5 10.5" />
          </svg>
        </button>

        <!-- 最小化窗口 -->
        <button
          class="shell-stack-btn"
          data-tip="缩小到底部"
          @click="emit('minimize-window')"
        >
          <svg class="shell-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 12H18" />
          </svg>
        </button>

        <!-- 最大化 / 还原 -->
        <button
          class="shell-stack-btn"
          :data-tip="isMaximized ? '窗口还原' : '窗口最大化'"
          @click="emit('toggle-maximize')"
        >
          <svg
            v-if="!isMaximized"
            class="shell-icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <rect x="7" y="7" width="10" height="10" rx="1.5" />
          </svg>

          <svg
            v-else
            class="shell-icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <rect x="9" y="9" width="9" height="9" rx="1.5" />
            <path d="M15 9V6H6V15H9" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>