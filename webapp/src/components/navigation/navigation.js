import React, { useEffect, useContext } from "react";
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/NavBar';

import ProvidersDropdown from "./providers-dropdown";
import ProvidersContext from "context/LinkedAccountContext";


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
        </Navbar>
    )
}

export { Navigation };
