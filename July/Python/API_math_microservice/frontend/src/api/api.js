import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const putere = async (x, y) => {
  const resp = await axios.post(`${BASE_URL}/putere`, { x, y });
  return resp.data.result;
};

export const fibo = async (n) => {
  const resp = await axios.post(`${BASE_URL}/fibo`, { n });
  return resp.data.result;
};

export const factorial = async (n) => {
  const resp = await axios.post(`${BASE_URL}/factorial`, { n });
  return resp.data.result;
};