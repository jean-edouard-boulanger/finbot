import React from "react";

const Money = props => {
    const {
        amount,
        locale,
        ccy,
        moneyFormatter
    } = props;
    if (amount >= 0) {
        return (<span >{moneyFormatter(amount, locale, ccy)}</span>);
    }
    else {
        return (<span span className="badge badge-danger">{moneyFormatter(amount, locale, ccy)}</span>);
    }
}

export default Money;