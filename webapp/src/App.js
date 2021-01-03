import React from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import { ToastContainer, Slide, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import 'datejs';

import AuthState from "context/auth-state";
import LinkedAccountState from "context/linked-account-state";
import MainContainer from "components/main-container";

//core components
import Home from "./routes/main-dashboard";
import Admin from "./routes/admin";
import Navbar from "./components/navigation";
import Auth from "./routes/auth";
import LinkedAccounts from "./routes/link-external-account";

toast.configure({
  delay: 500,
});

const App = () => {
  return (
    <AuthState>
      <LinkedAccountState>
        <BrowserRouter>
          <ToastContainer autoClose={7000} transition={Slide} position="bottom-right" />
          <Navbar />
          <MainContainer>
            <Switch>
              <Route exact path="/" render={() => <Home />} />
              <Route exact path="/admin/traces/:guid" render={() => <Admin />} />
              <Route path="/auth" render={() => <Auth />} />
              <Route path="/linked-account" render={() => <LinkedAccounts />} />
              {/* <Route component={Error}/> */}
            </Switch>
          </MainContainer>
        </BrowserRouter>
      </LinkedAccountState>
    </AuthState>
  )
}

export default App;
