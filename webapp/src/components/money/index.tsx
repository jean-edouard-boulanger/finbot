import React from "react";


export interface MoneyProps {
  amount: number
  locale: string
  ccy: string
  moneyFormatter(amount: number, locale: string, ccy: string): string
}


export const Money: React.FC<MoneyProps> = (props) => {
  const { amount, locale, ccy, moneyFormatter } = props;

  if (amount >= 0) {
    return <span>{moneyFormatter(amount, locale, ccy)}</span>;
  } else {
    return (
      <span className="badge badge-danger">
        {moneyFormatter(amount, locale, ccy)}
      </span>
    );
  }
};

export default Money;
