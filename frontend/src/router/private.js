import { createMemoryHistory, createRouter } from "vue-router";
import Chat from "../page/Chat.vue";

export const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: "/", component: Chat },
    { path: "/c/:id", component: Chat },
  ],
});
