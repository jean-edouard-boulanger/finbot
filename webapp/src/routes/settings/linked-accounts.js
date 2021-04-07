import React, { useContext, useEffect, useState } from "react";
import { withRouter, Switch, Route, Redirect, Link } from "react-router-dom";

import { ServicesContext, AuthContext } from "contexts";

import { toast } from "react-toastify";
import { Row, Col, Table, Button, Modal } from "react-bootstrap";
import { LinkAccount } from "./linked-accounts-new";

export const UnlinkAccountDialog = ({
  show,
  linkedAccount,
  handleUnlink,
  handleClose,
}) => {
  const accountName = (linkedAccount ?? {}).account_name;
  return (
    <Modal show={show}>
      <Modal.Header closeButton>
        <Modal.Title>Unlink account</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>
          Are you sure you want to unlink account{" "}
          <strong>{`"${accountName}"`}</strong>?
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          Cancel
        </Button>
        <Button onClick={handleUnlink} variant="primary">
          Unlink
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export const AccountsPanel = () => {
  const { finbotClient } = useContext(ServicesContext);
  const { account } = useContext(AuthContext);
  const [accounts, setAccounts] = useState([]);
  const [dialog, setDialog] = useState({
    show: false,
    linkedAccount: null,
    handleUnlink: null,
    handleClose: null,
  });

  const hideDialog = () => {
    setDialog({
      show: false,
      linkedAccount: null,
      handleUnlink: null,
      handleClose: null,
    });
  };

  const refreshAccounts = async () => {
    const results = await finbotClient.getLinkedAccounts({
      account_id: account.id,
    });
    setAccounts(results);
  };

  useEffect(() => {
    refreshAccounts();
  }, [finbotClient]);

  const handleUnlinkAccount = async (linkedAccount) => {
    try {
      await finbotClient.deleteLinkedAccount({
        account_id: account.id,
        linked_account_id: linkedAccount.id,
      });
      toast.success(`Successfully unlinked '${linkedAccount.account_name}'`);
      await refreshAccounts();
    } catch (e) {
      toast.error(
        `Unable to unlink account '${linkedAccount.account_name}': ${e}`
      );
    }
  };

  return (
    <>
      <UnlinkAccountDialog {...dialog} />
      <Table hover size={"sm"}>
        <thead>
          <tr>
            <th>Account name</th>
            <th>Provider</th>
            <th>&nbsp;</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((linkedAccount) => {
            return (
              <tr key={`account-${linkedAccount.id}`}>
                <td>{linkedAccount.account_name}</td>
                <td>{linkedAccount.provider.description}</td>
                <td>
                  <Button
                    onClick={() => {
                      setDialog({
                        show: true,
                        linkedAccount,
                        handleUnlink: () => {
                          hideDialog();
                          handleUnlinkAccount(linkedAccount);
                        },
                        handleClose: () => {
                          hideDialog();
                        },
                      });
                    }}
                    size={"sm"}
                    variant={"dark"}
                  >
                    Unlink
                  </Button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </>
  );
};

export const LinkedAccountsSettings = withRouter((props) => {
  const route = props.location.pathname;
  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>
            <Link to={"/settings/linked"}>Linked accounts</Link>{" "}
            {route.startsWith("/settings/linked/new") && (
              <small>{"| New"}</small>
            )}
          </h3>
        </Col>
      </Row>
      {route === "/settings/linked" && (
        <Row className={"mb-4"}>
          <Col>
            <Link to={"/settings/linked/new"}>
              <Button size={"sm"} variant={"info"}>
                Link new account
              </Button>
            </Link>
          </Col>
        </Row>
      )}
      <Row>
        <Col>
          <Switch>
            <Route
              exact
              path="/settings/linked/new"
              render={() => <LinkAccount />}
            />
            <Route
              exact
              path="/settings/linked"
              render={() => <AccountsPanel />}
            />
            <Redirect to={"/settings/linked"} />
          </Switch>
        </Col>
      </Row>
    </>
  );
});
