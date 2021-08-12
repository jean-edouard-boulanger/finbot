import { AuthState } from "./auth-state";

const IDENTITY_LOCAL_KEY = "identity";

export function persistLocal(state: AuthState) {
  localStorage.setItem(
    IDENTITY_LOCAL_KEY,
    JSON.stringify({
      token: state.token,
      account: state.account,
    })
  );
}

export function restoreLocal(currentState: AuthState): AuthState {
  const jsonData = localStorage.getItem(IDENTITY_LOCAL_KEY);
  if (jsonData === null) {
    return { ...currentState };
  }
  try {
    const data = JSON.parse(jsonData);
    return {
      ...currentState,
      token: data.token,
      account: data.account,
    };
  } catch {
    return { ...currentState };
  }
}

export function clearLocal() {
  localStorage.removeItem(IDENTITY_LOCAL_KEY);
}
