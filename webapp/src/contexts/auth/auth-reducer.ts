import { AuthState } from "./auth-state";
import { setAuthHeader } from "./auth-globals";
import { LOGIN_SUCCESS, LOGOUT } from "./auth-actions";
import { persistLocal, clearLocal } from "./auth-storage";

export interface Action {
  type: string;
  payload?: any;
}

export default (state: AuthState, action: Action): AuthState => {
  switch (action.type) {
    case LOGIN_SUCCESS: {
      const accessToken = action.payload.auth.access_token;
      setAuthHeader(accessToken);
      const newState = {
        ...state,
        token: accessToken,
        account: action.payload.account,
      };
      persistLocal(newState);
      return newState;
    }
    case LOGOUT: {
      clearLocal();
      setAuthHeader(null);
      return {
        ...state,
        token: null,
        account: null,
      };
    }
    default:
      return { ...state };
  }
};
