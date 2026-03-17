<script setup>
import { ref } from "vue";

defineProps({
  selectedItem: String,
});

const emit = defineEmits(["update:selectedItem"]);

// const isTemporyChat = ref(false);

const items = ref([
  {
    id: "gpt-4o",
    title: "GPT-4o",
    description: "Modelo multimodal avanzado de OpenAI.",
  },
  {
    id: "o1",
    title: "o1",
    description: "Optimizado para razonamiento complejo.",
  },
  {
    id: "o1-mini",
    title: "o1-mini",
    description: "Versión ligera del modelo o1.",
  },
]);

// const handleToogle = () => (isTemporyChat.value = !isTemporyChat.value);
</script>

<template>
  <div class="text-center !mx-auto lg:!m-0">
    <v-menu>
      <template v-slot:activator="{ props: menu }">
        <button
          class="hover:bg-gray-100 p-2 rounded-lg !text-[#5d5d5d] !font-semibold !text-lg fill-[#5d5d5d] flex flex-row gap-2 items-center"
          v-bind="menu"
        >
          {{ items.find((item) => item.id == selectedItem)?.title }}
          <box-icon type="solid" name="chevron-down"></box-icon>
        </button>
      </template>

      <v-list
        class="!bg-white !mt-2 !w-[320px] !shadow !border !border-neutral-100"
      >
        <v-list-item v-for="item in items" :key="item.id">
          <button
            class="flex flex-row justify-between items-center fill-black cursor-pointer hover:bg-neutral-200 p-2 rounded w-full"
            @click="emit('update:selectedItem', item.id)"
          >
            <div class="text-[#424242] text-sm text-left">
              <h4 class="font-medium">{{ item.title }}</h4>
              <p>{{ item.description }}</p>
            </div>
            <div
              v-if="selectedItem == item.id"
              class="grid place-content-center"
            >
              <box-icon
                type="solid"
                name="check-circle"
                :style="{ width: '20px', height: '20px' }"
              ></box-icon>
            </div>
          </button>
        </v-list-item>

        <!-- <div class="h-[1px] bg-neutral-400 mx-4"></div> -->

        <!-- <div class="px-4 mt-2">
          <button
            class="w-full flex flex-row cursor-pointer hover:bg-[#424242] p-2 py-3 rounded justify-between h-fit"
            @click="handleToogle"
          >
            <div class="text-gray-300 text-sm">
              <h4 class="font-normal">Chat temporal</h4>
            </div>
            <div>
              <label class="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  value=""
                  class="sr-only peer"
                  :checked="isTemporyChat"
                />
                <div
                  class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600 dark:peer-checked:bg-green-600"
                ></div>
              </label>
            </div>
          </button>
        </div> -->
      </v-list>
    </v-menu>
  </div>
</template>
