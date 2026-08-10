import React, { useContext, useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Settings,
  LogOut,
  Menu,
  User,
  Shield,
  Link2,
  Palette,
  Server,
  Mail,
  Plus,
} from "lucide-react";

import AuthContext from "contexts/auth/auth-context";
import {
  useApi,
  LinkedAccountsValuationApi,
  LinkedAccountValuationEntry,
  PortfoliosApi,
  PortfolioSummary,
} from "clients";
import { SystemStatusBadge } from "components/navigation";

import { Button } from "components/ui/button";
import { Separator } from "components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "components/ui/sheet";
import { ChatDrawer, ChatLauncherButton } from "components/chat-drawer";
import { FinbotMark } from "components/finbot-mark";
import { cn } from "lib/utils";

const FINBOT_PORTFOLIO_PROVIDER_ID = "finbot_portfolio";

function SidebarNavItem({
  to,
  icon: Icon,
  children,
  onClick,
}: {
  to: string;
  icon?: React.FC<{ className?: string }>;
  children: React.ReactNode;
  onClick?: () => void;
}) {
  const { pathname } = useLocation();
  const isActive =
    to === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(to);

  return (
    <NavLink to={to} onClick={onClick}>
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start gap-2",
          isActive && "bg-accent text-accent-foreground",
        )}
      >
        {Icon && <Icon className="h-4 w-4" />}
        {children}
      </Button>
    </NavLink>
  );
}

function AccountNavItem({
  to,
  colour,
  name,
  onClick,
}: {
  to: string;
  colour: string;
  name: string;
  onClick?: () => void;
}) {
  const { pathname } = useLocation();
  const isActive = pathname.startsWith(to);

  return (
    <NavLink to={to} onClick={onClick}>
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start gap-2 pl-4",
          isActive && "bg-accent text-accent-foreground",
        )}
      >
        <span
          className="h-2.5 w-2.5 shrink-0 rounded-sm"
          style={{ backgroundColor: colour }}
        />
        <span className="truncate">{name}</span>
      </Button>
    </NavLink>
  );
}

function SettingsSubNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      <p className="mt-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        My settings
      </p>
      <SidebarNavItem to="/settings/profile" icon={User} onClick={onNavigate}>
        Profile
      </SidebarNavItem>
      <SidebarNavItem
        to="/settings/security"
        icon={Shield}
        onClick={onNavigate}
      >
        Account security
      </SidebarNavItem>
      <SidebarNavItem to="/settings/linked" icon={Link2} onClick={onNavigate}>
        Linked accounts
      </SidebarNavItem>
      <SidebarNavItem
        to="/settings/appearance"
        icon={Palette}
        onClick={onNavigate}
      >
        Appearance
      </SidebarNavItem>
      <p className="mt-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Administration
      </p>
      <SidebarNavItem
        to="/settings/admin/providers"
        icon={Server}
        onClick={onNavigate}
      >
        Providers
      </SidebarNavItem>
      <SidebarNavItem
        to="/settings/admin/email_delivery"
        icon={Mail}
        onClick={onNavigate}
      >
        Email delivery
      </SidebarNavItem>
    </>
  );
}

function SidebarContent({
  accounts,
  accountsError,
  portfolios,
  onNavigate,
}: {
  accounts: LinkedAccountValuationEntry[];
  accountsError?: string | null;
  portfolios: PortfolioSummary[];
  onNavigate?: () => void;
}) {
  const { pathname } = useLocation();
  const isOnSettings = pathname.startsWith("/settings");

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-4">
        <NavLink
          to="/dashboard"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground"
          onClick={onNavigate}
        >
          <FinbotMark className="h-6 w-6 text-primary" />
          Finbot
        </NavLink>
        <SystemStatusBadge />
      </div>
      <Separator />

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-2 py-3">
        <SidebarNavItem
          to="/dashboard"
          icon={LayoutDashboard}
          onClick={onNavigate}
        >
          Dashboard
        </SidebarNavItem>

        {isOnSettings ? (
          <SettingsSubNav onNavigate={onNavigate} />
        ) : (
          <>
            <p className="mt-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Accounts
            </p>
            {accountsError ? (
              <p className="px-3 py-1 text-xs text-destructive">
                Failed to load accounts
              </p>
            ) : (
              accounts
                .filter(
                  (entry) =>
                    !entry.linkedAccount.frozen &&
                    // Portfolios are accounts too, but they have their own section below.
                    entry.linkedAccount.providerId !==
                      FINBOT_PORTFOLIO_PROVIDER_ID,
                )
                .map((entry) => (
                  <AccountNavItem
                    key={entry.linkedAccount.id}
                    to={`/dashboard/accounts/${entry.linkedAccount.id}`}
                    colour={entry.linkedAccount.accountColour}
                    name={entry.linkedAccount.description}
                    onClick={onNavigate}
                  />
                ))
            )}
            <NavLink to="/settings/linked?action=link" onClick={onNavigate}>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 pl-4 text-muted-foreground"
              >
                <Plus className="h-3.5 w-3.5" />
                <span className="text-sm">Link account</span>
              </Button>
            </NavLink>

            <p className="mt-4 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Portfolios
            </p>
            {portfolios
              .filter((portfolio) => !portfolio.frozen)
              .map((portfolio) => (
                <AccountNavItem
                  key={portfolio.id}
                  to={`/portfolios/${portfolio.id}`}
                  colour={portfolio.colour}
                  name={portfolio.name}
                  onClick={onNavigate}
                />
              ))}
            <NavLink to="/portfolios?action=new" onClick={onNavigate}>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 pl-4 text-muted-foreground"
              >
                <Plus className="h-3.5 w-3.5" />
                <span className="text-sm">Create portfolio</span>
              </Button>
            </NavLink>
          </>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        <Separator className="my-2" />
        <SidebarNavItem to="/settings" icon={Settings} onClick={onNavigate}>
          Settings
        </SidebarNavItem>
        <SidebarNavItem to="/logout" icon={LogOut} onClick={onNavigate}>
          Logout
        </SidebarNavItem>
      </nav>
    </div>
  );
}

export const AppShell: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const { userAccountId } = useContext(AuthContext);
  const linkedAccountsValuationApi = useApi(LinkedAccountsValuationApi);
  const portfoliosApi = useApi(PortfoliosApi);
  const [accounts, setAccounts] = useState<LinkedAccountValuationEntry[]>([]);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const result =
          await linkedAccountsValuationApi.getLinkedAccountsValuation({
            userAccountId: userAccountId!,
          });
        setAccounts(result.valuation.entries);
      } catch (e) {
        setAccountsError(`${e}`);
      }
    };
    fetch();
  }, [linkedAccountsValuationApi, userAccountId]);

  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        const result = await portfoliosApi.getPortfolios({
          userAccountId: userAccountId!,
        });
        setPortfolios(result.portfolios);
      } catch {
        setPortfolios([]);
      }
    };
    fetchPortfolios();
    // Portfolios are created, renamed and deleted from within the app, so the list is re-read as
    // you move around rather than only once on load.
  }, [portfoliosApi, userAccountId, pathname]);

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-border/50 bg-background md:fixed md:inset-y-0 md:flex md:flex-col">
        <SidebarContent
          accounts={accounts}
          accountsError={accountsError}
          portfolios={portfolios}
        />
      </aside>

      {/* Mobile header + sheet */}
      <div className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-3 border-b border-border/50 bg-background/80 px-4 backdrop-blur-xl md:hidden">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <SidebarContent
              accounts={accounts}
              accountsError={accountsError}
              portfolios={portfolios}
              onNavigate={() => setMobileOpen(false)}
            />
          </SheetContent>
        </Sheet>
        <NavLink
          to="/dashboard"
          className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground"
        >
          <FinbotMark className="h-6 w-6 text-primary" />
          Finbot
        </NavLink>
        <SystemStatusBadge />
      </div>

      {/* Main content */}
      {/* min-w-0: as a flex item, main defaults to min-width:auto and would otherwise be pushed
          wider than the viewport by any wide content (tables) instead of letting it scroll. */}
      <main className="min-w-0 flex-1 pt-14 md:pl-64 md:pt-0">{children}</main>

      {/* Chat assistant — global */}
      <ChatLauncherButton onClick={() => setChatOpen(true)} />
      <ChatDrawer open={chatOpen} onOpenChange={setChatOpen} />
    </div>
  );
};

export default AppShell;
