import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"
import { ToastContainer, Slide, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import React, { useEffect, useState } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';

import AuthState from "./context/AuthState";
import LinkedAccountState from "./context/LinkedAccountState";

//core components
import Home from "./Home/Home";
import Navbar from "./Navbar/Navbar";
import Auth from "./Auth";
import LinkedAccount from "./LinkedAccount";

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
        <BrowserRouter>
          <ToastContainer autoClose={7000} transition={Slide} position="bottom-right" />
          <Navbar style={{ boxShadow: "0 3px 10px rgba(51, 50, 47, 0.5)" }} />
          <div style={{ padding: "90px 30px 74px 30px", background: "linear-gradient(to right, #ACB6E5, #74ebd5)" }}>
            <Switch>
              <Route exact path="/" render={() => <Home />} />
              <Route path="/auth" render={() => <Auth />} />
              <Route path="/linked-account" render={() => <LinkedAccount />} />
              {/* <Route component={Error}/> */}
            </Switch>
          </div>
        </BrowserRouter>
      </LinkedAccountState>
    </AuthState>
  )
}

export default App;