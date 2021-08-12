import { createContext } from "react";
import { FinbotClient } from "clients";

type ServicesContextProps = {
  finbotClient: FinbotClient;
};

export const ServicesContext = createContext<Partial<ServicesContextProps>>({});

export default ServicesContext;
