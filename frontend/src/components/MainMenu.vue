<template>
  <div class="chat-container text-message !w-full !max-w-full !relative prose">
    <header
      class="w-full border-b border-neutral-300 absolute top-0 left-0 px-4 py-3"
    >
      <RouterLink to="/">
        <img src="/public/logo.png" alt="Logo Policía" class="mx-auto" />
      </RouterLink>
    </header>
    <ChatMessages
      :messages="activatedSession.allMsgs[chatIdParams] || []"
      class="chat-messages"
      @regenerate="handleRegenerate"
      @edited="handleEdited"
    />
    <ChatInput
      :is-loading="isLoading"
      @send-message="handleSendMessage"
      @stop-message="handleStop"
      class="chat-input"
      :isActive="isSearch"
      @update:isActive="handleButtonIsSearch"
      :modelSelect="modelSelect"
      :isChaningChat="isChaningChat"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import ChatMessages from "./chat/ChatMessages.vue";
import ChatInput from "./chat/ChatInput.vue";
import api from "../api";
import { activatedSession } from "../state";
import { useRoute, useRouter } from "vue-router";

// Obtener id chat, si esta vacio es porque es una nueva conversación
const route = useRoute();
const router = useRouter();

const isChaningChat = ref(false);

const chatIdParams = ref(undefined);

watch(
  () => route.params.id,
  (newVal) => {
    chatIdParams.value = newVal;
    if (newVal) {
      fetchGetMessages(newVal);
    }
  }
);

function fetchGetMessages(session_id) {
  if (session_id) {
    api.requestOneSession(session_id).then((res) => {
      console.log(res);
      loadMessages(session_id, res.messages);
    });
  } else {
    getMessages("");
  }
}

const getMessages = (chatId) => {
  return activatedSession.allMsgs[chatId] || [];
};

onMounted(() => {
  fetchGetMessages(route.params?.id);
});

// const messages = computed({
//   get() {
//     return activatedSession.allMsgs[chatIdParams.value] ?? [];
//   },
//   set(val) {
//     activatedSession.allMsgs[chatIdParams.value] = val;
//   },
// });

const setMessages = (chatId, messages) => {
  activatedSession.allMsgs[chatId] = messages;
};
const pushMessage = (chatId, msg) => {
  const prev = activatedSession.allMsgs[chatId] ?? [];

  activatedSession.allMsgs[chatId] = [...prev, msg];
};

const isLoading = ref(false);
const was_stop = ref(false);
const isSearch = ref(false);

const { modelSelect } = defineProps({
  modelSelect: String,
});

const loadingMessage = {
  text: "",
  sender: "assistant",
  isLoading: true,
};

onMounted(() => {
  isSearch.value = localStorage.getItem("isSearch") === "true";
});

const handleButtonIsSearch = () => {
  localStorage.setItem("isSearch", !isSearch.value);
  isSearch.value = !isSearch.value;
};

const handleEdited = async ({ chatId, id_msg }) => {
  const msgs = getMessages(chatId);

  const index = msgs.findIndex((msg) => msg.id === id_msg);
  if (index === -1) return;

  const msg_user_prev = msgs[index].text;
  const id_msg_ia = msgs[index + 1]?.id;

  // Cortar mensajes desde index + 1 hacia adelante
  const newList = msgs.slice(0, index + 1);

  // Reemplazar lista
  setMessages(chatId, newList);

  // Regenerar
  await handleSendMessage(
    {
      text: msg_user_prev,
      id: id_msg_ia,
      files: null,
    },
    true // modo regenerar
  );
};

const removeEndMessage = ({ chatId }) => {
  activatedSession.allMsgs[chatId] = (
    activatedSession.allMsgs[chatId] ?? []
  ).slice(0, -1);
};

const handleRegenerate = async ({ chatId, id_msg }) => {
  const msgs = getMessages(chatId);

  const index = msgs.findIndex((msg) => msg.id === id_msg);
  if (index === -1) return;

  // El mensaje del usuario siempre es el que viene ANTES del de la IA
  const msg_user_prev = msgs[index - 1]?.text;
  if (!msg_user_prev) return;

  // Cortar los mensajes justo antes del mensaje IA anterior
  const newList = msgs.slice(0, index);

  // Reemplazar en el estado
  setMessages(chatId, newList);

  // Llamar a handleSendMessage en modo regenerar
  await handleSendMessage(
    {
      text: msg_user_prev,
      id: id_msg, // se vuelve a enviar con el mismo id
      files: null,
    },
    true
  );
};

let id_current_msg = "";
const handleSendMessage = async (user_message, is_regenerate) => {
  if (isLoading.value) return;
  isLoading.value = true;
  const userText = user_message.text;
  const userFiles = user_message.files;
  const id = user_message.id;
  id_current_msg = id;
  const longitudDeseada = 28;
  const session_id = chatIdParams.value || crypto.randomUUID();
  const chatName = chatIdParams.value
    ? getChatName(chatIdParams.value)
    : userText.length >= longitudDeseada
    ? userText.substring(0, longitudDeseada)
    : userText;

  // Crear chat si es nuevo
  if (!chatIdParams.value) {
    createConversation({ id: session_id, name: chatName });
    // Inicializar sus mensajes antes del push
    activatedSession.allMsgs[session_id] = [];

    // Inject greeting message for immediate visibility
    // const greetingMsg = {
    //     text: SALUDO,
    //     sender: "assistant",
    //     id: "greeting-" + session_id,
    //     files: null,
    //     created_at: new Date().toISOString()
    // };
    // pushMessage(session_id, greetingMsg);

    // redirigir
    router.push(`/c/${session_id}`);
  }

  // Agregar el mensaje del usuario al chat
  if (!is_regenerate) {
    pushMessage(session_id, {
      text: userText,
      sender: "user",
      files: userFiles,
      id: id + "-u",
    });
  }

  pushMessage(session_id, loadingMessage);

  try {
    // Si hay archivos, enviamos los archivos al endpoint de adjuntos
    if (userFiles && userFiles.length > 0) {
      const formData = new FormData();

      formData.append("message_id", id);
      formData.append("session_id", session_id);
      // formData.append("session_name", chatName);
      formData.append("message", userText);
      // formData.append("flag_modifier", is_regenerate);
      // formData.append("model_name", modelSelect);
      // formData.append("search_tool", false);

      userFiles.forEach((fileObj) => {
        formData.append("files", fileObj.file);
      });

      const attachmentResponse = await api.requestAttachment(formData);

      if (was_stop.value) {
        was_stop.value = false;
        return;
      }

      removeEndMessage({ chatId: session_id });
      isLoading.value = false;
      pushMessage(session_id, {
        text: attachmentResponse.text,
        sender: "assistant",
        isLoading: false,
        id: id,
        citations: attachmentResponse.citations,
      });
    } else {
      // Si solo hay texto, enviamos el mensaje al chatbot
      const aiResponse = await api.requestChat(
        userText,
        id,
        is_regenerate,
        isSearch.value,
        modelSelect,
        session_id,
        chatName
      );
      if (was_stop.value) {
        was_stop.value = false;
        return;
      }

      removeEndMessage({ chatId: session_id });
      isLoading.value = false;

      pushMessage(session_id, {
        text: aiResponse.text,
        sender: "assistant",
        isLoading: false,
        id: id,
        citations: aiResponse.citations,
      });
    }
  } catch (error) {
    isLoading.value = false;
    removeEndMessage({ chatId: session_id });
    pushMessage(session_id, {
      text: "Hubo un error al procesar tu mensaje.",
      sender: "assistant",
      isLoading: false,
    });
  }
};

const handleStop = async (session_id) => {
  was_stop.value = true;
  isLoading.value = false;
  removeEndMessage({ chatId: session_id });
  pushMessage(session_id, {
    text: "El mesaje fue cancelado por el usuario",
    sender: "assistant",
    isLoading: false,
    id: "x",
  });
  // Vote logic removed
};

const loadMessages = (session_id, newMessages) => {
  if (session_id === undefined) {
    setMessages(session_id, newMessages);
    return;
  }
  // Removed skipping cache logic to ensure history is loaded
  // if (activatedSession.allMsgs[chatIdParams.value]) return;

  activatedSession.allMsgs = {
    ...activatedSession.allMsgs,
    [session_id]: newMessages.map((msg) => ({
      text: msg.content,
      sender: msg.role === "user" ? "user" : "assistant",
      id: msg.id,
      files: msg?.files,
      rate: msg.rate,
      citations: msg.citations,
    })),
  };
};

// ➕ Agregar conversación
const createConversation = ({ id, name }) => {
  const todayGroup = activatedSession.chatGroups.find((g) => g.date === "Hoy");

  if (todayGroup) {
    todayGroup.chats.unshift({ id, chat: name });
  } else {
    activatedSession.chatGroups.unshift({
      date: "Hoy",
      chats: [{ id, chat: name }],
    });
  }
};

const getChatName = (id) => {
  for (const group of activatedSession.chatGroups) {
    const found = group.chats.find((c) => c.id === id);
    if (found) return found.chat;
  }
  return null;
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background-color: #fff;
  overflow: hidden;
}

.chat-input {
  /* margin: 0px 100px; */
}

.chat-messages {
  margin-top: 86px;
  padding: 12px 30px;
}

.chat-note {
  text-align: center;
  font-size: 0.85rem;
  color: #666;
  margin: 10px 0px;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .chat-note {
    font-size: 0.75rem;
  }

  .chat-input {
    margin: 0px 20px;
  }
}

@media (min-width: 769px) and (max-width: 1080px) {
  .chat-note {
    font-size: 0.75rem;
  }

  .chat-input {
    margin: 0px 60px;
  }
}

.chat-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 10px 0px;
}

.chat-note {
  text-align: center;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
  margin-bottom: 8px;
}

.powered-by {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.powered-text {
  font-size: 14px;
  font-weight: 100;
  color: #777;
  margin: 0;
}

.powered-logo {
  height: 24px;
  width: auto;
}

@media (max-width: 768px) {
  .chat-note {
    font-size: 0.75rem;
  }

  .powered-text {
    font-size: 12px;
  }

  .powered-logo {
    height: 20px;
  }

  .chat-input {
    margin: 0px 20px;
  }
}

@media (min-width: 769px) and (max-width: 1080px) {
  .chat-note {
    font-size: 0.75rem;
  }

  .chat-input {
    margin: 0px 60px;
  }
}
</style>
