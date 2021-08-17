import React, { useContext, useEffect, useState } from "react";
import { withRouter, NavLink, RouteComponentProps } from "react-router-dom";

import AuthContext from "contexts/auth/auth-context";

import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import { Badge } from "react-bootstrap";
import { ServicesContext } from "contexts";
import { SystemReport } from "clients/finbot-client/types";

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
  const { finbotClient } = useContext(ServicesContext);
  const { isAuthenticated } = useContext(AuthContext);
  const [report, setReport] = useState<SystemReport | null>(null);

  useEffect(() => {
    const fetch = async () => {
      const report = await finbotClient!.getSystemReport();
      setReport(report);
    };
    fetch();
  }, [finbotClient]);

  const isDev = report?.runtime === "development";

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
        Finbot{` `}
        {isDev && (
          <Badge variant={"danger"}>DEV build v{report!.finbot_version}</Badge>
        )}
      </NavLink>
      <Navbar.Toggle aria-controls="responsive-navbar-nav" />
      {isAuthenticated ? <UserNavbar {...props} /> : <GuestNavbar {...props} />}
    </Navbar>
  );
});

export default Navigation;
