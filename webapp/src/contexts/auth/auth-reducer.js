import axios from 'axios';
import {
  LOGIN_SUCCESS,
  LOGOUT
} from './auth-actions';
import { persistLocal, clearLocal } from "./auth-storage";


const setAuthHeader = (token) => {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

const resetAuthHeader = () => {
  delete axios.defaults.headers.common['Authorization'];
}

export default (state, action) => {
  switch (action.type) {
    case LOGIN_SUCCESS: {
      const accessToken = action.payload.auth.access_token;
      setAuthHeader(accessToken);
      const newState = {
        ...state,
        token: accessToken,
        account: action.payload.account
      };
      persistLocal(newState);
      return newState;
    }
    case LOGOUT: {
      clearLocal();
      resetAuthHeader();
      return {
        ...state,
        token: null,
        account: null
      };
    }
    default:
      return {...state};
  }
};
