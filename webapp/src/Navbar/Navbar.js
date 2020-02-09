import React, { useEffect, useContext } from "react";
import { withRouter } from "react-router";
<<<<<<< HEAD
import { NavLink } from 'react-router-dom'

=======

import Navbar from 'react-bootstrap/Navbar';
>>>>>>> master
import NavBar from 'react-bootstrap/NavBar';
import Nav from 'react-bootstrap/Nav';
import ProvidersDropdown from "./Providers";
import ProvidersContext from "../context/LinkedAccountContext";
<<<<<<< HEAD
import AuthContext from "../context/authContext";

const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const authContext = useContext(AuthContext);
    const { _selectProvider, _awaitProviders, selectedProvider } = providersContext;
    const { token } = authContext;
=======


const Navigation = props => {
    const providersContext = useContext(ProvidersContext)
    const { providersList, _selectProvider, _awaitProviders, selectedProvider } = providersContext;
>>>>>>> master

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
<<<<<<< HEAD
            {/* <Navbar.Brand href="#home">Finbot</Navbar.Brand> */}
            <NavLink className="px-5 navbar-brand" to="/">Finbot</NavLink>

            {token ?
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <NavLink className="px-5 nav-link" to="/">Home</NavLink>
                        <NavLink className="px-5 nav-link" to="/auth/logout">Logout</NavLink>
                        <ProvidersDropdown _setProvider={_setProvider} />
=======
            <Navbar.Brand href="#home">Finbot</Navbar.Brand>

            {props.user ?
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
                        <Nav.Link className="px-5" href="/">Home</Nav.Link>
                        <Nav.Link className="px-5" href="/auth/logout">Logout</Nav.Link>
                        <ProvidersDropdown _setProvider={_setProvider} />
                        {/* <ProvidersDropdown options={props.providers} selectOption={selectProvider} /> */}
>>>>>>> master
                    </Nav>
                </>
                :
                <>
                    <Nav activeKey={props.location.pathname} className="ml-auto">
<<<<<<< HEAD
                        <NavLink className="px-5 nav-link" to="/auth/sign-up">Sign Up</NavLink>
                        <NavLink className="px-5 nav-link" to="/auth/logout">Log In</NavLink>
=======
                        <Nav.Link href="/auth/sign-up">Sign Up</Nav.Link>
                        <Nav.Link href="/auth/log-in">Log In</Nav.Link>
>>>>>>> master
                    </Nav>
                </>
            }
        </NavBar>
    )
}

export default withRouter(Navigation);