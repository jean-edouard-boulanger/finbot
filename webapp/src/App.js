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
    _setUser();
  }, [])

  function _resetUser() {
    setUser({ user: null })
  }

  function _setUser(init) {
    const token = localStorage.getItem('identity')
    if (token) {
      const decoded = jwtDecode(token)
      delete decoded.iat
      if (init) return decoded
      setUser({ user: decoded })
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