import { Credentials } from "clients/finbot-client/types";
import { createContext } from "react";

type AuthContextProps = {
  userAccountId: number | null;
  login(credentials: Credentials): Promise<void>;
  logout(): void;
};

export const AuthContext = createContext<Partial<AuthContextProps>>({});

export default AuthContext;
