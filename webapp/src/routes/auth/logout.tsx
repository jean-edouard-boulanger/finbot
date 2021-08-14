import React, { useContext } from "react";

import { AuthContext } from "contexts";

export const Logout: React.FC<Record<string, never>> = () => {
  const { logout } = useContext(AuthContext);
  logout!();
  return null;
};
