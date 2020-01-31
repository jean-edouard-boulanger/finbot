import React from "react";

const ValuationChange = props => {
    const {
        amount,
        currentValue,
        previousValue,

        showZero = false,
    } = props;

    const fmt = (val) => { return val.toLocaleString('en-GB'); };

    function hasValue(val) {
        return val !== undefined && val !== null;
    }

    function impl(val) {
        if (!hasValue(val) || (val === 0.0 && !showZero)) {
            return (<span className="text-muted">-</span>);
        }
        else if (val === 0.0) {
            return (<span className="text-muted">{fmt(0)}</span>);
        }
        else if (val < 0) {
            return (<span className="text-danger">{fmt(val)}</span>)
        }
        else {
            return (<span className="text-success">+{fmt(val)}</span>)
        }
    }

    // absolute change provided
    if (hasValue(amount)) {
        return impl(amount);
    }
    // current and previous values were provided, will compute difference
    else if (hasValue(currentValue) && hasValue(previousValue)) {
        return impl(currentValue - previousValue);
    }
    // invalid combination
    else {
        return impl(null);
    }
}

export default ValuationChange;