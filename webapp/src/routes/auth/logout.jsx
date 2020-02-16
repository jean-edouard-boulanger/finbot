import React from 'react'
import PropTypes from "prop-types";
import { Redirect } from 'react-router-dom'
import { withRouter } from "react-router";


const Logout = props => {

    props._exit()

    return <Redirect to="/auth/log-in" />
}

Logout.propTypes = {
    _exit: PropTypes.func,
};

export default withRouter(Logout)