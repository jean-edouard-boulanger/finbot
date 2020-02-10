import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"
import { ToastContainer, Slide, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import React, { useEffect, useState } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';

import AuthState from "./context/AuthState";
import LinkedAccountState from "./context/LinkedAccountState";
import AlertState from './context/AlertState';

//core components
import Home from "./Home/Home";
import Navbar from "./Navbar/Navbar";
import Auth from "./Auth";
import LinkedAccount from "./LinkedAccount";
import Alert from "./components/Alerts";

toast.configure({
  delay: 500,
});

const App = () => {
  //  const [user, setUser] = useState(localStorage.getItem("identity"));

  // useEffect(() => {
  //   if (localStorage.getItem("identity")) {
  //     setUser(localStorage.item)
  //   } else {
  //     setUser(null)
  //   }
  // }, [])


  return (
    <AuthState>
      <LinkedAccountState>
        <AlertState>
          <BrowserRouter>
            <ToastContainer autoClose={7000} transition={Slide} position="bottom-right" />
            <Navbar />
            <div>
              <Alert />
              <Switch>
                <Route exact path="/" render={() => <Home />} />
                <Route path="/auth" render={() => <Auth />} />
                <Route path="/linked-account" render={() => <LinkedAccount />} />
                {/* <Route component={Error}/> */}
              </Switch>
            </div>
          </BrowserRouter>
        </AlertState>
      </LinkedAccountState>
    </AuthState>
  )
}

export default App;