import React, { useEffect, useContext } from "react";
import { withRouter } from "react-router";

import Navbar from 'react-bootstrap/Navbar';
import NavBar from 'react-bootstrap/NavBar';
import Nav from 'react-bootstrap/Nav';
import ProvidersDropdown from "./Providers";
import ProvidersContext from "../context/LinkedAccountContext";


const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const { providersList, _selectProvider, _awaitProviders, selectedProvider } = providersContext;

    //component first mount
    useEffect(() => {
        _awaitProviders();
    }, [])

    //when another provider is updated, redirect to linked-account page
    useEffect(() => {
        if (selectedProvider) props.history.push("/linked-account")
    }, [selectedProvider])

    function _setProvider(val) {
        _selectProvider(val);
    }

    return (
        <NavBar bg="dark" variant="dark">
            <Navbar.Brand href="#home">Finbot</Navbar.Brand>

            {props.user ?
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <Nav.Link className="px-5" href="/">Home</Nav.Link>
                        <Nav.Link className="px-5" href="/auth/logout">Logout</Nav.Link>
                        <ProvidersDropdown _setProvider={_setProvider} />
                        {/* <ProvidersDropdown options={props.providers} selectOption={selectProvider} /> */}
                    </Nav>
                </>
                :
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <Nav.Link href="/auth/sign-up">Sign Up</Nav.Link>
                        <Nav.Link href="/auth/log-in">Log In</Nav.Link>
                    </Nav>
                </>
            }
        </NavBar>
    )
}

export default withRouter(Navigation);