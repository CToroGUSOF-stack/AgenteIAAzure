import { createRouter, createWebHistory } from "vue-router";
import Chat from "../page/Chat.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: Chat,
      props: () => {
        return {
          newChat: true,
        };
      },
    },
    {
      path: "/c/:id?",
      component: Chat,
      props: () => {
        return {
          newChat: false,
        };
      },
      beforeEnter: (to, _, next) => {
        if (!to.params.id) {
          return next("/");
        }
        next();
      },
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
});

export default router;
