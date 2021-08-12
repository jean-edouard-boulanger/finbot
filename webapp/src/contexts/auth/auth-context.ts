import { UserAccount, Credentials } from "clients/finbot-client/types";
import { createContext } from "react";

type AuthContextProps = {
  token: string | null;
  account: UserAccount | null;
  login(credentials: Credentials): Promise<void>;
  logout(): void;
  isAuthenticated: boolean;
};

export const AuthContext = createContext<Partial<AuthContextProps>>({});

export default AuthContext;
