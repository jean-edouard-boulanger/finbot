import React, { useContext, useEffect, useState } from "react";
import {
  useLocation,
  Outlet,
  Link,
  matchPath,
  useParams,
  useNavigate,
} from "react-router-dom";
import {
  CheckCircle,
  AlertCircle,
  Ghost,
  HelpCircle,
  MoreHorizontal,
} from "lucide-react";

import { AuthContext } from "contexts";
import {
  useApi,
  LinkedAccountsApi,
  LinkedAccount,
  ErrorMetadata,
} from "clients";
import { StackedBarLoader } from "components";
import { asDateTime } from "utils/time";
import { LinkAccount } from "./link-account";

import { Button } from "components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "components/ui/dialog";
import { Alert, AlertTitle, AlertDescription } from "components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Separator } from "components/ui/separator";
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
  const accountName = linkedAccount?.accountName;
  return (
    <Dialog open={show} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Unlink account</DialogTitle>
          <DialogDescription>
            Are you sure you want to unlink (delete) account{" "}
            {`"${accountName}"`}?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose} size="sm">
            Cancel
          </Button>
          <Button onClick={handleUnlink} variant="destructive" size="sm">
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const UpdateLinkedAccountPanel: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null,
  );
  const linkedAccountsApi = useApi(LinkedAccountsApi);
  useEffect(() => {
    const fetch = async () => {
      const result = await linkedAccountsApi.getLinkedAccount({
        userAccountId: userAccountId!,
        linkedAccountId: parseInt(linkedAccountId!),
      });
      setLinkedAccount(result.linkedAccount);
    };
    fetch();
  }, [linkedAccountsApi, userAccountId, linkedAccountId]);
  return <LinkAccount linkedAccount={linkedAccount} />;
};

type LinkedAccountStatus = "stable" | "unstable" | "frozen" | "unknown";

const getLinkedAccountStatus = (
  linkedAccount: LinkedAccount,
): LinkedAccountStatus => {
  if (linkedAccount.frozen) {
    return "frozen";
  }
  return (linkedAccount.status ?? { status: "unknown" }).status;
};

const getLinkedAccountLastError = (
  linkedAccount: LinkedAccount,
): ErrorMetadata | null => {
  const errors = linkedAccount?.status?.errors ?? [];
  if (errors.length === 0) {
    return null;
  }
  return errors[errors.length - 1].error;
};

const activeAccountsFirst = (
  account1: LinkedAccount,
  account2: LinkedAccount,
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
        <CheckCircle className="inline h-4 w-4 text-green-500" />
      )}
      {status === "unstable" && (
        <AlertCircle className="inline h-4 w-4 text-red-500" />
      )}
      {status === "frozen" && (
        <Ghost className="inline h-4 w-4 text-muted-foreground" />
      )}
      {status === "unknown" && (
        <HelpCircle className="inline h-4 w-4 text-muted-foreground" />
      )}
    </>
  );
};

export const LinkedAccountStatusPanel: React.FC = () => {
  const linkedAccountsApi = useApi(LinkedAccountsApi);
  const { userAccountId } = useContext(AuthContext);
  const { linkedAccountId } = useParams<Record<string, string | undefined>>();
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null,
  );
  const [showInternalDetails] = useState<boolean>(true);
  useEffect(() => {
    const fetch = async () => {
      try {
        const result = await linkedAccountsApi.getLinkedAccount({
          userAccountId: userAccountId!,
          linkedAccountId: parseInt(linkedAccountId!),
        });
        setLinkedAccount(result.linkedAccount);
      } catch (e) {
        toast.error(`${e}`);
      }
    };
    fetch();
  }, [linkedAccountsApi, userAccountId, linkedAccountId]);

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
      <div className="mb-4">
        <h4 className="text-lg font-semibold">
          {linkedAccount?.accountName ?? ""}{" "}
          <LinkedAccountStatusIcon status={status} />
        </h4>
      </div>
      {status === "unstable" && lastError && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>There is an issue with this linked account</AlertTitle>
          <Separator className="my-2" />
          <AlertDescription>
            <strong>Details</strong>: {lastError!.userMessage} (code:{" "}
            {lastError!.errorCode})
          </AlertDescription>
          {showInternalDetails && (
            <>
              <Separator className="my-2" />
              <AlertDescription>
                <strong>Internal details</strong>: {lastError!.debugMessage}
              </AlertDescription>
            </>
          )}
        </Alert>
      )}
      {status === null && (
        <Alert className="mb-4">
          <AlertTitle>
            We do not have any information about this linked account
          </AlertTitle>
          <Separator className="my-2" />
          <AlertDescription>
            This usually happens for accounts that have just been linked. The
            account status will be available as soon as the account valuation
            is calculated.
          </AlertDescription>
        </Alert>
      )}
      {status === "frozen" && (
        <Alert className="mb-4">
          <AlertTitle>This account is frozen</AlertTitle>
          <Separator className="my-2" />
          <AlertDescription>
            Frozen accounts can no longer be updated and are no longer
            valuated. Their historical valuation is still used in the
            calculation of the performance of your portfolio.
          </AlertDescription>
        </Alert>
      )}
      <div className="mb-4">
        <h5 className="font-medium">Previous snapshots</h5>
      </div>
    </>
  );
};

export interface AccountsPanelProps {}

export const AccountsPanel: React.FC<AccountsPanelProps> = () => {
  const push = useNavigate();
  const { userAccountId } = useContext(AuthContext);
  const [accounts, setAccounts] = useState<Array<LinkedAccount>>([]);
  const [dialog, setDialog] = useState<UnlinkAccountDialogProps>({
    show: false,
    linkedAccount: null,
    handleUnlink: () => {},
    handleClose: () => {},
  });
  const linkedAccountsApi = useApi(LinkedAccountsApi);

  const hideDialog = () => {
    setDialog({
      show: false,
      linkedAccount: null,
      handleUnlink: () => {},
      handleClose: () => {},
    });
  };

  const refreshAccounts = async () => {
    const result = await linkedAccountsApi.getUserAccountLinkedAccounts({
      userAccountId: userAccountId!,
    });
    setAccounts(result.linkedAccounts);
  };

  useEffect(() => {
    refreshAccounts();
  }, [linkedAccountsApi]);

  const handleUnlinkAccount = async (linkedAccount: LinkedAccount) => {
    try {
      await linkedAccountsApi.deleteLinkedAccount({
        userAccountId: userAccountId!,
        linkedAccountId: linkedAccount.id,
      });
      toast.success(`Successfully unlinked '${linkedAccount.accountName}'`);
      await refreshAccounts();
    } catch (e) {
      toast.error(
        `Unable to unlink account '${linkedAccount.accountName}': ${e}`,
      );
    }
  };

  return (
    <>
      <UnlinkAccountDialog {...dialog} />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Account name</TableHead>
            <TableHead>Last snapshot</TableHead>
            <TableHead>Provider</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {accounts.sort(activeAccountsFirst).map((linkedAccount) => {
            const linkedAccountStatus = getLinkedAccountStatus(linkedAccount);
            const lastSnapshotTime = asDateTime(
              linkedAccount!.status?.lastSnapshotTime,
            );
            return (
              <TableRow key={`account-${linkedAccount.id}`}>
                <TableCell>
                  <Link
                    to={`/settings/linked/${linkedAccount.id}/status`}
                    className="text-primary hover:underline"
                  >
                    {linkedAccount.accountName}
                  </Link>
                </TableCell>
                <TableCell>
                  <LinkedAccountStatusIcon status={linkedAccountStatus} />
                  {"  "}
                  {lastSnapshotTime === null
                    ? ""
                    : lastSnapshotTime.toLocaleString(DateTime.DATETIME_MED)}
                </TableCell>
                <TableCell>{linkedAccount!.provider!.description}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      disabled={linkedAccount.frozen}
                      onClick={() => {
                        push(`/settings/linked/${linkedAccount.id}/edit`);
                      }}
                    >
                      Edit
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={linkedAccount.frozen}
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem
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
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => {
                            push(
                              `/settings/linked/${linkedAccount.id}/status`,
                            );
                          }}
                        >
                          Status
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </>
  );
};

export const LinkedAccountsSettings: React.FC = () => {
  const { pathname } = useLocation();
  return (
    <>
      <div className="mb-4">
        <h3 className="text-2xl font-semibold">
          <Link to={"/settings/linked"} className="hover:underline">
            Linked accounts
          </Link>{" "}
          {matchPath("/settings/linked/new", pathname) ? (
            <span className="text-lg text-muted-foreground">| New</span>
          ) : matchPath("/settings/linked/:id/edit", pathname) ? (
            <span className="text-lg text-muted-foreground">| Edit</span>
          ) : matchPath("/settings/linked/:id/status", pathname) ? (
            <span className="text-lg text-muted-foreground">| Status</span>
          ) : (
            <></>
          )}
        </h3>
        <Separator className="mt-2" />
      </div>
      {pathname === "/settings/linked" && (
        <div className="mb-4">
          <Link to={"/settings/linked/new"}>
            <Button size="sm">Link new account</Button>
          </Link>
        </div>
      )}
      <div>
        <Outlet />
      </div>
    </>
  );
};
