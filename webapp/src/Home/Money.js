import React from "react";
import PropTypes from "prop-types";

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

Money.propTypes = {
    amount: PropTypes.number,
    locale: PropTypes.string,
    moneyFormatter: PropTypes.func,
    ccy: PropTypes.string,
};

export default Money;