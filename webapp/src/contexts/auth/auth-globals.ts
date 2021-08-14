import axios from "axios";

export const setAuthHeader = (token?: string | null): void => {
  if (!token) {
    delete axios.defaults.headers.common["Authorization"];
    return;
  }
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
};
