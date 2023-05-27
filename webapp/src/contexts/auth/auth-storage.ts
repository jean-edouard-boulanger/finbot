import { AuthState } from "./auth-state";

const IDENTITY_LOCAL_KEY = "finbot:auth:state";

function deserializeAuthState(data: Record<string, any>): AuthState | null {
  if (
    typeof data.accessToken === "string" &&
    typeof data.refreshToken === "string" &&
    Number.isInteger(data.userAccountId)
  ) {
    return {
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      userAccountId: data.userAccountId,
    };
  }
  return null;
}

export function saveAuthStateInLocalStorage(authState: AuthState): void {
  localStorage.setItem(IDENTITY_LOCAL_KEY, JSON.stringify(authState));
}

export function clearAuthStateFromLocalStorage(): void {
  localStorage.removeItem(IDENTITY_LOCAL_KEY);
}

export function loadAuthStateFromLocalStorage(): AuthState | null {
  const rawAuthState = localStorage.getItem(IDENTITY_LOCAL_KEY);
  if (rawAuthState === null) {
    return null;
  }
  try {
    return deserializeAuthState(JSON.parse(rawAuthState));
  } catch {
    clearAuthStateFromLocalStorage();
    return null;
  }
}
