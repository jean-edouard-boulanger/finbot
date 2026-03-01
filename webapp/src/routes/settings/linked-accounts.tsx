import React, { useContext, useEffect, useState } from "react";
import {
  CheckCircle,
  AlertCircle,
  Ghost,
  HelpCircle,
  MoreHorizontal,
  Pencil,
  X,
  Check,
  Link2,
} from "lucide-react";

import { AuthContext } from "contexts";
import {
  useApi,
  LinkedAccountsApi,
  LinkedAccount,
  ErrorMetadata,
  FormattingRulesApi,
  GetAccountsFormattingRulesResponse,
} from "clients";
import { ColourPicker } from "components";
import { asDateTime } from "utils/time";
import { LinkAccount } from "./link-account";

import { Button } from "components/ui/button";
import { Input } from "components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "components/ui/sheet";
import {
  Card,
  CardHeader,
  CardContent,
  CardDescription,
} from "components/ui/card";
import { Badge } from "components/ui/badge";
import { Skeleton } from "components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "components/ui/dropdown-menu";
import { Separator } from "components/ui/separator";
import { toast } from "react-toastify";

type FormattingRules = GetAccountsFormattingRulesResponse;

// --- Helpers (kept from original) ---

type LinkedAccountStatusType = "stable" | "unstable" | "frozen" | "unknown";

const getLinkedAccountStatus = (
  linkedAccount: LinkedAccount,
): LinkedAccountStatusType => {
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

const accountSortOrder = (account: LinkedAccount): number => {
  const status = getLinkedAccountStatus(account);
  if (status === "unstable") return 0;
  if (status === "unknown") return 1;
  if (status === "stable") return 2;
  if (status === "frozen") return 3;
  return 2;
};

const sortAccounts = (a: LinkedAccount, b: LinkedAccount): number => {
  return accountSortOrder(a) - accountSortOrder(b);
};

const SyncTimestamp: React.FC<{ linkedAccount: LinkedAccount }> = ({
  linkedAccount,
}) => {
  const status = getLinkedAccountStatus(linkedAccount);
  const lastSnapshotTime = asDateTime(linkedAccount.status?.lastSnapshotTime);

  if (status === "unstable") {
    return (
      <span className="text-xs text-muted-foreground">
        {lastSnapshotTime
          ? `Last sync attempt ${lastSnapshotTime.toRelative()}`
          : "No data yet"}
      </span>
    );
  }

  if (!lastSnapshotTime) {
    return <span className="text-xs text-muted-foreground">No data yet</span>;
  }

  return (
    <span className="text-xs text-muted-foreground">
      Synced {lastSnapshotTime.toRelative()}
    </span>
  );
};

// --- Unlink Dialog (kept from original) ---

interface UnlinkAccountDialogProps {
  show: boolean;
  linkedAccount: LinkedAccount | null;
  handleUnlink(): void;
  handleClose(): void;
}

const UnlinkAccountDialog: React.FC<UnlinkAccountDialogProps> = ({
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

// --- Error Details Dialog ---

interface ErrorDetailsDialogProps {
  show: boolean;
  linkedAccount: LinkedAccount | null;
  onClose: () => void;
}

const ErrorDetailsDialog: React.FC<ErrorDetailsDialogProps> = ({
  show,
  linkedAccount,
  onClose,
}) => {
  const lastError = linkedAccount
    ? getLinkedAccountLastError(linkedAccount)
    : null;
  return (
    <Dialog open={show} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Issue with {linkedAccount?.accountName ?? "account"}
          </DialogTitle>
          <DialogDescription>
            There is a problem with this linked account.
          </DialogDescription>
        </DialogHeader>
        {lastError && (
          <div className="space-y-3 text-sm">
            <div>
              <p className="font-medium text-destructive">
                {lastError.userMessage}
              </p>
              {lastError.errorCode && (
                <p className="text-muted-foreground mt-1">
                  Error code: {lastError.errorCode}
                </p>
              )}
            </div>
            {lastError.debugMessage && (
              <div className="rounded-md bg-muted p-3">
                <p className="text-xs text-muted-foreground font-mono">
                  {lastError.debugMessage}
                </p>
              </div>
            )}
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} size="sm">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// --- Account Status Badge ---

interface AccountStatusBadgeProps {
  linkedAccount: LinkedAccount;
  onErrorClick?: () => void;
}

const AccountStatusBadge: React.FC<AccountStatusBadgeProps> = ({
  linkedAccount,
  onErrorClick,
}) => {
  const status = getLinkedAccountStatus(linkedAccount);

  if (status === "stable") {
    return (
      <Badge variant="success">
        <CheckCircle className="mr-1 h-3 w-3" />
        Stable
      </Badge>
    );
  }

  if (status === "frozen") {
    return (
      <Badge variant="secondary">
        <Ghost className="mr-1 h-3 w-3" />
        Frozen
      </Badge>
    );
  }

  if (status === "unstable") {
    return (
      <Badge
        variant="destructive"
        className="cursor-pointer"
        onClick={onErrorClick}
      >
        <AlertCircle className="mr-1 h-3 w-3" />
        Error — View details
      </Badge>
    );
  }

  return (
    <Badge variant="outline">
      <HelpCircle className="mr-1 h-3 w-3" />
      Pending
    </Badge>
  );
};

// --- Inline Editable Name ---

interface InlineEditableNameProps {
  value: string;
  onSave: (newName: string) => Promise<void>;
  disabled?: boolean;
}

const InlineEditableName: React.FC<InlineEditableNameProps> = ({
  value,
  onSave,
  disabled,
}) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!draft.trim() || draft === value) {
      setEditing(false);
      return;
    }
    setSaving(true);
    await onSave(draft.trim());
    setSaving(false);
    setEditing(false);
  };

  const cancel = () => {
    setDraft(value);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex items-center gap-1">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") save();
            if (e.key === "Escape") cancel();
          }}
          autoFocus
          className="h-7 text-sm w-40"
        />
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={save}
          disabled={saving}
        >
          <Check className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={cancel}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <button
      className="group flex items-center gap-1 text-sm font-semibold text-left disabled:cursor-default"
      onClick={() => {
        if (!disabled) {
          setDraft(value);
          setEditing(true);
        }
      }}
      disabled={disabled}
    >
      {value}
      {!disabled && (
        <Pencil className="h-3 w-3 opacity-0 group-hover:opacity-50 transition-opacity" />
      )}
    </button>
  );
};

// --- Linked Account Card ---

interface LinkedAccountCardProps {
  linkedAccount: LinkedAccount;
  formattingRules: FormattingRules | null;
  onEditCredentials: (account: LinkedAccount) => void;
  onRename: (account: LinkedAccount, newName: string) => Promise<void>;
  onRecolour: (account: LinkedAccount, newColour: string) => void;
  onFreeze: (account: LinkedAccount) => void;
  onUnfreeze: (account: LinkedAccount) => void;
  onUnlink: (account: LinkedAccount) => void;
  onViewError: (account: LinkedAccount) => void;
}

const LinkedAccountCard: React.FC<LinkedAccountCardProps> = ({
  linkedAccount,
  formattingRules,
  onEditCredentials,
  onRename,
  onRecolour,
  onFreeze,
  onUnfreeze,
  onUnlink,
  onViewError,
}) => {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <ColourPicker
              colour={linkedAccount.accountColour}
              presetsColours={formattingRules?.colourPalette}
              onChange={(newColour) => onRecolour(linkedAccount, newColour)}
            />
            <div>
              <InlineEditableName
                value={linkedAccount.accountName}
                onSave={(newName) => onRename(linkedAccount, newName)}
                disabled={linkedAccount.frozen}
              />
              <CardDescription>
                {linkedAccount.provider.description}
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                disabled={linkedAccount.frozen}
                onClick={() => onEditCredentials(linkedAccount)}
              >
                Edit credentials
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {linkedAccount.frozen ? (
                <DropdownMenuItem onClick={() => onUnfreeze(linkedAccount)}>
                  Unfreeze
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => onFreeze(linkedAccount)}>
                  Freeze
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => onUnlink(linkedAccount)}
              >
                Unlink
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <AccountStatusBadge
            linkedAccount={linkedAccount}
            onErrorClick={() => onViewError(linkedAccount)}
          />
          <SyncTimestamp linkedAccount={linkedAccount} />
        </div>
      </CardContent>
    </Card>
  );
};

// --- Link Account Sheet ---

const LinkAccountSheetContent: React.FC<{
  linkedAccountId: number;
  onSuccess: () => void;
}> = ({ linkedAccountId, onSuccess }) => {
  const { userAccountId } = useContext(AuthContext);
  const linkedAccountsApi = useApi(LinkedAccountsApi);
  const [linkedAccount, setLinkedAccount] = useState<LinkedAccount | null>(
    null,
  );

  useEffect(() => {
    const fetch = async () => {
      const result = await linkedAccountsApi.getLinkedAccount({
        userAccountId: userAccountId!,
        linkedAccountId,
      });
      setLinkedAccount(result.linkedAccount);
    };
    fetch();
  }, [linkedAccountsApi, userAccountId, linkedAccountId]);

  if (!linkedAccount) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return <LinkAccount linkedAccount={linkedAccount} onSuccess={onSuccess} />;
};

interface LinkAccountSheetProps {
  open: boolean;
  linkedAccount: LinkedAccount | null;
  onClose: () => void;
  onSuccess: () => void;
}

const LinkAccountSheet: React.FC<LinkAccountSheetProps> = ({
  open,
  linkedAccount,
  onClose,
  onSuccess,
}) => {
  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent side="right" className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {linkedAccount ? "Edit credentials" : "Link new account"}
          </SheetTitle>
          <SheetDescription>
            {linkedAccount
              ? `Update credentials for ${linkedAccount.accountName}`
              : "Connect a new financial data provider"}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6">
          {linkedAccount ? (
            <LinkAccountSheetContent
              key={linkedAccount.id}
              linkedAccountId={linkedAccount.id}
              onSuccess={onSuccess}
            />
          ) : (
            <LinkAccount onSuccess={onSuccess} />
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};

// --- Empty State ---

const EmptyAccountsState: React.FC<{ onLinkAccount: () => void }> = ({
  onLinkAccount,
}) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <Link2 className="h-12 w-12 text-muted-foreground/50 mb-4" />
    <h3 className="text-lg font-semibold">No linked accounts</h3>
    <p className="text-sm text-muted-foreground mt-1 mb-6 max-w-sm">
      Link a financial account to start tracking your portfolio. We support
      banks, brokerages, and more.
    </p>
    <Button onClick={onLinkAccount}>Link your first account</Button>
  </div>
);

// --- Accounts Panel ---

const AccountsPanel: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const linkedAccountsApi = useApi(LinkedAccountsApi);
  const formattingRulesApi = useApi(FormattingRulesApi);

  const [accounts, setAccounts] = useState<Array<LinkedAccount>>([]);
  const [formattingRules, setFormattingRules] =
    useState<FormattingRules | null>(null);
  const [sheetState, setSheetState] = useState<{
    open: boolean;
    linkedAccount: LinkedAccount | null;
  }>({ open: false, linkedAccount: null });
  const [dialog, setDialog] = useState<UnlinkAccountDialogProps>({
    show: false,
    linkedAccount: null,
    handleUnlink: () => {},
    handleClose: () => {},
  });
  const [errorDialog, setErrorDialog] = useState<{
    show: boolean;
    linkedAccount: LinkedAccount | null;
  }>({ show: false, linkedAccount: null });

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

  useEffect(() => {
    const fetch = async () => {
      setFormattingRules(await formattingRulesApi.getAccountsFormattingRules());
    };
    fetch();
  }, [formattingRulesApi]);

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

  const handleRename = async (
    account: LinkedAccount,
    newName: string,
  ) => {
    try {
      await linkedAccountsApi.updateLinkedAccountMetadata({
        userAccountId: userAccountId!,
        linkedAccountId: account.id,
        updateLinkedAccountMetadataRequest: { accountName: newName },
      });
      toast.success("Account renamed");
      await refreshAccounts();
    } catch (e) {
      toast.error(`Failed to rename account: ${e}`);
    }
  };

  const handleRecolour = async (
    account: LinkedAccount,
    newColour: string,
  ) => {
    try {
      await linkedAccountsApi.updateLinkedAccountMetadata({
        userAccountId: userAccountId!,
        linkedAccountId: account.id,
        updateLinkedAccountMetadataRequest: { accountColour: newColour },
      });
      await refreshAccounts();
    } catch (e) {
      toast.error(`Failed to update colour: ${e}`);
    }
  };

  const handleFreeze = async (account: LinkedAccount) => {
    try {
      await linkedAccountsApi.updateLinkedAccountMetadata({
        userAccountId: userAccountId!,
        linkedAccountId: account.id,
        updateLinkedAccountMetadataRequest: { frozen: true },
      });
      toast.success(`Account '${account.accountName}' frozen`);
      await refreshAccounts();
    } catch (e) {
      toast.error(`Failed to freeze account: ${e}`);
    }
  };

  const handleUnfreeze = async (account: LinkedAccount) => {
    try {
      await linkedAccountsApi.updateLinkedAccountMetadata({
        userAccountId: userAccountId!,
        linkedAccountId: account.id,
        updateLinkedAccountMetadataRequest: { frozen: false },
      });
      toast.success(`Account '${account.accountName}' unfrozen`);
      await refreshAccounts();
    } catch (e) {
      toast.error(`Failed to unfreeze account: ${e}`);
    }
  };

  const openSheet = (linkedAccount: LinkedAccount | null) => {
    setSheetState({ open: true, linkedAccount });
  };

  const closeSheet = () => {
    setSheetState({ open: false, linkedAccount: null });
  };

  const handleSheetSuccess = async () => {
    closeSheet();
    await refreshAccounts();
  };

  const sortedAccounts = [...accounts].sort(sortAccounts);

  return (
    <>
      <UnlinkAccountDialog {...dialog} />
      <ErrorDetailsDialog
        show={errorDialog.show}
        linkedAccount={errorDialog.linkedAccount}
        onClose={() => setErrorDialog({ show: false, linkedAccount: null })}
      />
      <LinkAccountSheet
        open={sheetState.open}
        linkedAccount={sheetState.linkedAccount}
        onClose={closeSheet}
        onSuccess={handleSheetSuccess}
      />

      {accounts.length === 0 ? (
        <EmptyAccountsState onLinkAccount={() => openSheet(null)} />
      ) : (
        <>
          <div className="mb-4">
            <Button size="sm" onClick={() => openSheet(null)}>
              Link new account
            </Button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {sortedAccounts.map((account) => (
              <LinkedAccountCard
                key={account.id}
                linkedAccount={account}
                formattingRules={formattingRules}
                onEditCredentials={(a) => openSheet(a)}
                onRename={handleRename}
                onRecolour={handleRecolour}
                onFreeze={handleFreeze}
                onUnfreeze={handleUnfreeze}
                onViewError={(a) => {
                  setErrorDialog({ show: true, linkedAccount: a });
                }}
                onUnlink={(a) => {
                  setDialog({
                    show: true,
                    linkedAccount: a,
                    handleUnlink: () => {
                      hideDialog();
                      handleUnlinkAccount(a);
                    },
                    handleClose: () => {
                      hideDialog();
                    },
                  });
                }}
              />
            ))}
          </div>
        </>
      )}
    </>
  );
};

// --- Settings Page Container ---

export const LinkedAccountsSettings: React.FC = () => {
  return (
    <>
      <div className="mb-4">
        <h3 className="text-2xl font-semibold">Linked accounts</h3>
        <Separator className="mt-2" />
      </div>
      <AccountsPanel />
    </>
  );
};

export default LinkedAccountsSettings;
