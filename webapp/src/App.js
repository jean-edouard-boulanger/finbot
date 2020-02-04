import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"

import React, { useState, useEffect } from 'react';
import { Route, Switch, Redirect } from "react-router-dom";
import 'datejs'
import jwtDecode from 'jwt-decode'

//core components
import Home from "./Home/Home";
import Navbar from "./Home/Navbar";

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
    console.log({ token })
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
    <>
      <Navbar />
      <Switch>
        <Route exact path="/" component={Home} />
        {/* <Route component={Error}/> */}
        {/* <Redirect from="/" to="/signin" /> */}
      </Switch>
    </>
  )
}

export default App;