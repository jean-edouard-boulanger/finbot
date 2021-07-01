import { setAuthHeader } from "./auth-globals";
import { LOGIN_SUCCESS, LOGOUT } from "./auth-actions";
import { persistLocal, clearLocal } from "./auth-storage";

export default (state, action) => {
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
