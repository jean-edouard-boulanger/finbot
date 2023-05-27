import React, { useContext, useEffect, useState } from "react";

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
  const [authState, setAuthStateImpl] = useState<AuthState | null>(() => {
    return loadAuthStateFromLocalStorage();
  });

  const setAuthState = (newAuthState: AuthState | null) => {
    if (newAuthState !== null) {
      saveAuthStateInLocalStorage(newAuthState);
    } else {
      clearAuthStateFromLocalStorage();
    }
    setAuthStateImpl(newAuthState);
  };

  function logout() {
    setAuthState(null);
  }

  useEffect(() => {
    const axiosInstance = finbotClient!.axiosInstance;
    axiosInstance.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        if (error.response.status === 401) {
          setAuthState(null);
        }
        return error;
      }
    );
  }, [finbotClient]);

  useEffect(() => {
    const axiosInstance = finbotClient!.axiosInstance;
    if (authState !== null) {
      axiosInstance.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${authState.accessToken}`;
    } else {
      delete axiosInstance.defaults.headers.common["Authorization"];
    }
  }, [finbotClient, authState]);

  async function login(credentials: Credentials) {
    const { email, password } = credentials;
    const authResponse = await finbotClient!.logInAccount({ email, password });
    const authState: AuthState = {
      accessToken: authResponse.auth.access_token,
      refreshToken: authResponse.auth.refresh_token,
      userAccountId: authResponse.account.id,
    };
    setAuthState(authState);
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
