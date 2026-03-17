<template>
  <div>
    <div class="card relative">
      <button
        v-show="file"
        class="absolute right-1 top-1 -translate-y-1/2 translate-x-1/2 rounded-full transition-colors border-[3px] border-[#f4f4f4] bg-black p-[2px] fill-white h-[20px] w-[20px] grid place-content-center text-white"
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 29 28"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          class="icon-xs"
        >
          <path
            fill-rule="evenodd"
            clip-rule="evenodd"
            d="M7.30286 6.80256C7.89516 6.21026 8.85546 6.21026 9.44775 6.80256L14.5003 11.8551L19.5529 6.80256C20.1452 6.21026 21.1055 6.21026 21.6978 6.80256C22.2901 7.39485 22.2901 8.35515 21.6978 8.94745L16.6452 14L21.6978 19.0526C22.2901 19.6449 22.2901 20.6052 21.6978 21.1974C21.1055 21.7897 20.1452 21.7897 19.5529 21.1974L14.5003 16.1449L9.44775 21.1974C8.85546 21.7897 7.89516 21.7897 7.30286 21.1974C6.71057 20.6052 6.71057 19.6449 7.30286 19.0526L12.3554 14L7.30286 8.94745C6.71057 8.35515 6.71057 7.39485 7.30286 6.80256Z"
            fill="currentColor"
          ></path>
        </svg>
      </button>
      <div class="card-content">
        <div class="file-icon" :style="{ backgroundColor: backgroundColor }">
          <span>{{ getFileType(docPayload) }}</span>
        </div>
        <div class="file-info flex justify-between items-center">
          <p class="file-name">{{ getFileName(docPayload) }}</p>
          <button
            v-show="isDelete"
            class="grid place-content-center ml-auto p-1 rounded-full cursor-pointer hover:opacity-50"
            @click="emit('update:uploadedFiles', props.id)"
          >
            <box-icon name="x"></box-icon>
          </button>
        </div>
        <!-- <button class="download-arrow" @click="openFile(docPayload)" v-if="getFileOwn(docPayload)">
          <i class="fa fa-external-link"></i>
        </button> -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  docPayload: {
    name: String,
    type: String,
    required: true,
  },
  fileName: String,
  id: Number,
  isDelete: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:uploadedFiles"]);

const getFileType = (fileName) => {
  const extension = fileName.split(".").pop().toUpperCase();
  return extension || "DOC";
};

const getFileName = (fileName) => {
  return fileName.split("@").pop().split("/").pop().split(".").shift();
};

// const getFileOwn = (fileName) => {
//     const isNotFile = (fileName.split('@').shift() != 'file')
//     return isNotFile
// };

// const openFile = (fileUrl) => {
//     window.open(fileUrl, '_blank');
// };

const getBackgroundColor = (fileName) => {
  const extension = getFileType(fileName);
  switch (extension) {
    case "PDF":
      return "rgb(255, 85, 136)";
    case "DOC":
    case "DOCX":
      return "rgb(79, 165, 236)";
    case "XLS":
    case "CSV":
    case "XLSX":
      return "rgb(26 225 21)";
    case "PPT":
    case "PPTX":
      return "rgb(230 162 29)";
    case "JPG":
    case "JPEG":
    case "PNG":
    case "GIF":
    case "BMP":
      return "rgb(54 203 234)";
    case "TXT":
      return "#a29fa4";
    case "HTML":
      return "rgb(255, 0, 89)";
    default:
      return "rgb(197, 197, 197)";
  }
};

const backgroundColor = computed(() => {
  return getBackgroundColor(props.docPayload);
});
</script>

<style scoped>
.card {
  display: flex;
  align-items: center;
  background-color: #ffffff9a;
  border: 1px solid #dfdfdf;
  border-radius: 16px;
  padding: 7px;
  max-width: 400px;
  margin: 8px 3px;
  margin-top: 0;
  gap: 12px;
  font-family: Arial, sans-serif;
  /* user-select: none; */
}

.card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.file-icon {
  background-color: #f4f4f4;
  border: 1px solid #ccc;
  border-radius: 10px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.file-info {
  flex: 1;
  margin-left: 12px;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0;
  width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.download-arrow {
  background-color: var(--secundary-color);
  color: var(--primary-color);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.download-arrow:hover {
  background-color: var(--primary-color);
  color: var(--secundary-color);
}

.bg-blue {
  background-color: rgb(79, 165, 236);
  color: white;
}
.bg-green {
  background-color: rgb(78, 241, 78);
  color: white;
}
.bg-red {
  background-color: rgb(197, 197, 197);
  color: white;
}
</style>
