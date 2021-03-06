import React from "react";
import {withRouter, Switch, Route, Redirect} from "react-router-dom";

import { ProfileSettings } from "./profile";
import { LinkedAccountsSettings } from "./linked-accounts";
import { ProvidersSettings } from "./providers";
import { PlaidIntegrationSettings } from "./plaid-integration";

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
        onClick={() => {props.history.push("/settings/profile")}}
        action >
        Profile
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/linked")}
        onClick={() => {props.history.push("/settings/linked")}}
        action >
        Linked accounts
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/plaid")}
        onClick={() => {props.history.push("/settings/plaid")}}
        action >
        Plaid integration
      </ListGroup.Item>
      <ListGroup.Item>
        <strong>Administration</strong>
      </ListGroup.Item>
      <ListGroup.Item
        active={route.startsWith("/settings/providers")}
        onClick={() => {props.history.push("/settings/providers")}}
        action >
        Providers
      </ListGroup.Item>
    </ListGroup>
  )
});

export const Settings = () => {
  return (
    <Row>
      <Col md={3}>
        <NavigationPanel />
      </Col>
      <Col md={9}>
        <Switch>
          <Route exact path="/settings/profile" render={() => <ProfileSettings />} />
          <Route path="/settings/linked" render={() => <LinkedAccountsSettings />} />
          <Route path="/settings/plaid" render={() => <PlaidIntegrationSettings />} />
          <Route path="/settings/providers" render={() => <ProvidersSettings />} />

          <Redirect to={"/settings/profile"} />
        </Switch>
      </Col>
    </Row>
  )
};

export default Settings;
