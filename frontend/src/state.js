import { reactive } from "vue";

export const activatedSession = reactive({
  // session_id: null,
  // session_name: "",
  // name: "",
  user_id: null,
  allMsgs: { "": [] },
  chatGroups: [],
});

export const isLoadingDeleteMap = reactive({});
