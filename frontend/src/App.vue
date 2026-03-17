<template>
  <div class="flex flex-row h-screen">
    <div
      :class="`transition-all flex flex-col overflow-x-hidden
        ${
          open
            ? 'lg:w-3/12 w-8/12 top-0'
            : 'w-0 -translate-x-full lg:w-[60px] lg:translate-x-0'
        }`"
    >
      <Sidebar
        class="w-full"
        @toggle-sidebar="toggleSidebar"
        @delete-chat="deleteChat"
        @rename-chat="renameChat"
        :open="open"
      />
    </div>

    <div class="flex-1">
      <router-view />
    </div>

    <!-- Notificación global -->
    <v-snackbar
      v-model="snackbar"
      timeout="4000"
      variant="tonal"
      location="top"
      color="green"
    >
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { activatedSession } from "./state";
import Sidebar from "./components/Sidebar.vue";
import { useRouter } from "vue-router";
import api from "./api.js";

const loaderMessage = ref("Autenticándose en Policía...");
const loading = ref(true);
const open = ref(true);

// Snackbar global (para notificaciones)
const snackbar = ref(false);
const snackbarText = ref("");

const showAlert = (message) => {
  snackbarText.value = message;
  snackbar.value = true;
};

const toggleSidebar = () => (open.value = !open.value);

// ==============================
//  AUTENTICACIÓN
// ==============================
onMounted(async () => {
  // 1. Intentar obtener el código de la URL
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");

  if (localStorage.getItem("access_token") && activatedSession.user_id) {
    loading.value = false;
    return;
  }

  if (code) {
    loaderMessage.value = "Redirigiendo a SnoftIA...";

    try {
      // 2. Intercambiar código por token con el backend
      const data = await api.requestToken(code);

      if (data.access_token) {
        // 3. Guardar sesión exitosa
        localStorage.setItem("access_token", data.access_token);
        // Si el backend devuelve permisos/roles, guardarlos
        if (data.permissions) {
            localStorage.setItem("permissions", JSON.stringify(data.permissions));
        }

        activatedSession.user_id = data.user_id || data.name; // Prefer stable ID if available
        activatedSession.name = data.name;

        // Limpiar URL
        window.history.replaceState({}, document.title, "/");
        loading.value = false;
      } else {
        throw new Error("No access_token in response");
      }
    } catch (error) {
      console.error("Auth error:", error);
      // Si falla, limpiar y redirigir a login
      window.history.replaceState({}, document.title, "/");
      setTimeout(() => api.requestLogin(), 1500);
    }
  } else {
    // 4. Si no hay código ni sesión activa, mandar a login
    setTimeout(() => api.requestLogin(), 1500);
  }
});

// ==============================
//  CARGAR CHAT GROUPS EN SESSION
// ==============================
onMounted(async () => {
  try {
    const response = await api.requestAllSession();
    console.log(response)
    activatedSession.chatGroups = formatChatGroups(response.sessions);
    // eslint-disable-next-line no-unused-vars
  } catch (_) {
    //console.error("API error requestAllSession:", error);
  }
});

// Función para formatear las fechas y agrupar las conversaciones
const formatChatGroups = (sessions) => {
  // Sort sessions by date descending first
  sessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const groups = {
    hoy: { date: "Hoy", chats: [] },
    ayer: { date: "Ayer", chats: [] },
    antiguos: { date: "Más antiguos", chats: [] },
  };

  sessions.forEach((session) => {
    // Ensure accurate date parsing
    const created_at = new Date(session.created_at);
    const createdDate = new Date(created_at);
    createdDate.setHours(0, 0, 0, 0);

    const chat = {
      id: session.session_id,
      chat: session.session_name,
      originalDate: created_at // Keep original for sorting if needed
    };

    if (createdDate.getTime() === today.getTime()) {
      groups.hoy.chats.push(chat);
    } else if (createdDate.getTime() === yesterday.getTime()) {
      groups.ayer.chats.push(chat);
    } else {
      groups.antiguos.chats.push(chat);
    }
  });

  // Filtrar grupos que tengan chats y retornar en orden: Hoy, Ayer, Antiguos
  return [groups.hoy, groups.ayer, groups.antiguos].filter((group) => group.chats.length > 0);
};

// ==============================
//  MANEJO DE CHATS
// ==============================
const router = useRouter();
const chatIdParams = computed(() => router.params.id);

// 🗑 Eliminar conversación
const deleteChat = async (chatId) => {
  console.log("App.vue: deleteChat called for:", chatId);

  // 1. API Call - Only this part should show an error to the user if it fails
  try {
      console.log("App.vue: Calling api.requestDeleteSession...");
      await api.requestDeleteSession(chatId);
      console.log("App.vue: Deleted session successfully");
      showAlert("Conversación eliminada con éxito");
  } catch (error) {
    console.error("App.vue: API Error deleting chat:", error);
    alert("Error al eliminar el chat. Por favor intente nuevamente.");
    return; // Stop here if API call failed
  }

  // 2. UI Update (Post-deletion) - Separate try/catch, just log errors, don't alert
  // The deletion was successful, so we don't want to confuse the user
  try {
      if (activatedSession.chatGroups && Array.isArray(activatedSession.chatGroups)) {
        for (const group of activatedSession.chatGroups) {
          if (group && Array.isArray(group.chats)) {
             const index = group.chats.findIndex(c => c && c.id === chatId);
             if (index !== -1) {
               group.chats.splice(index, 1);
               break; // Found and deleted
             }
          }
        }
      }

      if (chatIdParams.value === chatId) {
        router.push("/");
      }
  } catch (uiError) {
    // UI update failed, but deletion was successful. Just log it.
    console.warn("App.vue: UI update error (deletion was successful):", uiError);
  }
};

const renameChat = async ({ id, name }) => {
  // Snapshot current state for rollback
  const previousGroups = [...activatedSession.chatGroups];

  try {
    // 1. Optimistic update (UI first)
    let found = false;
    // Create new array to force reactivity
    const newGroups = activatedSession.chatGroups.map(group => {
      const chatIndex = group.chats.findIndex(c => c.id === id);
      if (chatIndex !== -1) {
        // Clone the chat object and update name
        const updatedChat = { ...group.chats[chatIndex], chat: name };
        const updatedChats = [...group.chats];
        updatedChats[chatIndex] = updatedChat;
        found = true;
        return { ...group, chats: updatedChats };
      }
      return group;
    });

    if (found) {
        activatedSession.chatGroups = newGroups;
    }

    // 2. API Call in background
    await api.requestRenameSession(id, name);
    console.log("Renamed session successfully");

  } catch (error) {
    console.error("Error renaming chat, reverting:", error);
    // Revert to previous state
    activatedSession.chatGroups = previousGroups;
    alert("Error al renombrar el chat. Por favor intente nuevamente.");
  }
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 1s ease-in-out;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
