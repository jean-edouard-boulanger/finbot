import React, { useContext, useEffect, useState } from "react";
import {
  withRouter,
  Switch,
  Route,
  Redirect,
  Link,
  matchPath,
  useParams,
  useHistory,
} from "react-router-dom";

import { ServicesContext, AuthContext } from "contexts";
import { StackedBarLoader } from "components";
import {
  FinbotErrorMetadata,
  LinkedAccount,
} from "clients/finbot-client/types";
import { LinkAccount } from "./link-account";

import {
  Alert,
  Row,
  Col,
  Table,
  Button,
  Modal,
  SplitButton,
  Dropdown,
} from "react-bootstrap";
import DropdownItem from "react-bootstrap/DropdownItem";
import {
  FaExclamationCircle,
  FaCheckCircle,
  FaQuestionCircle,
} from "react-icons/fa";
import { toast } from "react-toastify";

interface UnlinkAccountDialogProps {
  show: boolean;
  linkedAccount: LinkedAccount | null;
  handleUnlink(): void;
  handleClose(): void;
}

export const UnlinkAccountDialog: React.FC<UnlinkAccountDialogProps> = ({
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
        <Button variant="dark" onClick={handleClose} size={"sm"}>
          Cancel
        </Button>
        <Button onClick={handleUnlink} variant="danger" size={"sm"}>
          Unlink
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

const UpdateLinkedAccountPanel = withRouter(() => {
  const { finbotClient } = useContext(ServicesContext);
  const { account } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null
  );
  useEffect(() => {
    const fetch = async () => {
      const linkedAccount = await finbotClient!.getLinkedAccount({
        account_id: account!.id,
        linked_account_id: parseInt(linkedAccountId!),
      });
      setLinkedAccount(linkedAccount);
    };
    fetch();
  }, [finbotClient, account, linkedAccountId]);
  return <LinkAccount linkedAccount={linkedAccount} />;
});

const getLinkedAccountStatus = (
  linkedAccount: LinkedAccount
): "stable" | "unstable" | null => {
  return (linkedAccount.status ?? { status: null }).status;
};

const getLinkedAccountLastError = (
  linkedAccount: LinkedAccount
): FinbotErrorMetadata | null => {
  const errors = (linkedAccount.status ?? { errors: [] }).errors;
  if (errors === null || errors.length === 0) {
    return null;
  }
  return errors[errors.length - 1].error;
};

interface LinkedAccountStatusIconProps {
  status: "stable" | "unstable" | null;
}

const LinkedAccountStatusIcon: React.FC<LinkedAccountStatusIconProps> = ({
  status,
}) => {
  return (
    <>
      {status === "stable" && (
        <span className={"text-success"}>
          <FaCheckCircle />
        </span>
      )}
      {status === "unstable" && (
        <span className={"text-danger"}>
          <FaExclamationCircle />
        </span>
      )}
      {status === null && <FaQuestionCircle />}
    </>
  );
};

const LinkedAccountStatusPanel = withRouter(() => {
  const { finbotClient } = useContext(ServicesContext);
  const { account } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null
  );
  useEffect(() => {
    const fetch = async () => {
      try {
        const linkedAccount = await finbotClient!.getLinkedAccount({
          account_id: account!.id,
          linked_account_id: parseInt(linkedAccountId!),
        });
        setLinkedAccount(linkedAccount);
      } catch (e) {
        toast.error(e);
      }
    };
    fetch();
  }, [finbotClient, account, linkedAccountId]);

  if (linkedAccount === null) {
    return (
      <StackedBarLoader
        count={4}
        color={"#FBFBFB"}
        spacing={"0.8em"}
        height={"1em"}
        width={"100%"}
      />
    );
  }

  const status = getLinkedAccountStatus(linkedAccount!);
  const lastError = getLinkedAccountLastError(linkedAccount!);

  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h4>
            {(linkedAccount ?? { account_name: "" }).account_name}{" "}
            <LinkedAccountStatusIcon status={status} />
          </h4>
        </Col>
      </Row>
      {status === "unstable" && (
        <Row className={"mb-4"}>
          <Col>
            <Alert variant={"danger"}>
              <Alert.Heading>
                There is an issue with this linked account
              </Alert.Heading>
              <p>
                Details: {lastError!.user_message} (code:{" "}
                {lastError!.error_code})
              </p>
              <hr />
              <span className={"font-italic"}>
                Reference: {lastError!.distributed_trace_key!.guid}/
                {lastError!.distributed_trace_key!.path}
              </span>
            </Alert>
          </Col>
        </Row>
      )}
      {status === null && (
        <Row className={"mb-4"}>
          <Col>
            <Alert variant={"info"}>
              <Alert.Heading>
                We do not have any information about this linked account
              </Alert.Heading>
              <p>
                This usually happens for accounts that have just been linked.
                The account status will be available as soon as the account
                valuation is calculated.
              </p>
            </Alert>
          </Col>
        </Row>
      )}
      <Row className={"mb-4"}>
        <Col>
          <h5>Previous snapshots</h5>
        </Col>
      </Row>
    </>
  );
});

export interface AccountsPanelProps {}

export const AccountsPanel: React.FC<AccountsPanelProps> = () => {
  const { push } = useHistory();
  const { finbotClient } = useContext(ServicesContext);
  const { account } = useContext(AuthContext);
  const [accounts, setAccounts] = useState<Array<LinkedAccount>>([]);
  const [dialog, setDialog] = useState<UnlinkAccountDialogProps>({
    show: false,
    linkedAccount: null,
    handleUnlink: () => {},
    handleClose: () => {},
  });
  const userAccountId = account!.id;

  const hideDialog = () => {
    setDialog({
      show: false,
      linkedAccount: null,
      handleUnlink: () => {},
      handleClose: () => {},
    });
  };

  const refreshAccounts = async () => {
    const results = await finbotClient!.getLinkedAccounts({
      account_id: userAccountId,
    });
    setAccounts(results);
  };

  useEffect(() => {
    refreshAccounts();
  }, [finbotClient]);

  const handleUnlinkAccount = async (linkedAccount: LinkedAccount) => {
    try {
      await finbotClient!.deleteLinkedAccount({
        account_id: userAccountId,
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
            <th style={{ width: "6em" }}>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((linkedAccount) => {
            const status = getLinkedAccountStatus(linkedAccount);
            return (
              <tr key={`account-${linkedAccount.id}`}>
                <td>
                  <Link to={`/settings/linked/${linkedAccount.id}/edit`}>
                    {linkedAccount.account_name}
                  </Link>
                </td>
                <td>{linkedAccount!.provider!.description}</td>
                <td style={{ textAlign: "center" }}>
                  <Link to={`/settings/linked/${linkedAccount.id}/status`}>
                    <LinkedAccountStatusIcon status={status} />
                  </Link>
                </td>
                <td>
                  <SplitButton
                    id={`action-${linkedAccount.id}`}
                    variant={"dark"}
                    title={"Edit"}
                    size={"sm"}
                    onClick={() => {
                      push(`/settings/linked/${linkedAccount.id}/edit`);
                    }}
                  >
                    <DropdownItem
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
                    >
                      Unlink
                    </DropdownItem>
                    <Dropdown.Divider />
                    <DropdownItem
                      onClick={() => {
                        push(`/settings/linked/${linkedAccount.id}/status`);
                      }}
                    >
                      Status
                    </DropdownItem>
                  </SplitButton>
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
            {matchPath(route, {
              path: "/settings/linked/new",
              exact: true,
              strict: true,
            }) ? (
              <small>{"| New"}</small>
            ) : matchPath(route, {
                path: "/settings/linked/:id/edit",
                exact: true,
                strict: true,
              }) ? (
              <small>{"| Edit"}</small>
            ) : matchPath(route, {
                path: "/settings/linked/:id/status",
                exact: true,
                strict: true,
              }) ? (
              <small>{"| Status"}</small>
            ) : (
              <></>
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
              path="/settings/linked/:linkedAccountId/edit"
              render={() => <UpdateLinkedAccountPanel />}
            />
            <Route
              exact
              path="/settings/linked/:linkedAccountId/status"
              render={() => <LinkedAccountStatusPanel />}
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
