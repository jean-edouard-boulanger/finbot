import React, { useEffect, useContext } from "react";
import { NavLink } from 'react-router-dom'

import NavBar from 'react-bootstrap/NavBar';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import ProvidersDropdown from "./providers-dropdown";
import ProvidersContext from "../../context/linked-account-context";
import AuthContext from "../../context/auth-context";

const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const authContext = useContext(AuthContext);
    const { _selectProvider, _awaitProviders, selectedProvider } = providersContext;
    const { token } = authContext;

    //component first mount
    useEffect(() => {
        console.log("providers were mounted")
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
        <NavBar collapseOnSelect expand="md" bg="dark" variant="dark">
            <NavLink className="px-5 navbar-brand" to="/">Finbot</NavLink>
            <Navbar.Toggle aria-controls="responsive-navbar-nav" />

            {token ?
                <>
                    <Navbar.Collapse id="responsive-navbar-nav">
                        <Nav activeKey={props.location.pathname} className="ml-auto">
                            <NavLink className="px-5 nav-link" to="/">Home</NavLink>
                            <NavLink className="px-5 nav-link" to="/auth/logout">Logout</NavLink>
                            <ProvidersDropdown _setProvider={_setProvider} />
                        </Nav>
                    </Navbar.Collapse>
                </>
                :
                <>
                    <Navbar.Collapse id="responsive-navbar-nav">
                        <Nav activeKey={props.location.pathname} className="ml-auto">
                            <NavLink className="px-5 nav-link" to="/auth/sign-up">Sign Up</NavLink>
                            <NavLink className="px-5 nav-link" to="/auth/logout">Log In</NavLink>
                        </Nav>
                    </Navbar.Collapse>
                </>
            }
        </NavBar>
    )
}

export { Navigation };
