import React from 'react';

import { ServicesContext } from './services-context';
import { FinbotClient } from "clients";


export const ServicesProvider = (props) => {
  return (
    <ServicesContext.Provider
      value={{
        finbotClient: new FinbotClient()
      }} >
      {props.children}
    </ServicesContext.Provider>
  );
}

export default ServicesProvider;