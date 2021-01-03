import React, {useEffect, useContext} from "react";
import {NavLink} from 'react-router-dom'

import NavBar from 'react-bootstrap/NavBar';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import AuthContext from "../../context/auth/auth-context";

const Navigation = props => {
  const authContext = useContext(AuthContext);
  const {token} = authContext;

  return (
    <NavBar className="box-shadow" collapseOnSelect expand="md" bg="dark" variant="dark">
      <NavLink className="px-5 navbar-brand" to="/">Finbot</NavLink>
      <Navbar.Toggle aria-controls="responsive-navbar-nav"/>

      {token ?
        <>
          <Navbar.Collapse id="responsive-navbar-nav">
            <Nav activeKey={props.location.pathname} className="ml-auto">
              <NavLink className="px-5 nav-link" to="/" exact>Home</NavLink>
              <NavLink className="px-5 nav-link" to="/auth/logout">Logout</NavLink>
              <NavLink className="px-5 nav-link" to="/linked-account/create" exact>Link account</NavLink>
            </Nav>
          </Navbar.Collapse>
        </>
        :
        <>
          <Navbar.Collapse id="responsive-navbar-nav">
            <Nav activeKey={props.location.pathname} className="ml-auto">
              <NavLink className="px-5 nav-link" to="/auth/sign-up">Sign Up</NavLink>
              <NavLink className="px-5 nav-link" to="/auth/log-in">Log In</NavLink>
            </Nav>
          </Navbar.Collapse>
        </>
      }
    </NavBar>
  )
}

export {Navigation};
