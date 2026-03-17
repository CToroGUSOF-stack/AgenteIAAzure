<template>
  <!-- Estado inicial: sin mensajes - mostrar saludo inicial -->
  <div v-if="messages.length === 0" class="chat-messages greeting-container" ref="scrollContainer">
    <h1 class="text-center">Hola, Test</h1>
  </div>
  <div v-else class="chat-messages" ref="scrollContainer">
    <div v-for="(msg, index) in messages" :key="index">
      <UserMessage
        v-if="msg.sender === 'user'"
        :msg="msg"
        @edited="handleEdited"
      />
      <IAMessage v-else :msg="msg" @regenerate="handleRegenerate" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import UserMessage from "./UserMessage.vue";
import IAMessage from "./IAMessage.vue";
import { useRoute } from "vue-router";

// Mensaje de saludo inicial para nuevas conversaciones
// const greetingMessage = {
//   text: SALUDO,
//   sender: "assistant",
//   isLoading: false,
//   id: "greeting-initial"
// };

const scrollContainer = ref(null);

const route = useRoute()
const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
    // Formato: [{ text: 'Hola', sender: 'user', files: Files, id: '15488sdas-sdasd, etc' }, { text: '¡Hola!', sender: 'assistant', isLoading: false, id: '15488sdas-sdasd, etc' }, ... ]
  },
});
const emit = defineEmits(["regenerate", "edited"]);

const handleRegenerate = (id_msg) => {
  emit("regenerate", {id_msg, chatId: route.params.id});
};
const handleEdited = (id_msg) => {
  emit("edited", {id_msg, chatId: route.params.id});
};

const scrollToBottom = async () => {
  await nextTick();
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

watch(
  () => props.messages,
  () => {
    scrollToBottom();
  },
  { deep: true }
);
</script>

<style scoped>
.chat-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  background-color: #ffffff;
  overflow-y: auto;
}

.greeting-container {
  justify-content: center;
  padding-top: 20%;
}
</style>
