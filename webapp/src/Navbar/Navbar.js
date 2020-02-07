import React from "react";
import Navbar from 'react-bootstrap/Navbar';
import NavBar from 'react-bootstrap/NavBar';
import Nav from 'react-bootstrap/Nav';
import ProvidersDropdown from "./Providers";
import { withRouter } from "react-router";

const Navigation = props => {
    // console.log("in navigation", props.user)

    return (
        <NavBar bg="dark" variant="dark">
            <Navbar.Brand href="#home">Finbot</Navbar.Brand>

            {props.user ?
                <Nav activeKey={props.location.pathname} className="mr-auto">
                    <Nav.Link href="/">Home</Nav.Link>
                    <Nav.Link href="/auth/logout">Logout</Nav.Link>
                    <ProvidersDropdown options={props.providers} />
                </Nav>
                :
                <>
                    <Nav activeKey={props.location.pathname} className="mr-auto">
                        <Nav.Link href="/auth/sign-up">Sign Up</Nav.Link>
                        <Nav.Link href="/auth/log-in">Log In</Nav.Link>
                    </Nav>
                </>
            }
        </NavBar>
    )
}

export default withRouter(Navigation);