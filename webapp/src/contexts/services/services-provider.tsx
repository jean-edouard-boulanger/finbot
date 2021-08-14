import React from "react";

import { ServicesContext } from "./services-context";
import { FinbotClient } from "clients";

export const ServicesProvider = ({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element => {
  return (
    <ServicesContext.Provider
      value={{
        finbotClient: new FinbotClient(),
      }}
    >
      {children}
    </ServicesContext.Provider>
  );
};

export default ServicesProvider;
