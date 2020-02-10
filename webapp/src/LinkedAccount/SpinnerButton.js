import React from "react";

const SpinnerButton = props => {

    return (
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}>
            <button className="btn text-center d-flex justify-content-center" type="button">
                <span className="spinner-border spinner-border-sm mr-3" role="status" aria-hidden="true"></span>
                {props.message}
            </button>
        </div>
    )
}

export default SpinnerButton;