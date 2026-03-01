import React, { useContext, useEffect, useState } from "react";
import { useLocation, NavLink } from "react-router-dom";
import { Menu } from "lucide-react";

import AuthContext from "contexts/auth/auth-context";
import { useInterval } from "utils/use-interval";
import { useApi, SystemReport, SystemApi } from "clients";

import { Badge } from "components/ui/badge";
import { Button } from "components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "components/ui/sheet";
import { cn } from "lib/utils";

const SystemStatusBadge: React.FC<Record<string, never>> = () => {
  const systemApi = useApi(SystemApi);
  const [backendReachable, setBackendReachable] = useState(true);
  const [report, setReport] = useState<SystemReport | null>(null);

  const updateReport = async () => {
    try {
      setReport((await systemApi.getSystemReport()).systemReport);
      setBackendReachable(true);
    } catch (e) {
      setBackendReachable(false);
      setReport(null);
    }
  };

  useEffect(() => {
    updateReport();
  }, [systemApi]);

  useInterval(async () => {
    updateReport();
  }, 10000);

  if (!backendReachable) {
    return <Badge variant="destructive">BACKEND UNREACHABLE</Badge>;
  }

  if (report?.runtime === "development") {
    return (
      <Badge variant="destructive">DEV build v{report!.finbotVersion}</Badge>
    );
  }

  if (report?.isDemo) {
    return <Badge>DEMO</Badge>;
  }

  return <></>;
};

function NavItem({
  to,
  children,
}: {
  to: string;
  children: React.ReactNode;
}) {
  const { pathname } = useLocation();
  const isActive = pathname.startsWith(to);
  return (
    <NavLink
      to={to}
      className={cn(
        "px-4 py-2 text-sm font-medium transition-colors hover:text-white",
        isActive ? "text-white" : "text-gray-300",
      )}
    >
      {children}
    </NavLink>
  );
}

const UserNavbar: React.FC = () => {
  return (
    <nav className="hidden items-center gap-1 md:flex">
      <NavItem to="/dashboard">Dashboard</NavItem>
      <NavItem to="/settings">Settings</NavItem>
      <NavItem to="/logout">Logout</NavItem>
    </nav>
  );
};

const GuestNavbar: React.FC = () => {
  return (
    <nav className="hidden items-center gap-1 md:flex">
      <NavItem to="/login">Sign in</NavItem>
      <NavItem to="/signup">Sign up</NavItem>
    </nav>
  );
};

function MobileNav({ isAuthenticated }: { isAuthenticated: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden text-white">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64">
        <SheetTitle>Navigation</SheetTitle>
        <nav className="mt-6 flex flex-col gap-2">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/settings"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              >
                Settings
              </NavLink>
              <NavLink
                to="/logout"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              >
                Logout
              </NavLink>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              >
                Sign in
              </NavLink>
              <NavLink
                to="/signup"
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              >
                Sign up
              </NavLink>
            </>
          )}
        </nav>
      </SheetContent>
    </Sheet>
  );
}

export const Navigation: React.FC = () => {
  const { userAccountId } = useContext(AuthContext);
  const isAuthenticated = userAccountId !== null;

  return (
    <header className="sticky top-0 z-40 border-b bg-gray-900 shadow-sm">
      <div className="container mx-auto flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <MobileNav isAuthenticated={isAuthenticated} />
          <NavLink
            to={isAuthenticated ? "/dashboard" : "/login"}
            className="text-lg font-semibold text-white"
          >
            Finbot{" "}
            <SystemStatusBadge />
          </NavLink>
        </div>
        {isAuthenticated ? <UserNavbar /> : <GuestNavbar />}
      </div>
    </header>
  );
};

export default Navigation;
