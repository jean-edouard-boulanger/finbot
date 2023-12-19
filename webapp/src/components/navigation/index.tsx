import React, { useContext, useEffect, useState } from "react";
import { useLocation, NavLink } from "react-router-dom";

import AuthContext from "contexts/auth/auth-context";
import { useInterval } from "utils/use-interval";
import { useApi, SystemReport, SystemApi } from "clients";

import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import { Badge } from "react-bootstrap";

const SystemStatusBadge: React.FC<Record<string, never>> = () => {
  const systemApi = useApi(SystemApi);
  const [backendReachable, setBackendReachable] = useState(true);
  const [report, setReport] = useState<SystemReport | null>(null);

  const updateReport = async () => {
    try {
      setReport((await systemApi.getSystemReport()).systemReport);
      setBackendReachable(true);
    } catch (e) {
      setBackendReachable(false);
      setReport(null);
    }
  };

  useEffect(() => {
    updateReport();
  }, [systemApi]);

  useInterval(async () => {
    updateReport();
  }, 10000);

  return (
    <>
      {backendReachable && report?.runtime === "development" && (
        <Badge bg={"danger"}>DEV build v{report!.finbotVersion}</Badge>
      )}
      {!backendReachable && <Badge bg={"danger"}>BACKEND UNREACHABLE</Badge>}
    </>
  );
};

const UserNavbar: React.FC = () => {
  const { pathname } = useLocation();
  return (
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
  );
};

const GuestNavbar: React.FC = () => {
  const { pathname } = useLocation();
  return (
    <Nav activeKey={pathname} className="ml-auto">
      <NavLink className="px-5 nav-link" to="/login">
        Sign in
      </NavLink>
      <NavLink className="px-5 nav-link" to="/signup">
        Sign up
      </NavLink>
    </Nav>
  );
};

export const Navigation: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const isAuthenticated = userAccountId !== null;

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
      <Navbar.Collapse id="responsive-navbar-nav">
        <Nav className="me-auto" />
        {isAuthenticated ? <UserNavbar /> : <GuestNavbar />}
      </Navbar.Collapse>
    </Navbar>
  );
};

export default Navigation;
