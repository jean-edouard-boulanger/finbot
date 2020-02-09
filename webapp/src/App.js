import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import 'datejs';

import React, { useState, useEffect } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";

import LinkedAccountContext from "context/linked-account-context";
import LinkedAccountState from "context/linked-account-state";
import Navigation from "components/navigation";

import Auth from "routes/auth";
import MainDashboard from "routes/main-dashboard";
import LinkExternalAccount from "routes/link-external-account"


const App = () => {
  const [user, setUser] = useState(_setUser(true));
  const { providersList } = LinkedAccountContext;

  useEffect(() => {
    _setUser();
  }, []);

  function _resetUser() {
    console.log("in reset user")
    setUser({ user: null });
  }

  //hardcode token for now as long as no token from serverside available
  function _setUser(init) {
    const token = localStorage.getItem('identity');
    if (token) {
      console.log({ token })
      // const decoded = jwtDecode(token)
      // console.log({ decoded })
      // delete decoded.iat
      // if (init) return decoded
      if (init) return token;
      // setUser({ user: decoded })
      setUser({ user: token })
    } else {
      return null;
    }
  }

  return (
    <LinkedAccountState>
      <BrowserRouter>
        <div>
          <Navigation user={user} providers={providersList} />
          <Switch>
            <Route exact path="/" render={() => <MainDashboard user={user} />} />
            <Route path="/auth" render={() => <Auth setUser={_setUser} resetUser={_resetUser} />} />
            <Route path="/external-accounts/link" render={() => <LinkExternalAccount providers={providersList} />} />
          </Switch>
        </div>
      </BrowserRouter>
    </LinkedAccountState>
  )
}


export default App;
