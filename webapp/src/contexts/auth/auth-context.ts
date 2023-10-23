import { createContext } from "react";

import { Credentials } from "./auth-types";

type AuthContextProps = {
  userAccountId: number | null;
  accessToken: string | null;
  refreshToken: string | null;
  login(credentials: Credentials): Promise<void>;
  logout(): void;
};

export const AuthContext = createContext<Partial<AuthContextProps>>({});

export default AuthContext;
