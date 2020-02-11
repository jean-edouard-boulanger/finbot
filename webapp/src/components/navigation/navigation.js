import React, { useEffect, useContext } from "react";
import { withRouter } from "react-router";
import { NavLink } from 'react-router-dom'

import NavBar from 'react-bootstrap/NavBar';
import Nav from 'react-bootstrap/Nav';
import ProvidersDropdown from "./providers-dropdown";
import ProvidersContext from "../../context/linked-account-context";
import AuthContext from "../../context/authContext";

const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const authContext = useContext(AuthContext);
    const { _selectProvider, _awaitProviders, selectedProvider } = providersContext;
    const { token } = authContext;

    //component first mount
    useEffect(() => {
        _awaitProviders();
    }, [])

    //when another provider is updated, redirect to linked-account page
    useEffect(() => {
        if (selectedProvider) props.history.push("/linked-account/create")
        // if (selectedProvider) props.history.push("/external-accounts/link")
    }, [selectedProvider])

    function _setProvider(val) {
        _selectProvider(val);
    }

    return (
        <NavBar bg="dark" variant="dark">
            <NavLink className="px-5 navbar-brand" to="/">Finbot</NavLink>

            {token ?
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <NavLink className="px-5 nav-link" to="/">Home</NavLink>
                        <NavLink className="px-5 nav-link" to="/auth/logout">Logout</NavLink>
                        <ProvidersDropdown _setProvider={_setProvider} />
                    </Nav>
                </>
                :
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <NavLink className="px-5 nav-link" to="/auth/sign-up">Sign Up</NavLink>
                        <NavLink className="px-5 nav-link" to="/auth/logout">Log In</NavLink>
                    </Nav>
                </>
            }
        </NavBar>
    )
}

export { Navigation };
