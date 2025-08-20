import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;
    const url = original?.url || "";

    // Nu încerca refresh pentru /auth/refresh sau /auth/login (evităm bucle)
    const isRefreshRoute = url.includes("/auth/refresh");
    const isLoginRoute = url.includes("/auth/login");

    if (
      status === 401 &&
      !original._retry &&
      !isRefreshRoute &&
      !isLoginRoute
    ) {
      original._retry = true;
      try {
        await api.post("/auth/refresh"); // încearcă o singură dată
        return api(original); // re-execută requestul original
      } catch (e) {
        // refresh eșuat -> lasă eroarea să fie tratată (ex: redirect la /login)
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
