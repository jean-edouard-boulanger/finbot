import React from "react";

export type MoneyFormatterType = (
  amount: number,
  locale: string,
  ccy: string,
) => string;

export interface MoneyProps {
  amount: number;
  locale: string;
  ccy: string;
  moneyFormatter: MoneyFormatterType;
}

export const defaultMoneyFormatter: MoneyFormatterType = (
  amount,
  locale,
  currency,
) => {
  const localized = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
  }).format(Math.abs(amount));
  return amount >= 0 ? localized : `(${localized})`;
};

export const Money: React.FC<MoneyProps> = (props) => {
  const { amount, locale, ccy, moneyFormatter } = props;

  if (amount >= 0) {
    return <span>{moneyFormatter(amount, locale, ccy)}</span>;
  } else {
    return (
      <span className="text-danger">{moneyFormatter(amount, locale, ccy)}</span>
    );
  }
};

export default Money;
