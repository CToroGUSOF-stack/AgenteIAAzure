<template>
  <div class="chat-section">
    <div
      v-for="(group, groupIndex) in activatedSession.chatGroups"
      :key="group.date"
      class="chat-group"
    >
      <div class="chat-date">{{ group.date }}</div>
      <ul class="chat-list">
        <template
          v-for="(chat, chatIndex) in group.chats"
          :key="chat ? chat.id : chatIndex"
        >
        <li
          v-if="chat && chat.id"
          class="chat-item flex justify-between items-center rounded-md transition-colors duration-150 cursor-pointer hover:opacity-80 group"
          :class="{
            'bg-[#006937] text-[#fff] !font-bold':
              chat.id === chatIdParam /* seleccionado */,
            'bg-gray-100': editingChatId === chat.id /* editing style */
          }"
          @click="selectChat(chat)"
        >
          <!-- View Mode -->
          <span v-if="editingChatId !== chat.id" class="chat-text w-full p-2 truncate">
            {{ chat.chat }}
          </span>

          <!-- Edit Mode -->
          <div v-else class="w-full p-1" @click.stop>
            <input
              ref="editInputRef"
              v-model="editNameInput"
              class="w-full text-black px-2 py-1 rounded text-sm border border-green-500 focus:outline-none"
              @keyup.enter="saveEdit(chat)"
              @keyup.esc="cancelEdit"
              @blur="cancelEdit"
              placeholder="Nombre del chat"
            />
          </div>

          <!-- Options Buttons -->
          <div class="chat-options absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex gap-1 bg-inherit px-1" v-if="chat.chat != 'Nueva conversacion' && editingChatId !== chat.id">

            <!-- Rename Button -->
            <button @click.stop="startEdit(chat)" class="p-1 hover:bg-gray-200 rounded-full" title="Renombrar">
                <svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='gray' class='bi bi-pencil' viewBox='0 0 16 16'>
                  <path d='M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z'/>
                </svg>
            </button>

            <!-- Delete Button -->
            <button
                @click.stop="deletedChat(chat.id)"
                :disabled="isLoadingDeleteMap[chat.id]"
                class="p-1 hover:bg-gray-200 rounded-full"
                title="Eliminar"
            >
                <div role="status">
                <svg
                    v-if="isLoadingDeleteMap[chat.id]"
                    aria-hidden="true"
                    class="w-4 h-4 animate-spin text-gray-300 fill-gray-500"
                    viewBox="0 0 100 101"
                    fill="none"
                >
                    <path
                    d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591..."
                    fill="currentColor"
                    />
                    <path d="M93.9676 39.0409C96.393..." fill="currentFill" />
                </svg>

                <svg v-else xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='gray' class='bi bi-trash' viewBox='0 0 16 16'>
                    <path d='M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z'/>
                    <path d='M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z'/>
                </svg>
                </div>
            </button>
          </div>
        </li>
        </template>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { activatedSession, isLoadingDeleteMap } from "@/state";
import IconWithTooltip from "../utils/IconTooltip.vue";
import { computed, ref, nextTick } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const chatIdParam = computed(() => route.params.id);

const emit = defineEmits(["select-conversation", "delete-conversation", "rename-conversation"]);

const editingChatId = ref(null);
const editNameInput = ref("");
const editInputRef = ref(null);

const deletedChat = (id_chat) => {
  emit("delete-conversation", id_chat);
};

const selectChat = (chat) => {
  if (editingChatId.value === chat.id) return;
  emit("select-conversation", chat);
};

const startEdit = async (chat) => {
    editingChatId.value = chat.id;
    editNameInput.value = chat.chat;
    await nextTick();
    if (editInputRef.value && editInputRef.value[0]) {
        editInputRef.value[0].focus();
    }
};

const saveEdit = (chat) => {
    if (editNameInput.value.trim() && editNameInput.value !== chat.chat) {
        emit("rename-conversation", { id: chat.id, name: editNameInput.value });
    }
    editingChatId.value = null;
    editNameInput.value = "";
};

const cancelEdit = () => {
    editingChatId.value = null;
};
</script>

<style scoped>
.chat-section {
  flex-grow: 1;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 15px;
  position: relative;
}

.chat-group {
  margin-bottom: 16px;
}

.chat-date {
  font-weight: bold;
  color: #555;
  margin-bottom: 8px;
}

.chat-list {
  list-style: none;
  padding: 0;
}

.chat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 4px;
  position: relative;
  transition: background-color 0.2s ease;
  min-height: 40px;
}

/* Hover effect on entire row handled by tailwind directives in template but kept here for structure */

.chat-text {
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.chat-options {
  /* Using tailwind group-hover:block/flex now */
  /* display: none; */
}

/* Make sure the option icon is visible on selected items force override if needed */
.selected .chat-options svg {
  fill: white;
}

@media (max-width: 768px) {
  .chat-text {
    max-width: 155px;
  }
}
</style>
