import React, { useEffect, useState } from "react";

import {
  makeApi,
  AuthenticationApi,
  LoginRequest,
  useResponseInterceptor,
} from "clients";

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
  const [authState, _setAuthState] = useState<AuthState | null>(null);
  const [responseInterceptor] = useResponseInterceptor();

  const updateAuthState = (newAuthState: AuthState | null) => {
    if (newAuthState !== null) {
      saveAuthStateInLocalStorage(newAuthState);
    } else {
      clearAuthStateFromLocalStorage();
    }
    _setAuthState(newAuthState);
  };

  useEffect(() => {
    responseInterceptor.subscribe((response) => {
      if (response.status === 401) {
        logout();
      }
    });
    return () => {
      responseInterceptor.unsubscribe();
    };
  }, [responseInterceptor]);

  useEffect(() => {
    updateAuthState(loadAuthStateFromLocalStorage());
  }, []);

  function logout() {
    updateAuthState(null);
  }

  async function login(credentials: LoginRequest) {
    const api = makeApi(AuthenticationApi);
    const response = await api.authenticateUser({
      loginRequest: credentials,
    });
    const authState: AuthState = {
      accessToken: response.auth.accessToken,
      refreshToken: response.auth.refreshToken,
      userAccountId: response.account.id,
    };
    updateAuthState(authState);
  }

  return (
    <AuthContext.Provider
      value={{
        userAccountId: authState?.userAccountId ?? null,
        accessToken: authState?.accessToken ?? null,
        refreshToken: authState?.refreshToken ?? null,
        login,
        logout,
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
};
