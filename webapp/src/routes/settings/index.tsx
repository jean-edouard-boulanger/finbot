import React from "react";
import { withRouter, Switch, Route, Redirect } from "react-router-dom";

import { ProfileSettings } from "./profile";
import { LinkedAccountsSettings } from "./linked-accounts";
import { ProvidersSettings } from "./providers";
import { PlaidIntegrationSettings } from "./plaid-integration";
import { TwilioIntegrationSettings } from "./twilio-integration";
import { AccountSecuritySettings } from "./account-security";
import { EmailDeliverySettingsPanel } from "./email-delivery";

import { ListGroup, Row, Col } from "react-bootstrap";

export const NavigationPanel = withRouter((props) => {
  const route = props.location.pathname;
  return (
    <ListGroup>
      <ListGroup.Item>
        <strong>My settings</strong>
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/profile")}
        onClick={() => {
          props.history.push("/settings/profile");
        }}
        action
      >
        Profile
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/security")}
        onClick={() => {
          props.history.push("/settings/security");
        }}
        action
      >
        Account security
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/linked")}
        onClick={() => {
          props.history.push("/settings/linked");
        }}
        action
      >
        Linked accounts
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/twilio")}
        onClick={() => {
          props.history.push("/settings/twilio");
        }}
        action
      >
        Twilio integration
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/plaid")}
        onClick={() => {
          props.history.push("/settings/plaid");
        }}
        action
      >
        Plaid integration
      </ListGroup.Item>
      <ListGroup.Item>
        <strong>Administration</strong>
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/admin/providers")}
        onClick={() => {
          props.history.push("/settings/admin/providers");
        }}
        action
      >
        Providers
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/admin/email_delivery")}
        onClick={() => {
          props.history.push("/settings/admin/email_delivery");
        }}
        action
      >
        Email delivery
      </ListGroup.Item>
    </ListGroup>
  );
});

export const Settings: React.FC<Record<string, never>> = () => {
  return (
    <Row>
      <Col md={3}>
        <NavigationPanel />
      </Col>
      <Col md={9}>
        <Switch>
          <Route
            exact
            path="/settings/profile"
            render={() => <ProfileSettings />}
          />
          <Route
            exact
            path="/settings/security"
            render={() => <AccountSecuritySettings />}
          />
          <Route
            path="/settings/linked"
            render={() => <LinkedAccountsSettings />}
          />
          <Route
            path="/settings/twilio"
            render={() => <TwilioIntegrationSettings />}
          />
          <Route
            path="/settings/plaid"
            render={() => <PlaidIntegrationSettings />}
          />
          <Route
            path="/settings/admin/providers"
            render={() => <ProvidersSettings />}
          />
          <Route
            path="/settings/admin/email_delivery"
            render={() => <EmailDeliverySettingsPanel />}
          />

          <Redirect to={"/settings/profile"} />
        </Switch>
      </Col>
    </Row>
  );
};

export default Settings;
