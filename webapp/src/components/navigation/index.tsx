import React, { useContext, useState } from "react";
import { useLocation, NavLink } from "react-router-dom";

import AuthContext from "contexts/auth/auth-context";
import { useInterval } from "utils/use-interval";

import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import { Badge } from "react-bootstrap";
import { ServicesContext } from "contexts";
import { SystemReport } from "clients/finbot-client/types";

const SystemStatusBadge: React.FC<Record<string, never>> = () => {
  const { finbotClient } = useContext(ServicesContext);
  const [backendReachable, setBackendReachable] = useState(true);
  const [report, setReport] = useState<SystemReport | null>(null);

  useInterval(async () => {
    try {
      setReport(await finbotClient!.getSystemReport());
      setBackendReachable(true);
    } catch (e) {
      setBackendReachable(false);
      setReport(null);
    }
  }, 10000);

  return (
    <>
      {backendReachable && report?.runtime === "development" && (
        <Badge variant={"danger"}>DEV build v{report!.finbot_version}</Badge>
      )}
      {!backendReachable && (
        <Badge variant={"danger"}>BACKEND UNREACHABLE</Badge>
      )}
    </>
  );
};

const UserNavbar: React.FC = () => {
  const { pathname } = useLocation();
  return (
    <Navbar.Collapse id="responsive-navbar-nav">
      <Nav activeKey={pathname} className="ml-auto">
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

const GuestNavbar: React.FC = () => {
  const { pathname } = useLocation();
  return (
    <Navbar.Collapse id="responsive-navbar-nav">
      <Nav activeKey={pathname} className="ml-auto">
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

export const Navigation: React.FC = () => {
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
        to={isAuthenticated ? `/dashboard` : "/login"}
      >
        Finbot{` `}
        <SystemStatusBadge />
      </NavLink>
      <Navbar.Toggle aria-controls="responsive-navbar-nav" />
      {isAuthenticated ? <UserNavbar /> : <GuestNavbar />}
    </Navbar>
  );
};

export default Navigation;
