import React from "react";
import { useLocation, useNavigate, Outlet } from "react-router-dom";

import { Button } from "components/ui/button";
import { Separator } from "components/ui/separator";
import { cn } from "lib/utils";

interface NavItemProps {
  path: string;
  label: string;
  currentPath: string;
  onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({
  path,
  label,
  currentPath,
  onClick,
}) => {
  const isActive = currentPath.startsWith(path);
  return (
    <Button
      variant="ghost"
      className={cn(
        "w-full justify-start",
        isActive && "bg-accent text-accent-foreground",
      )}
      onClick={onClick}
    >
      {label}
    </Button>
  );
};

export const NavigationPanel: React.FC = () => {
  const { pathname } = useLocation();
  const push = useNavigate();
  return (
    <nav className="flex flex-col gap-1">
      <p className="px-3 py-2 text-sm font-semibold text-muted-foreground">
        My settings
      </p>
      <NavItem
        path="/settings/profile"
        label="Profile"
        currentPath={pathname}
        onClick={() => push("/settings/profile")}
      />
      <NavItem
        path="/settings/security"
        label="Account security"
        currentPath={pathname}
        onClick={() => push("/settings/security")}
      />
      <NavItem
        path="/settings/linked"
        label="Linked accounts"
        currentPath={pathname}
        onClick={() => push("/settings/linked")}
      />
      <Separator className="my-2" />
      <p className="px-3 py-2 text-sm font-semibold text-muted-foreground">
        Administration
      </p>
      <NavItem
        path="/settings/admin/providers"
        label="Providers"
        currentPath={pathname}
        onClick={() => push("/settings/admin/providers")}
      />
      <NavItem
        path="/settings/admin/email_delivery"
        label="Email delivery"
        currentPath={pathname}
        onClick={() => push("/settings/admin/email_delivery")}
      />
    </nav>
  );
};

export const Settings: React.FC<Record<string, never>> = () => {
  return (
    <div className="flex gap-6">
      <div className="w-56 shrink-0">
        <NavigationPanel />
      </div>
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
};

export default Settings;
