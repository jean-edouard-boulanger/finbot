import React, { useContext } from "react";
import { withRouter, NavLink, RouteComponentProps } from "react-router-dom";

import AuthContext from "contexts/auth/auth-context";

import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";

const UserNavbar: React.FC<RouteComponentProps<Record<string, never>>> = (
  props
) => {
  return (
    <Navbar.Collapse id="responsive-navbar-nav">
      <Nav activeKey={props.location.pathname} className="ml-auto">
        <NavLink className="px-5 nav-link" to="/dashboard">
          Dashboard
        </NavLink>
        <NavLink className="px-5 nav-link" to="/settings">
          Settings
        </NavLink>
        <NavLink className="px-5 nav-link" to="/logout">
          Logout
        </NavLink>
      </Nav>
    </Navbar.Collapse>
  );
};

const GuestNavbar: React.FC<RouteComponentProps<Record<string, never>>> = (
  props
) => {
  return (
    <Navbar.Collapse id="responsive-navbar-nav">
      <Nav activeKey={props.location.pathname} className="ml-auto">
        <NavLink className="px-5 nav-link" to="/login">
          Sign in
        </NavLink>
        <NavLink className="px-5 nav-link" to="/signup">
          Sign up
        </NavLink>
      </Nav>
    </Navbar.Collapse>
  );
};

export const Navigation = withRouter((props) => {
  const { isAuthenticated } = useContext(AuthContext);
  return (
    <Navbar
      className="box-shadow"
      collapseOnSelect
      expand="md"
      bg="dark"
      variant="dark"
    >
      <NavLink
        className="px-5 navbar-brand"
        to={isAuthenticated ? `/dashboard` : "/loading"}
      >
        Finbot
      </NavLink>
      <Navbar.Toggle aria-controls="responsive-navbar-nav" />
      {isAuthenticated ? <UserNavbar {...props} /> : <GuestNavbar {...props} />}
    </Navbar>
  );
});

export default Navigation;
