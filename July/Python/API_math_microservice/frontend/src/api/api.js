import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  withCredentials: true,
  headers: {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,OPTIONS",
    "Content-Type": "application/json",
  },
});

export default api;

export const putere = async (x, y) => {
  const resp = await api.post("/putere", { x, y });
  return resp.data.result;
};

export const fibo = async (n) => {
  const resp = await api.post("/fibo", { n });
  return resp.data.result;
};

export const factorial = async (n) => {
  const resp = await api.post("/factorial", { n });
  return resp.data.result;
};

export const prime = async (n, token) => {
  const resp = await api.post(
    "/prime",
    { n: Number(n)},
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return resp.data;
};

export const login_user = async (body) => {
  const resp = await api.post("/login", body);
  console.log(resp);

  return resp;
};

export const getUserByID = async (id) => {
  const resp = await api.post(`/user`, { user_id: id });
  console.log(resp);

  return resp;
};