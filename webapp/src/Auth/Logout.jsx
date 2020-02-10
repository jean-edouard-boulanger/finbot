import React from 'react'
import { Redirect } from 'react-router-dom'
import { withRouter } from "react-router";


const Logout = props => {

    props._exit()

    return <Redirect to="/auth/log-in" />
}

export default withRouter(Logout)