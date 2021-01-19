import React, { useContext, useEffect, useState } from "react";
import {withRouter, Switch, Route, Redirect, Link} from "react-router-dom";

import { ServicesContext, AuthContext } from "contexts";

import { toast } from "react-toastify";
import { Row, Col, Table, Button } from "react-bootstrap";
import { LinkAccount } from "./linked-accounts-new";


export const AccountsPanel = () => {
  const {finbotClient} = useContext(ServicesContext);
  const {account} = useContext(AuthContext);
  const [accounts, setAccounts] = useState([]);

  const refreshAccounts = async () => {
    const results = await finbotClient.getLinkedAccounts(
      {account_id: account.id});
    setAccounts(results);
  }

  useEffect(() => {
    refreshAccounts();
  }, [finbotClient]);

  const handleUnlinkAccount = async (linkedAccount) => {
    try {
      await finbotClient.deleteLinkedAccount({
        account_id: account.id,
        linked_account_id: linkedAccount.id
      });
      toast.success(`Successfully unlinked '${linkedAccount.account_name}'`);
      await refreshAccounts();
    }
    catch(e) {
      toast.error(`Unable to unlink account '${linkedAccount.account_name}': ${e}`);
    }
  }

  return (
    <div>
      <Table hover size={"sm"}>
        <thead>
          <tr>
            <th>Account name</th>
            <th>Provider</th>
            <th>&nbsp;</th>
          </tr>
        </thead>
        <tbody>
          {
            (accounts.map((linkedAccount) => {
              return (
                <tr key={`account-${linkedAccount.id}`}>
                  <td>{linkedAccount.account_name}</td>
                  <td>{linkedAccount.provider.description}</td>
                  <td>
                    <Button
                      onClick={() => handleUnlinkAccount(linkedAccount)}
                      size={"sm"}
                      variant={"dark"} >
                      Unlink
                    </Button>
                  </td>
                </tr>
              )
            }))
          }
        </tbody>
      </Table>
    </div>
  )
}

export const LinkedAccountsSettings = withRouter((props) => {
  const route = props.location.pathname;
  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>
            <Link to={"/settings/linked"}>Linked accounts</Link>{" "}
            {
              (route.startsWith("/settings/linked/new"))
                && <small>{"| New"}</small>
            }
          </h3>
        </Col>
      </Row>
      {
        (route === "/settings/linked") &&
          <Row className={"mb-4"}>
            <Col>
              <Link to={"/settings/linked/new"}>
                <Button size={"sm"} variant={"info"}>Link new account</Button>
              </Link>
            </Col>
          </Row>
      }
      <Row>
        <Col>
          <Switch>
            <Route exact path="/settings/linked/new" render={() => <LinkAccount />} />
            <Route exact path="/settings/linked" render={() => <AccountsPanel />} />
            <Redirect to={"/settings/linked"} />
          </Switch>
        </Col>
      </Row>
    </>
  )
});
