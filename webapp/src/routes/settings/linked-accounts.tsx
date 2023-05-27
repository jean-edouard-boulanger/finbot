import React, { useContext, useEffect, useState } from "react";
import {
  useLocation,
  Outlet,
  Link,
  matchPath,
  useParams,
  useNavigate,
} from "react-router-dom";

import { ServicesContext, AuthContext } from "contexts";
import { StackedBarLoader } from "components";
import {
  FinbotErrorMetadata,
  LinkedAccount,
} from "clients/finbot-client/types";
import { asDateTime } from "utils/time";
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
import {
  FaExclamationCircle,
  FaCheckCircle,
  FaQuestionCircle,
  FaGhost,
} from "react-icons/fa";
import { toast } from "react-toastify";
import { DateTime } from "luxon";

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
          Are you sure you want to unlink (delete) account {`"${accountName}"`}?
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="dark" onClick={handleClose} size={"sm"}>
          Cancel
        </Button>
        <Button onClick={handleUnlink} variant="danger" size={"sm"}>
          Confirm
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export const UpdateLinkedAccountPanel: React.FC = () => {
  const { finbotClient } = useContext(ServicesContext);
  const { userAccountId } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null
  );
  useEffect(() => {
    const fetch = async () => {
      const linkedAccount = await finbotClient!.getLinkedAccount({
        account_id: userAccountId!,
        linked_account_id: parseInt(linkedAccountId!),
      });
      setLinkedAccount(linkedAccount);
    };
    fetch();
  }, [finbotClient, userAccountId, linkedAccountId]);
  return <LinkAccount linkedAccount={linkedAccount} />;
};

type LinkedAccountStatus = "stable" | "unstable" | "frozen" | "unknown";

const getLinkedAccountStatus = (
  linkedAccount: LinkedAccount
): LinkedAccountStatus => {
  if (linkedAccount.frozen) {
    return "frozen";
  }
  return (linkedAccount.status ?? { status: "unknown" }).status;
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

const activeAccountsFirst = (
  account1: LinkedAccount,
  account2: LinkedAccount
): number => {
  return Number(account1.frozen) - Number(account2.frozen);
};

interface LinkedAccountStatusIconProps {
  status: LinkedAccountStatus;
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
      {status === "frozen" && <FaGhost />}
      {status === "unknown" && <FaQuestionCircle />}
    </>
  );
};

export const LinkedAccountStatusPanel: React.FC = () => {
  const { finbotClient } = useContext(ServicesContext);
  const { userAccountId } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null
  );
  const [showInternalDetails] = useState<boolean>(true);
  useEffect(() => {
    const fetch = async () => {
      try {
        const linkedAccount = await finbotClient!.getLinkedAccount({
          account_id: userAccountId!,
          linked_account_id: parseInt(linkedAccountId!),
        });
        setLinkedAccount(linkedAccount);
      } catch (e) {
        toast.error(`${e}`);
      }
    };
    fetch();
  }, [finbotClient, userAccountId, linkedAccountId]);

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
      {status === "unstable" && lastError && (
        <Row className={"mb-4"}>
          <Col>
            <Alert variant={"danger"}>
              <Alert.Heading>
                There is an issue with this linked account
              </Alert.Heading>
              <hr />
              <p>
                <strong>Details</strong>: {lastError!.user_message} (code:{" "}
                {lastError!.error_code})
              </p>
              {showInternalDetails && (
                <>
                  <hr />
                  <p>
                    <strong>Internal details</strong>:{" "}
                    {lastError!.debug_message}
                  </p>
                </>
              )}
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
              <hr />
              <p>
                This usually happens for accounts that have just been linked.
                The account status will be available as soon as the account
                valuation is calculated.
              </p>
            </Alert>
          </Col>
        </Row>
      )}
      {status === "frozen" && (
        <Row className={"mb-4"}>
          <Col>
            <Alert variant={"info"}>
              <Alert.Heading>This account is frozen</Alert.Heading>
              <hr />
              <p>
                Frozen accounts can no longer be updated and are no longer
                valuated. Their historical valuation is still used in the
                calculation of the performance of your portfolio.
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
};

export interface AccountsPanelProps {}

export const AccountsPanel: React.FC<AccountsPanelProps> = () => {
  const push = useNavigate();
  const { finbotClient } = useContext(ServicesContext);
  const { userAccountId } = useContext(AuthContext);
  const [accounts, setAccounts] = useState<Array<LinkedAccount>>([]);
  const [dialog, setDialog] = useState<UnlinkAccountDialogProps>({
    show: false,
    linkedAccount: null,
    handleUnlink: () => {},
    handleClose: () => {},
  });

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
      account_id: userAccountId!,
    });
    setAccounts(results);
  };

  useEffect(() => {
    refreshAccounts();
  }, [finbotClient]);

  const handleUnlinkAccount = async (linkedAccount: LinkedAccount) => {
    try {
      await finbotClient!.deleteLinkedAccount({
        account_id: userAccountId!,
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
            <th>Last snapshot</th>
            <th>Provider</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {accounts.sort(activeAccountsFirst).map((linkedAccount) => {
            const linkedAccountStatus = getLinkedAccountStatus(linkedAccount);
            const lastSnapshotTime = asDateTime(
              linkedAccount!.status?.last_snapshot_time
            );
            return (
              <tr key={`account-${linkedAccount.id}`}>
                <td>
                  <Link to={`/settings/linked/${linkedAccount.id}/status`}>
                    {linkedAccount.account_name}
                  </Link>
                </td>
                <td>
                  <LinkedAccountStatusIcon status={linkedAccountStatus} />
                  {"  "}
                  {lastSnapshotTime === null
                    ? ""
                    : lastSnapshotTime.toLocaleString(DateTime.DATETIME_MED)}
                </td>
                <td>{linkedAccount!.provider!.description}</td>
                <td>
                  <SplitButton
                    id={`action-${linkedAccount.id}`}
                    disabled={linkedAccount.frozen}
                    variant={"dark"}
                    title={"Edit"}
                    size={"sm"}
                    toggleLabel={""}
                    onClick={() => {
                      push(`/settings/linked/${linkedAccount.id}/edit`);
                    }}
                  >
                    <Dropdown.Item
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
                    </Dropdown.Item>
                    <Dropdown.Divider />
                    <Dropdown.Item
                      onClick={() => {
                        push(`/settings/linked/${linkedAccount.id}/status`);
                      }}
                    >
                      Status
                    </Dropdown.Item>
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

export const LinkedAccountsSettings: React.FC = () => {
  const { pathname } = useLocation();
  return (
    <>
      <Row className={"mb-4"}>
        <Col>
          <h3>
            <Link to={"/settings/linked"}>Linked accounts</Link>{" "}
            {matchPath("/settings/linked/new", pathname) ? (
              <small>{"| New"}</small>
            ) : matchPath("/settings/linked/:id/edit", pathname) ? (
              <small>{"| Edit"}</small>
            ) : matchPath("/settings/linked/:id/status", pathname) ? (
              <small>{"| Status"}</small>
            ) : (
              <></>
            )}
          </h3>
          <hr />
        </Col>
      </Row>
      {pathname === "/settings/linked" && (
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
          <Outlet />
        </Col>
      </Row>
    </>
  );
};
