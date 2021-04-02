import React, { useReducer, useContext } from "react";

import { ServicesContext } from "contexts";

import AuthContext from "./auth-context";
import authReducer from "./auth-reducer";
import { setAuthHeader } from "./auth-globals";
import { LOGIN_SUCCESS, LOGOUT } from "./auth-actions";
import { restoreLocal } from "./auth-storage";

const isValidAuthState = (state) => {
  if (state.token === null && state.account === null) {
    return true;
  }
  return (
    state.token !== null &&
    state.token !== undefined &&
    state.account !== null &&
    state.account !== undefined
  );
};

const makeFreshAuthState = () => {
  return {
    token: null,
    account: null,
  };
};

export const AuthProvider = (props) => {
  let initialState = restoreLocal(makeFreshAuthState());
  if (!isValidAuthState(initialState)) {
    initialState = makeFreshAuthState();
  }
  setAuthHeader(initialState.token);

  const { finbotClient } = useContext(ServicesContext);
  const [state, dispatch] = useReducer(authReducer, initialState);

  async function handleLogin(formData) {
    const { email, password } = formData;
    const res = await finbotClient.logInAccount({ email, password });
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
