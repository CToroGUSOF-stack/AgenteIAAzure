<template>
  <div class="user-badge" :class="{ 'small-screen': isSmallScreen }">
    <span v-if="!isSmallScreen">{{ name }}</span>
    <img :src="imageUrl" alt="User Avatar" class="avatar" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";

// Props
const props = defineProps({
  name: {
    type: String,
    default: "Teams Vamos",
  },
  imageUrl: {
    type: String,
    default:
      "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png", // Default image if none is provided
  },
});

// Reactive state for screen size
const isSmallScreen = ref(false);

// Helper function to check screen size
const updateScreenSize = () => {
  isSmallScreen.value = window.innerWidth <= 768;
};

// Lifecycle hooks
onMounted(() => {
  updateScreenSize();
  window.addEventListener("resize", updateScreenSize);
});

onUnmounted(() => {
  window.removeEventListener("resize", updateScreenSize);
});
</script>

<style scoped>
.user-badge {
  display: flex;
  align-items: center;
  background-color: white;
  padding: 5px 10px;
  transition: all 0.3s ease;
}

.user-badge.small-screen {
  padding: 5px;
}

.user-badge span {
  margin-right: 10px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.user-badge .avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
</style>
