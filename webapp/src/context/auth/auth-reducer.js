import {
  RESTORE_IDENTITY,
  REGISTER_SUCCESS,
  REGISTER_FAIL,
  AUTH_ERROR,
  LOGIN_SUCCESS,
  LOGIN_FAIL,
  LOGOUT,
  CLEAR_ERRORS
} from './auth-types';
import { persistLocal, clearLocal, restoreLocal } from "./auth-storage";


export default (state, action) => {
  switch (action.type) {
    case RESTORE_IDENTITY: {
      return restoreLocal(state);
    }
    case REGISTER_SUCCESS: {
      clearLocal();
      return {
        ...state,
        loading: false,
        accountID: action.payload.id
      };
    }
    case LOGIN_SUCCESS: {
      const newState = {
        ...state,
        isAuthenticated: true,
        loading: false,
        token: action.payload.auth.access_token,
        accountID: action.payload.account.id
      };
      persistLocal(newState);
      return newState;
    }
    case REGISTER_FAIL:
    case AUTH_ERROR:
    case LOGIN_FAIL: {
      clearLocal();
      return {
        ...state,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: action.payload,
        accountID: null
      };
    }
    case LOGOUT: {
      clearLocal();
      return {
        ...state,
        token: null,
        isAuthenticated: false,
        loading: false,
        accountID: null
      };
    }
    case CLEAR_ERRORS: {
      return {
        ...state,
        error: null
      };
    }
    default:
      return {...state};
  }
};
