import React from "react";
import { Outlet } from "react-router-dom";

export const Settings: React.FC<Record<string, never>> = () => {
  return (
    <div className="container mx-auto px-6 pb-48 pt-6">
      <Outlet />
    </div>
  );
};

export default Settings;
