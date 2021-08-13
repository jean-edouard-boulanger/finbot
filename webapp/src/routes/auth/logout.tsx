import { useContext } from "react";

import { AuthContext } from "contexts";

export const Logout = () => {
  const { logout } = useContext(AuthContext);
  logout!();
  return null;
};
