import React from "react";

export interface ValuationChangeProps {
  amount?: number | null;
  currentValue?: number | null;
  previousValue?: number | null;
  locale?: string;
  showZero?: boolean;
}

export const ValuationChange: React.FC<ValuationChangeProps> = (props) => {
  const {
    amount,
    currentValue,
    previousValue,

    locale = "en-GB",
    showZero = false,
  } = props;

  const fmt = (val: number): string => {
    return val.toLocaleString(locale);
  };

  function impl(val?: number | null) {
    if (val === null || val === undefined || (val === 0.0 && !showZero)) {
      return <span className="text-muted-foreground">-</span>;
    } else if (val === 0.0) {
      return <span className="text-muted-foreground">{fmt(0)}</span>;
    } else if (val < 0) {
      return <span className="text-red-500">{fmt(val)}</span>;
    } else {
      return <span className="text-green-500">+{fmt(val)}</span>;
    }
  }

  // absolute change provided
  if (amount !== null && amount !== undefined) {
    return impl(amount);
  }
  // current and previous values were provided, will compute difference
  else if (
    currentValue !== null &&
    currentValue !== undefined &&
    previousValue !== null &&
    previousValue !== undefined
  ) {
    return impl(currentValue - previousValue);
  }
  // invalid combination
  else {
    return impl(null);
  }
};

export interface RelativeValuationChangeProps {
  amount?: number;
}

export const RelativeValuationChange: React.FC<RelativeValuationChangeProps> = (
  props,
) => {
  const { amount } = props;
  if (!amount || amount === 0.0) {
    return <span className="text-muted-foreground">-</span>;
  }
  if (amount < 0) {
    return <span className="text-red-500">{(amount * 100).toFixed(2)}%</span>;
  } else {
    return (
      <span className="text-green-500">+{(amount * 100).toFixed(2)}%</span>
    );
  }
};
