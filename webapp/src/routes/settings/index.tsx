import React from "react";
import { useLocation, useNavigate, Outlet } from "react-router-dom";

import { ListGroup, Row, Col } from "react-bootstrap";

export const NavigationPanel: React.FC = () => {
  const { pathname } = useLocation();
  const push = useNavigate();
  return (
    <ListGroup>
      <ListGroup.Item>
        <strong>My settings</strong>
      </ListGroup.Item>
      <ListGroup.Item
        active={pathname.startsWith("/settings/profile")}
        onClick={() => {
          push("/settings/profile");
        }}
        action
      >
        Profile
      </ListGroup.Item>
      <ListGroup.Item
        active={pathname.startsWith("/settings/security")}
        onClick={() => {
          push("/settings/security");
        }}
        action
      >
        Account security
      </ListGroup.Item>
      <ListGroup.Item
        active={pathname.startsWith("/settings/linked")}
        onClick={() => {
          push("/settings/linked");
        }}
        action
      >
        Linked accounts
      </ListGroup.Item>
      <ListGroup.Item>
        <strong>Administration</strong>
      </ListGroup.Item>
      <ListGroup.Item
        active={pathname.startsWith("/settings/admin/providers")}
        onClick={() => {
          push("/settings/admin/providers");
        }}
        action
      >
        Providers
      </ListGroup.Item>
      <ListGroup.Item
        active={pathname.startsWith("/settings/admin/email_delivery")}
        onClick={() => {
          push("/settings/admin/email_delivery");
        }}
        action
      >
        Email delivery
      </ListGroup.Item>
    </ListGroup>
  );
};

export const Settings: React.FC<Record<string, never>> = () => {
  return (
    <Row>
      <Col md={3}>
        <NavigationPanel />
      </Col>
      <Col md={9}>
        <Outlet />
      </Col>
    </Row>
  );
};

export default Settings;
