import React, {useEffect, useContext} from "react";
import {Route, Switch} from "react-router-dom";
import {withRouter} from "react-router";
import {toast} from 'react-toastify';

import AuthContext from "context/auth/auth-context";
import Logout from "./logout";
import LoginForm from "./login-form";
import SignupForm from "./signup-form";

const Auth = (props) => {
  const authContext = useContext(AuthContext);
  const {clearErrors, isAuthenticated, error} = authContext;

  useEffect(() => {
    if (isAuthenticated) {
      props.history.push("/");
    }
    else {
      props.history.push("/auth/log-in");
    }
  }, [isAuthenticated, props.history])

  useEffect(() => {
    if (error) {
      toast.error(error, {});
      clearErrors();
    }
  }, [error, clearErrors])

  return (
    <div>
      <Switch>
        <Route
          exact
          path="/auth/sign-up"
          render={() => <SignupForm />}
        />
        <Route
          exact
          path="/auth/log-in"
          render={() => <LoginForm />}
        />
        <Route
          exact
          path="/auth/logout"
          render={() => <Logout />}
        />
      </Switch>
    </div>
  );
}


export default withRouter(Auth);