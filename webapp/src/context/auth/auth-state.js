import React, {useReducer} from 'react';

import AuthContext from './auth-context';
import authReducer from './auth-reducer';
import FinbotClient from "clients/finbot-client";
import {
  REGISTER_SUCCESS,
  REGISTER_FAIL,
  LOGIN_SUCCESS,
  LOGIN_FAIL,
  LOGOUT,
  CLEAR_ERRORS
} from "./auth-types"
import { restoreLocal } from "./auth-storage";

const AuthState = props => {
  const initialState = restoreLocal({
    token: null,
    isAuthenticated: false,
    loading: true,
    accountID: null,
    error: null
  });

  const [state, dispatch] = useReducer(authReducer, initialState);

  let finbot_client = new FinbotClient();

  async function handleRegister(formData) {
    const {email, password, full_name, settings} = formData;

    try {
      const res = await finbot_client.registerAccount({email, password, full_name, settings});
      dispatch({
        type: REGISTER_SUCCESS,
        payload: res.user_account
      });
    } catch (err) {
      dispatch({
        type: REGISTER_FAIL,
        payload: err
      });
    }
  }

  async function handleLogin(formData) {
    const {email, password} = formData;

    try {
      const res = await finbot_client.logInAccount({email, password});
      dispatch({
        type: LOGIN_SUCCESS,
        payload: res
      });
    } catch (err) {
      dispatch({
        type: LOGIN_FAIL,
        payload: err
      });
    }
  }

  function handleLogout() {
    dispatch({type: LOGOUT})
  }

  function handleClearErrors() {
    dispatch({type: CLEAR_ERRORS})
  }

  return (
    <AuthContext.Provider
      value={{
        token: state.token,
        isAuthenticated: state.isAuthenticated,
        loading: state.loading,
        error: state.error,
        accountID: state.accountID,
        register: handleRegister,
        login: handleLogin,
        logout: handleLogout,
        clearErrors: handleClearErrors
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
};

export default AuthState;
