import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import React, { useEffect, useState } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';
import AuthState from "./context/AuthState";
import LinkedAccountState from "./context/LinkedAccountState";

//core components
import Home from "./Home/Home";
import Navbar from "./Navbar/Navbar";
import Auth from "./Auth";
import Form from "./LinkedAccount/Schema";

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
          <div>
            <Navbar />
            <Switch>
              <Route exact path="/" render={() => <Home />} />
              <Route path="/auth" render={() => <Auth />} />
              <Route path="/linked-account" render={() => <Form />} />
              {/* <Route component={Error}/> */}
            </Switch>
          </div>
        </BrowserRouter>
      </LinkedAccountState>
    </AuthState>
  )
}

export default App;