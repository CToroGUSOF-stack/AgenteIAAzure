<template>
  <div
    class="user-message !w-full"
    @mouseover="showIcon = true"
    @mouseleave="showIcon = false"
    v-if="is_msg"
  >
    <div class="doc-input" v-if="msg.files && msg.files.length > 0">
      <Doc
        v-for="(file, index) in msg.files"
        :key="index"
        :docPayload="`https://chatdk-backend.agreeablebay-b003088a.eastus2.azurecontainerapps.io/${file?.name ?? file}`"
        :fileName="file?.name ?? file"
      />
    </div>
    <div class="relative max-w-11/12">
      <div v-if="showIcon" class="absolute top-0 left-[-50px]">
        <IconWithTooltip
          :key="isCopied"
          :position="'bottom'"
          :svg="
            isCopied
              ? `<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' class='bi bi-check' viewBox='0 0 16 16'><path d='M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z'/></svg>`
              : `<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='currentColor' class='bi bi-copy' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1z'/></svg>`
          "
          :size="25"
          tooltip="copiar"
          @push-icon="handleCopy"
        />
        <IconWithTooltip
          :key="isCopied"
          :position="'bottom'"
          :svg="`<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='currentColor' class='bi bi-pencil' viewBox='0 0 16 16'><path fill-rule='evenodd' d='M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325'/></svg>`"
          :size="25"
          tooltip="Editar"
          @push-icon="is_msg = false"
        />
      </div>
      <p v-html="formattedMessage" v-if="msg.text != ''" class="w-11/12"></p>
    </div>
  </div>
  <div class="chat-input-user-msg" v-else>
    <!-- <div class="attachment-input-user-msg">
      <Doc v-for="(file, index) in uploadedFiles" :key="index" :docPayload="`https://chatdk-backend.agreeablebay-b003088a.eastus2.azurecontainerapps.io/${file.name}`" />
    </div> -->
    <textarea
      v-model="msg_input_copy"
      class="message-input-user-msg"
      @keydown="handleKeyDown"
    ></textarea>

    <div class="button-group">
      <button class="btn cancel-btn" @click="handleCancelEdit()">
        Cancelar
      </button>
      <button class="btn send-btn" @click="handleSend()">Enviar</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import Doc from "../utils/Doc.vue";
import IconWithTooltip from "../utils/IconTooltip.vue";

const props = defineProps({
  msg: {
    type: Object,
    required: true,
  },
});
const emit = defineEmits(["edited"]);

const showIcon = ref(false);
const isCopied = ref(false);
const is_msg = ref(true);
let msg_input_copy = props.msg.text;

const formattedMessage = computed(() => {
  return props.msg.text.replace(/\n/g, "<br>");
});

const handleCopy = async () => {
  await navigator.clipboard.writeText(props.msg.text || "");
  isCopied.value = true;
  setTimeout(() => {
    isCopied.value = false;
  }, 1000);
};
const handleSend = () => {
  is_msg.value = true;
  props.msg.text = msg_input_copy
  emit('edited', props.msg.id);
};
const handleCancelEdit = () => {
  is_msg.value = true;
  msg_input_copy = props.msg.text;
};
</script>

<style scoped>
.user-message {
  align-self: flex-end;
  color: #333;
  max-width: 70%;
  /* Máximo 50%, pero se ajusta al contenido */
  margin: 0 0 0 auto;
  text-align: left;
  word-wrap: break-word;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  /* Asegura que todo quede alineado a la derecha */
}

.message-container {
  display: flex;
  align-items: center;
  /* Asegura alineación horizontal */
  position: relative;
}

.user-message p {
  border-radius: 8px;
  background-color: #2c8a5d;
  padding: 0.5rem 1rem;
  width: auto;
  /* Se ajusta al contenido */
  max-width: 100%;
  color: rgb(255, 255, 255);
}

.doc-input {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  /* Asegura que los archivos estén alineados a la derecha */
}

.chat-input-user-msg {
  display: flex;
  flex-direction: column;
  /* margin: 0px 100px; */
  padding: 0.5rem 1rem;
  border-radius: 20px;
  background-color: #f1f1f1;
}

.attachment-input-user-msg {
  display: flex;
  flex-direction: row;
  overflow-y: auto;
}

.file-input {
  display: none;
}

.message-input-user-msg {
  width: 100%;
  resize: vertical;
  max-height: 150px;
  min-height: 40px;
  padding: 0.5rem;
  padding-left: 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  background-color: #f1f1f1;
  color: #333;
  overflow-y: auto;
}

.message-input-user-msg::placeholder {
  color: #999;
}

.message-input-user-msg:focus {
  outline: none;
}
.button-group {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 10px;
}

.btn {
  padding: 12px 15px;
  font-size: 12px;
  border: none;
  cursor: pointer;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.cancel-btn {
  border: 1px solid rgb(180, 174, 174);
  background-color: white;
  color: black;
}

.cancel-btn:hover {
  background-color: #f0f0f0;
}

.send-btn {
  border: 1px solid black;
  background-color: black;
  color: white;
}

.send-btn:hover {
  background-color: #333;
}

@media (max-width: 768px) {
  .user-message {
    margin: 0 20px 0 auto;
    max-width: 90%;
  }
  .chat-input-user-msg {
    margin: 0px 20px;
  }
}

@media (min-width: 769px) and (max-width: 1080px) {
  .chat-input-user-msg {
    margin: 0px 60px;
  }
}
</style>
