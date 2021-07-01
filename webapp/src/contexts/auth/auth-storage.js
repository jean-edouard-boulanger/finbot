const IDENTITY_LOCAL_KEY = "identity";

export function persistLocal(state) {
  localStorage.setItem(
    IDENTITY_LOCAL_KEY,
    JSON.stringify({
      token: state.token,
      account: state.account,
    })
  );
}

export function restoreLocal(state) {
  const jsonData = localStorage.getItem(IDENTITY_LOCAL_KEY);
  if (jsonData === null) {
    return { ...state };
  }
  try {
    const data = JSON.parse(jsonData);
    return {
      ...state,
      token: data.token,
      account: data.account,
    };
  } catch {
    return { ...state };
  }
}

export function clearLocal() {
  localStorage.removeItem(IDENTITY_LOCAL_KEY);
}
