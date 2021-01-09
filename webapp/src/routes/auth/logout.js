import {useContext} from "react";

import AuthContext from "contexts/auth/auth-context";


export const Logout = () => {
  const {logout} = useContext(AuthContext);
  logout();
  return null;
}
