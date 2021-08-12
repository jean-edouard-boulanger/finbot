import axios from "axios";

export const setAuthHeader = (token?: string | null) => {
  if (!token) {
    delete axios.defaults.headers.common["Authorization"];
    return;
  }
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
};
