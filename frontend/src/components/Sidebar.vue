<template>
  <div class="sidebar relative pt-2 border-r border-neutral-300 h-full">
    <div class="">
      <!-- HEADER -->
      <button class="!mx-[10px] !mb-2 cursor-pointer" @click="toggleSidebar">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="{1.5}"
          stroke="#000"
          class="size-8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
      </button>

      <!-- HISTORIAL MOCKEADO -->

      <RouterLink
        to="/"
        class="!mx-[10px] px-[5px] py-2 flex flex-row hover:bg-neutral-200 rounded-sm items-center"
      >
        <div class="flex flex-row">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="!size-6"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
            />
          </svg>
          <span v-show="open" class="text-nowrap !ml-2">
            Nueva conversación
          </span>
        </div>
      </RouterLink>
      <div
        :class="`transition-all duration-300 ease-in-out ${
          open ? 'opacity-100' : 'opacity-0'
        }`"
      >
        <ChatHistorial
          @select-conversation="selectChat"
          @delete-conversation="deleteChat"
          @rename-conversation="renameChat"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import ChatHistorial from "./sidebar/HistorialSection.vue";

const router = useRouter();

const emit = defineEmits([
  "toggle-sidebar",
  "delete-chat",
  "rename-chat",
]);

defineProps({
  open: {
    type: Boolean,
    required: true,
  }
});

const toggleSidebar = () => emit("toggle-sidebar");

// ========================
// Seleccionar conversación
// ========================
const selectChat = (chat) => {
  router.push(`/c/${chat.id}`);
};

const deleteChat = (chatId) => {
  emit("delete-chat", chatId);
};

const renameChat = (payload) => {
  emit("rename-chat", payload);
};


</script>

<style scoped>
.sidebar-interna {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0px 16px 0px;
  padding: 0 8px;
}

.logo-header {
  height: 32px;
  margin-left: 8px;
  transition: transform 0.2s ease;
}

.logo-header:hover {
  transform: scale(1.05);
}

.footer {
  text-align: center;
  margin-top: 16px;
}

.footer-line {
  margin: 10px 20px;
  border: none;
  height: 0.6px;
  background-color: #ccc;
}

.footer-text {
  font-size: 14px;
  font-weight: 100;
  color: #777;
}

.footer-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.footer-logo {
  height: 24px;
  width: auto;
}
</style>
