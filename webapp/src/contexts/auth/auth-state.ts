export interface AuthState {
  token: string | null;
  account: any;
}

export const makeFreshAuthState = (): AuthState => {
  return {
    token: null,
    account: null,
  };
};

export const isValidAuthState = (state: any): boolean => {
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
