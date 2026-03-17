<template>
  <div class="chat-input shadow-lg border border-gray-200">
    <v-snackbar
      v-model="snackbar"
      timeout="4000"
      variant="tonal"
      location="top"
    >
      {{ snackbarText }}
    </v-snackbar>

    <div class="flex flex-row flex-nowrap gap-2 max-w-full overflow-x-auto">
      <Doc
        v-for="(file, index) in uploadedFiles"
        :key="index"
        :doc-payload="`https://chatdk-backend.agreeablebay-b003088a.eastus2.azurecontainerapps.io/${file.name}`"
        :file-name="file"
        :id="index"
        @update:uploadedFiles="handleDeleteId"
        :is-delete="true"
      />
    </div>
    <textarea
      v-model="newMessage"
      class="message-input"
      placeholder="Escribe tu mensaje..."
      @keydown="handleKeyDown"
      ref="inputRef"
    ></textarea>

    <div class="button-row">
      <div>
        <div class="flex flex-row gap-2">
          <v-tooltip text="Adjuntar archivos" location="top">
            <template v-slot:activator="{ props }">
              <button
                v-bind="props"
                class="attach-btn disabled:opacity-40"
                @click="attachFile"
                :disabled="isActive"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="28"
                  height="28"
                  fill="currentColor"
                  class="bi bi-paperclip"
                  viewBox="0 0 16 16"
                >
                  <path
                    d="M4.5 3a2.5 2.5 0 0 1 5 0v9a1.5 1.5 0 0 1-3 0V5a.5.5 0 0 1 1 0v7a.5.5 0 0 0 1 0V3a1.5 1.5 0 1 0-3 0v9a2.5 2.5 0 0 0 5 0V5a.5.5 0 0 1 1 0v7a3.5 3.5 0 1 1-7 0z"
                  />
                </svg>
                <input
                  type="file"
                  @change="handleFiles"
                  ref="fileInput"
                  class="file-input"
                  :accept="acceptedFiles"
                  multiple
                />
              </button>
            </template>
          </v-tooltip>
          <!-- Search button removed as requested -->
        </div>
      </div>
      <button class="send-btn" @click="sendMessage" v-if="!props.isLoading">
        <IconWithTooltip
          :svg="`<svg xmlns='http://www.w3.org/2000/svg' width='30' height='30' fill='currentColor' class='bi bi-arrow-up-circle-fill' viewBox='0 0 16 16'><path d='M16 8A8 8 0 1 0 0 8a8 8 0 0 0 16 0m-7.5 3.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707z'/></svg>`"
          :size="36"
          tooltip="Enviar"
        />
      </button>
      <button class="stop-btn" @click="stopMessage" v-else>
        <IconWithTooltip
          :svg="`<svg xmlns='http://www.w3.org/2000/svg' width='30' height='30' fill='currentColor' class='bi bi-stop-circle-fi' viewBox='0 0 16 16'><path d='M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M6.5 5A1.5 1.5 0 0 0 5 6.5v3A1.5 1.5 0 0 0 6.5 11h3A1.5 1.5 0 0 0 11 9.5v-3A1.5 1.5 0 0 0 9.5 5z'/></svg>`"
          :size="36"
          tooltip="Detener"
        />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import Doc from "../utils/Doc.vue";
import IconWithTooltip from "../utils/IconTooltip.vue";
import { useRoute } from "vue-router";

const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false,
  },
  isActive: Boolean,
  modelSelect: String,
  isChaningChat: Boolean,
});
const emit = defineEmits([
  "handleButtonIsSearch",
  "stop-message",
  "update:isActive",
]);
const fileInput = ref(null);
const newMessage = ref("");
const uploadedFiles = ref([]);
const inputRef = ref(null);
const snackbar = ref(false);
const snackbarText = ref("");

const acceptedFiles = ".pdf,.doc,.docx,.xlsx,.html,.jpg,.jpeg,.png";
const isSmallScreen = ref(window.innerWidth < 768);

const handleKeyDown = (event) => {
  if (event.key === "Enter") {
    if (props.isLoading) return;
    if (event.shiftKey || isSmallScreen.value) {
      event.preventDefault();
      newMessage.value += "\n";
    } else {
      event.preventDefault();
      sendMessage();
    }
  }
};

const handleDeleteId = (id) => {
  uploadedFiles.value = uploadedFiles.value.filter((_, index) => index != id);
};

const route = useRoute();

const sendMessage = () => {
  if (!newMessage.value.trim() && uploadedFiles.value.length === 0) return;
  emit(
    "send-message",
    {
      text: newMessage.value.trim(),
      files: uploadedFiles.value.length > 0 ? [...uploadedFiles.value] : null,
      id: crypto.randomUUID(),
    },
    false,
    route.params.id || crypto.randomUUID()
  );

  newMessage.value = "";
  uploadedFiles.value = []; // Limpiar archivos después de enviar
};

const stopMessage = () => {
  emit("stop-message", route.params.id);
};

const attachFile = () => {
  fileInput.value.click();
};

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const MAX_FILES = 10;

const handleFiles = (event) => {
  const files = event.target.files || event.dataTransfer.files;

  let acceptedCount = 0;
  let rejectedCount = 0;
  let oversizedFiles = [];

  Array.from(files).forEach((file) => {
    // Si ya llegamos al límite de archivos, lo rechazamos
    if (uploadedFiles.value.length >= MAX_FILES) {
      rejectedCount++;
      return;
    }

    // Si el archivo es muy grande
    if (file.size > MAX_FILE_SIZE) {
      oversizedFiles.push(file.name);
      return;
    }

    let type = "Unknown";
    const name = file.name.toLowerCase();

    if (
      name.endsWith(".png") ||
      name.endsWith(".jpg") ||
      name.endsWith(".jpeg")
    ) {
      type = "image";
    } else if (name.endsWith(".wav")) {
      type = "audio";
    } else if (name.endsWith(".pdf")) {
      type = "pdf";
    } else if (name.endsWith(".doc") || name.endsWith(".docx")) {
      type = "word";
    } else if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
      type = "excel";
    }

    uploadedFiles.value.push({ type, name: file.name, file });
    acceptedCount++;
  });

  // Construye mensajes combinados
  const messages = [];

  if (acceptedCount > 0) {
    messages.push(
      `Se aceptaron ${acceptedCount} archivo${acceptedCount > 1 ? "s" : ""}.`
    );
  }

  if (rejectedCount > 0) {
    messages.push(
      `Se rechazaron ${rejectedCount} archivo${
        rejectedCount > 1 ? "s" : ""
      } por exceder el límite de 10.`
    );
  }

  if (oversizedFiles.length > 0) {
    messages.push(
      `Estos archivos exceden los 100MB: ${oversizedFiles.join(", ")}`
    );
  }

  if (messages.length > 0) {
    showAlert(messages.join(" "));
  }

  event.target.value = "";
};

const showAlert = (message) => {
  snackbarText.value = message;
  snackbar.value = true;
};

const updateScreenSize = () => {
  isSmallScreen.value = window.innerWidth <= 600;
};

// Agregar y remover el event listener para detectar cambios de tamaño
onMounted(() => {
  window.addEventListener("resize", updateScreenSize);
});

onUnmounted(() => {
  window.removeEventListener("resize", updateScreenSize);
});
watch(
  () => props.isChaningChat,
  () => {
    newMessage.value = "";
    uploadedFiles.value = [];
    inputRef.value?.focus();
  }
);
</script>

<style scoped>
.chat-input {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background-color: #fff;
  width: 100%;
}

.attachment-input {
  display: flex;
  flex-direction: row;
  overflow-x: auto;
  overflow-y: hidden;
  gap: 0.5rem; /* opcional: espacio entre archivos */
  width: 100% !important;
}

.file-input {
  display: none;
}

.message-input {
  width: 100%;
  resize: vertical;
  max-height: 150px;
  min-height: 40px;
  padding: 0.5rem;
  padding-left: 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  background-color: white;
  color: #333;
  overflow-y: auto;
  resize: none;
}

.message-input::placeholder {
  color: #999;
}

.message-input:focus {
  outline: none;
}

.button-row {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.internet-btn {
  padding: 12px 15px;
  font-size: 12px;
  border: none;
  cursor: pointer;
  border-radius: 20px;
  transition: all 0.3s ease;
  border: 1px solid rgb(180, 174, 174);
  background-color: white;
  color: black;
}

.attach-btn {
  background: none;
  border: none;
  color: #052b8d;
  cursor: pointer;
}

.attach-btn:hover {
  color: #052b8d;
}

.stop-btn,
.send-btn {
  color: #006937;
  border: none;
}

.send-btn:hover {
  color: #006937;
}
</style>

<!--
Tasks
- [x] al cambiar de chat, limpiar el input y quitar los archivos
- [x] Revisar tooltips de Adjuntar archivos
- [x] Limitar la subida de aarchivos al frontend ya sea por tamaño o cantidad
- [ ] Agregar marca de agua al sidebar
-->
