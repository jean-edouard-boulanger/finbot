import axios from "axios";

export const setAuthHeader = (token) => {
  if(!token) {
    delete axios.defaults.headers.common['Authorization'];
    return;
  }
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}
