import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"
import { ToastContainer, Slide, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import React, { useEffect, useState } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';

import AuthState from "./context/AuthState";
import LinkedAccountState from "./context/linked-account-state";

//core components
import Home from "./routes/main-dashboard";
import Navbar from "./components/navigation";
import Auth from "./routes/auth";
import LinkedAccount from "./routes/link-external-account";
// <Route path="/external-accounts/link" render={() => <LinkExternalAccount providers={providersList} />} /> 
// import LinkedAccountState from "context/linked-account-state";
// import Navigation from "components/navigation";

// import Auth from "routes/auth";
// import MainDashboard from "routes/main-dashboard";
// import LinkExternalAccount from "routes/link-external-account"

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
          <div style={{ padding: "90px 30px 74px 30px" }}>
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
