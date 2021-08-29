import * as emailAddresses from "email-addresses";

export const isEmailValid = (email: string): boolean => {
  const result = emailAddresses.parseOneAddress(email);
  return result !== null;
};
