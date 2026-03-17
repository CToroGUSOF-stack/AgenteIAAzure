<template>
  <div class="icon-wrapper" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @click="pushIcon()" ref="iconRef">
    <div class="icon" :style="{ width: `${size}px`, height: `${size}px` }" v-html="svg"></div>
    <div v-if="showTooltip" :class="['tooltip', tooltipPosition]">
      {{ tooltip }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  svg: {
    type: String,
    required: true,
  },
  size: {
    type: Number,
    default: 24,
  },
  tooltip: {
    type: String,
    default: '',
  },
  position: {
    type: String,
    default: 'top',
  }
});

const emit = defineEmits(['push-icon']);

const pushIcon = () => {
  emit('push-icon');
}

const showTooltip = ref(false);
const tooltipPosition = ref(props.position); // Por defecto, el tooltip se muestra arriba
const iconRef = ref(null);

const onMouseEnter = () => {
  showTooltip.value = true;
};

const onMouseLeave = () => {
  showTooltip.value = false;
};
</script>

<style scoped>
.icon-wrapper {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.icon {
  display: flex;
  justify-content: center;
  align-items: center;
}

.tooltip {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
  pointer-events: none;
}

.tooltip.top {
  bottom: 100%;
  /* Mostrar arriba del icono */
  margin-bottom: 8px;
}

.tooltip.bottom {
  top: 100%;
  /* Mostrar abajo del icono */
  margin-top: 8px;
}

.icon-wrapper:hover .tooltip {
  opacity: 1;
}
</style>
