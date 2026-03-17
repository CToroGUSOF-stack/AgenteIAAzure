import axios from "axios";

const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "https://aca-chatagent-eastus2.niceisland-39c955b7.eastus2.azurecontainerapps.io/api";
const token = "dev_token_bypass";

const apiClientMultipart = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "multipart/form-data",
  },
});
const apiClientCommon = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClientCommon.interceptors.response.use(
  (response) => response,

  (error) => {
    // const status = error.response?.status;
    // const detail = error.response?.data?.detail;

    // if (
    //   (status === 401 || status === 403) &&
    //   (detail === "Token inválido" ||
    //     detail === "Token expirado" ||
    //     detail === "Not authenticated" ||
    //     detail === "Token inválido o malformado" ||
    //     detail === "Claims inválidos")
    // ) {
    //   localStorage.removeItem("access_token");
    //   window.location.href = `${BASE_URL}/auth/login`;
    // }
    return Promise.reject(error);
  }
);

export default {
  async requestToken(code) {
    const response = await apiClientCommon.get(`/auth/token?code=${code}`);
    return response.data;
  },
  async requestLogin() {
    // window.location.href = `${BASE_URL}/auth/login`;
  },
  async requestAllSession() {
    ;
    if (!token) {
      // Return empty structure or reject, but do not send request
      return Promise.reject("No auth token");
    }
    const response = await apiClientCommon.get("/chat/sessions", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
  async requestOneSession(session_id) {
    ;
    if (!token) return Promise.reject("No auth token");
    const response = await apiClientCommon.get("/chat/get_one_session", {
      params: {
        session_id: session_id,
      },
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
  async requestDeleteSession(session_id) {
    console.log("api.js: requestDeleteSession called for:", session_id);
    if (!token) {
      console.error("api.js: No auth token found");
      return Promise.reject("No auth token");
    }
    const response = await apiClientCommon.delete(
      `/chat/delete_one_session/${session_id}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },
  async requestChat(
    user_query,
    msg_id,
    modifier,
    search_tool,
    model_name = "gpt-5-mini",
    session_id,
    session_name
  ) {
    const requestData = {
      query: user_query,
      session_id: session_id,
      // session_name: session_name,
      // flag_modifier: modifier,
      // model_name,
      // search_tool: model_name == "o1-mini" ? false : search_tool,
    };
    ;
    if (!token) return Promise.reject("No auth token");
    const response = await apiClientCommon.post("/chat/message", requestData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
  async requestAttachment(attachment) {
    ;
    const response = await apiClientMultipart.post(
      "/chat/attachment",
      attachment,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },
  async requestRenameSession(session_id, new_name) {
    ;
    if (!token) return Promise.reject("No auth token");
    const response = await apiClientCommon.patch(
      `/chat/sessions/${session_id}`,
      { session_name: new_name },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },
  // requestVote removed
};
