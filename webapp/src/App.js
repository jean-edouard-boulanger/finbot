import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import React, { useState, useEffect } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';
import jwtDecode from 'jwt-decode';

//core components
import Home from "./Home/Home";
import Navbar from "./Home/Navbar";
import Auth from "./Auth/index"

const App = () => {
  const [user, setUser] = useState(_setUser(true))

  useEffect(() => {
    console.log("app comp did mount")
    _setUser();
  }, [])

  function _resetUser() {
    console.log("in reset user")
    setUser({ user: null })
  }

  //hardcode token for now as long as no token from serverside available
  function _setUser(init) {
    console.log("in _setUsr")
    const token = localStorage.getItem('identity')
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
      return null
    }
  }

  return (
    <BrowserRouter>
      <div>
        <Navbar user={user} />
        <Switch>
          <Route exact path="/" render={() => <Home user={user} />} />
          <Route path="/auth" render={() => <Auth setUser={_setUser} resetUser={_resetUser} />} />
          {/* <Route component={Error}/> */}
        </Switch>
      </div>
    </BrowserRouter>
  )
}

export default App;