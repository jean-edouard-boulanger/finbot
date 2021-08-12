import React, { useReducer, useContext } from "react";

import { Credentials } from "clients/finbot-client/types";
import { ServicesContext } from "contexts";

import AuthContext from "./auth-context";
import authReducer from "./auth-reducer";
import { setAuthHeader } from "./auth-globals";
import { LOGIN_SUCCESS, LOGOUT } from "./auth-actions";
import { restoreLocal } from "./auth-storage";
import { makeFreshAuthState, isValidAuthState } from "./auth-state";


export const AuthProvider = (props: React.HTMLAttributes<HTMLElement>) => {
  let initialState = restoreLocal(makeFreshAuthState());
  if (!isValidAuthState(initialState)) {
    initialState = makeFreshAuthState();
  }
  setAuthHeader(initialState.token);

  const { finbotClient } = useContext(ServicesContext);
  const [state, dispatch] = useReducer(authReducer, initialState);

  async function handleLogin(credentials: Credentials) {
    const { email, password } = credentials;
    const res = await finbotClient?.logInAccount({ email, password });
    dispatch({
      type: LOGIN_SUCCESS,
      payload: res,
    });
  }

  function handleLogout() {
    dispatch({ type: LOGOUT });
  }

  const isAuthenticated = state.token !== null && state.token !== undefined;

  return (
    <AuthContext.Provider
      value={{
        token: state.token,
        account: state.account,

        login: handleLogin,
        logout: handleLogout,
        isAuthenticated,
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
};
