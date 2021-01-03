import React, {useContext} from "react";

import AuthContext from "context/auth/auth-context";

import {Redirect} from 'react-router-dom'
import {withRouter} from "react-router";


const Logout = () => {
  const authContext = useContext(AuthContext);
  authContext.logout();
  return (
    <Redirect to="/auth/log-in"/>
  );
}

export default withRouter(Logout)