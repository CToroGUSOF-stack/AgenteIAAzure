<template>
  <MainMenu
    :modelSelect="selectedModel"
    class="pb-4 px-10"
  />
</template>

<script setup>
import { ref } from "vue";

import MainMenu from "../components/MainMenu.vue";
const selectedModel = ref("gpt-5-mini");
</script>
