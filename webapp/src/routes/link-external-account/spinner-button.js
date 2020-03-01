import React from "react";
import PropTypes from "prop-types";
import Button from "react-bootstrap/Button";

const SpinnerButton = props => {
    return (
        <Button className="bg-dark" type="button" disabled>
            <span className="spinner-border spinner-border-sm mr-3" role="status" aria-hidden="true"></span>
            {props.message}
        </Button>
    )
}

SpinnerButton.propTypes = {
    message: PropTypes.string,
};

export default SpinnerButton;