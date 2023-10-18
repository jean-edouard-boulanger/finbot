import React, { useContext, useEffect, useRef, useState } from "react";

import { Credentials } from "clients/finbot-client/types";
import { ServicesContext } from "contexts";

import AuthContext from "./auth-context";
import { AuthState } from "./auth-state";
import {
  loadAuthStateFromLocalStorage,
  clearAuthStateFromLocalStorage,
  saveAuthStateInLocalStorage,
} from "./auth-storage";

interface AuthProviderProps {
  children?: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = (props) => {
  const { finbotClient } = useContext(ServicesContext);
  const [authState, _setAuthState] = useState<AuthState | null>(null);
  const responseInterceptorIdRef = useRef<number | null>(null);

  const updateAuthState = (newAuthState: AuthState | null) => {
    const axiosInstance = finbotClient!.axiosInstance;
    if (newAuthState !== null && responseInterceptorIdRef.current === null) {
      responseInterceptorIdRef.current =
        axiosInstance.interceptors.response.use(
          (value) => value,
          (error) => {
            if (error.response.status === 401) {
              updateAuthState(null);
            }
            return error;
          },
        );
    }
    if (newAuthState === null && responseInterceptorIdRef.current !== null) {
      axiosInstance.interceptors.response.eject(
        responseInterceptorIdRef.current,
      );
      responseInterceptorIdRef.current = null;
    }
    if (newAuthState !== null) {
      saveAuthStateInLocalStorage(newAuthState);
      axiosInstance.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${newAuthState.accessToken}`;
    } else {
      clearAuthStateFromLocalStorage();
      delete axiosInstance.defaults.headers.common["Authorization"];
    }
    _setAuthState(newAuthState);
  };

  useEffect(() => {
    updateAuthState(loadAuthStateFromLocalStorage());
  }, []);

  function logout() {
    updateAuthState(null);
  }

  async function login(credentials: Credentials) {
    const { email, password } = credentials;
    const authResponse = await finbotClient!.logInAccount({ email, password });
    const authState: AuthState = {
      accessToken: authResponse.auth.access_token,
      refreshToken: authResponse.auth.refresh_token,
      userAccountId: authResponse.account.id,
    };
    updateAuthState(authState);
  }

  return (
    <AuthContext.Provider
      value={{
        userAccountId: authState?.userAccountId ?? null,
        login,
        logout,
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
};
