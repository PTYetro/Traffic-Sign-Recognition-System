<script setup>
defineProps({
  booting: {
    type: Boolean,
    default: false,
  },
  bootError: {
    type: String,
    default: '',
  },
  isDesktopShell: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['retry', 'close-app'])
</script>

<template>
  <div v-if="booting || bootError" class="boot-overlay">
    <div class="boot-card">
      <div class="boot-center">
        <div v-if="!bootError" class="boot-inline">
          <div class="boot-spinner"></div>
          <div class="boot-inline-text">服务启动中</div>
        </div>

        <template v-else>
          <div class="boot-error-title">服务启动异常</div>
          <div class="boot-error-text">{{ bootError }}</div>

          <div class="boot-actions">
            <button class="boot-retry-btn" @click="emit('retry')">
              重新检测
            </button>

            <button
              v-if="isDesktopShell"
              class="boot-close-btn"
              @click="emit('close-app')"
            >
              关闭应用
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>