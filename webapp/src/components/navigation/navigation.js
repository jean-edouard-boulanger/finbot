import React, { useEffect, useContext } from "react";
import { NavLink } from 'react-router-dom'
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/NavBar';

import ProvidersDropdown from "./providers-dropdown";
import ProvidersContext from "context/linked-account-context";


const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const { _selectProvider, _awaitProviders, selectedProvider } = providersContext;

    //component first mount
    useEffect(() => {
        _awaitProviders();
    }, [])

    //when another provider is updated, redirect to linked-account page
    useEffect(() => {
        if (selectedProvider) props.history.push("/external-accounts/link")
    }, [selectedProvider])

    function _setProvider(val) {
        _selectProvider(val);
    }

    return (
        <Navbar bg="dark" variant="dark">
            <NavLink className="navbar-brand" to="/">Finbot</NavLink>

            {props.user ?
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <ProvidersDropdown _setProvider={_setProvider} />
                        <NavLink className="nav-link" to="/auth/logout">Logout</NavLink>
                    </Nav>
                </>
                :
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <NavLink className="nav-link" to="/auth/sign-up">Sign Up</NavLink>
                        <NavLink className="nav-link" to="/auth/log-in">Log In</NavLink>
                    </Nav>
                </>
            }
        </Navbar>
    )
}

export { Navigation };
