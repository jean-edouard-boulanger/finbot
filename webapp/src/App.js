import React from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import { ToastContainer, Slide, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import 'datejs';

import AuthState from "context/auth/auth-state";
import MainContainer from "components/main-container";

import Home from "./routes/main-dashboard";
import Admin from "./routes/admin";
import Navbar from "./components/navigation";
import Auth from "./routes/auth";
import LinkAccounts from "./routes/link-external-account";

toast.configure({
  delay: 500,
});

const App = () => {
  return (
    <AuthState>
      <BrowserRouter>
        <ToastContainer autoClose={7000} transition={Slide} position="bottom-right" />
        <Navbar />
        <MainContainer>
          <Switch>
            <Route exact path="/" render={() => <Home />} />
            <Route exact path="/admin/traces/:guid" render={() => <Admin />} />
            <Route path="/auth" render={() => <Auth />} />
            <Route path="/linked-account" render={() => <LinkAccounts />} />
          </Switch>
        </MainContainer>
      </BrowserRouter>
    </AuthState>
  )
}

export default App;
